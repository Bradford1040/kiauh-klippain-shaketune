# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2023-2026  Shake&Tune contributors Bradford Alden Adams aka (Bradford1040)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: accelerometer.py
# Description: Provides a custom and internal Shake&Tune Accelerometer helper that interfaces
#              with Klipper's accelerometer classes. It includes functions to start and stop
#              accelerometer measurements.
#              It also includes functions to load and save measurements from a file in a new
#              compressed format (.stdata) or from the legacy Klipper CSV files.


import json
import os
import time
import uuid
from io import TextIOWrapper
from multiprocessing import Process, Queue, Value
from pathlib import Path
from typing import Optional, TypedDict

import numpy as np
from zstandard import FLUSH_FRAME, ZstdCompressor, ZstdDecompressor

from ..helpers.console_output import ConsoleOutput

Sample = tuple[float, float, float, float]
SamplesList = list[Sample]

STOP_SENTINEL = 'STOP_SENTINEL'
WRITE_TIMEOUT = 300
WAIT_FOR_SAMPLE_TIMEOUT = 30
COMPRESSION_LEVEL = 11  # Zstandard compression level (0 to 22, higher is slower but better compression)


class Measurement(TypedDict):
    name: str
    samples: SamplesList


class MeasurementsManager:
    def __init__(self, chunk_size: int, k_reactor=None, stdata_filename: Optional[Path] = None):
        # Klipper reactor is required to save data (optional for CLI mode, which never saves .stdata)
        self._k_reactor = k_reactor
        self._chunk_size = chunk_size
        self._final_file = None
        self._temp_file = None

        # Get the stdata filename and associated temporary file (with the correct extension)
        if stdata_filename is not None:
            self._final_file = stdata_filename
            if self._final_file.suffix != '.stdata':
                self._final_file = self._final_file.with_suffix('.stdata')
            self._temp_file = self._final_file.parent / f'snt_tmp-{str(uuid.uuid4())[:8]}.stdata'

        self.measurements: list[Measurement] = []

        # Create a dedicated process with a Queue to manage all the writing operations
        self._writer_queue = Queue()
        self._is_writing = Value('b', False)
        self._writer_process: Optional[Process] = None

    # Dedicated writer process: opens the output file in binary write mode and wraps it with a Zstandard compressor
    # stream. It then continuously reads measurement objects from the queue and writes each as a JSON line
    def _writer_loop(self, output_file: Path, write_queue: Queue, is_writing):
        try:
            with open(output_file, 'wb') as f:
                cctx = ZstdCompressor(level=COMPRESSION_LEVEL)
                with cctx.stream_writer(f) as compressor:
                    while True:
                        meas = write_queue.get()
                        if meas == STOP_SENTINEL:
                            break
                        with is_writing.get_lock():
                            is_writing.value = True
                        line = (json.dumps(meas) + '\n').encode('utf-8')
                        compressor.write(line)
                        with is_writing.get_lock():
                            is_writing.value = False
                    compressor.flush(FLUSH_FRAME)
        except Exception as e:
            ConsoleOutput.print(f'Error writing to file {output_file}: {e}')

    def clear_measurements(self, keep_last: bool = False):
        self.measurements = [self.measurements[-1]] if keep_last and self.measurements else []

    def append_samples_to_current_measurement(self, additional_samples: SamplesList):
        try:
            self.measurements[-1]['samples'].extend(additional_samples)
        except IndexError as err:
            raise ValueError('no measurements available to append samples to!') from err

    def add_measurement(self, name: str, samples: Optional[SamplesList] = None, timeout: float = WRITE_TIMEOUT):
        if not self._temp_file:
            raise ValueError('no file path provided to the MeasurementsManager! Unable to add any measurement.')

        # Start the writer process if it's not already running
        if self._writer_process is None:
            self._writer_process = Process(
                target=self._writer_loop,
                args=(self._temp_file, self._writer_queue, self._is_writing),
                daemon=False,
            )
            self._writer_process.start()

        samples = samples if samples is not None else []
        self.measurements.append({'name': name, 'samples': samples})
        if len(self.measurements) > self._chunk_size:
            self._flush_chunk()  # Flush the current chunk of measurements to disk

            # Force wait for the writer process to finish writing in order to avoid being able
            # to start a new measurement while the previous one is still being written on disk
            # This is necessary to avoid Timer too close errors in Klipper...
            if self._k_reactor is None:
                return  # In case no reactor is available, we can't wait for the writer to finish
            eventtime = self._k_reactor.monotonic()
            endtime = eventtime + timeout
            while eventtime < endtime:
                with self._is_writing.get_lock():
                    if self._writer_queue.empty() and not self._is_writing.value:
                        return  # writer process is idle, so we can continue...
                eventtime = self._k_reactor.pause(eventtime + 0.05)

            # Raise an error with some statistics about the writer process
            raise TimeoutError(
                'timeout while waiting for the writer process to finish writing measurements '
                f'chunk to disk!\nWriter process is still running after {timeout} seconds and '
                f'has {self._writer_queue.qsize()} items in the queue!'
            )

    # Flush all measurements except the last one (which can still receive appended samples) to the dedicated
    # writer process. Each measurement is sent as a single JSON-serializable object via the Queue
    def _flush_chunk(self):
        if len(self.measurements) <= 1:
            return
        flush_list = self.measurements[:-1]
        for meas in flush_list:
            self._writer_queue.put(meas)
        self.clear_measurements(keep_last=True)

    def save_stdata(self, timeout: int = WRITE_TIMEOUT):
        # Klipper reactor is required to save data (optional for CLI mode, which never saves .stdata)
        if not self._k_reactor:
            raise ValueError('no Klipper reactor provided! Unable to save data to disk.')
        if not self._writer_process:
            raise ValueError('no writer process available! Unable to save data to disk.')
        if not self._final_file:
            raise ValueError('no file path provided to the MeasurementsManager! Unable to save data to disk.')

        # Flush any remaining in-memory measurements
        if len(self.measurements) > 0:
            for meas in self.measurements:
                self._writer_queue.put(meas)
            self.clear_measurements()

        # Signal the writer process to finish its task
        self._writer_queue.put(STOP_SENTINEL)

        # Wait for the writer process to finish its task
        eventtime = self._k_reactor.monotonic()
        endtime = eventtime + timeout
        complete = False
        while eventtime < endtime:
            if not self._writer_process.is_alive():
                complete = True
                break
            eventtime = self._k_reactor.pause(eventtime + 0.05)
        if not complete:
            raise TimeoutError(
                'Shake&Tune was unable to finish and close the .stdata writing process before the '
                f'timeout of {timeout} seconds. This might be due to a slow, busy or full SD card.'
            )

        try:
            if self._final_file.exists():
                self._final_file.unlink()
            self._temp_file.replace(self._final_file)  # type: ignore[union-attr]
        except Exception as e:
            ConsoleOutput.print(f'Shake&Tune was unable to create the final data file ({self._final_file}): {e}')

    # Return all the measurements from memory. Measurements flushed to disk are available via load_from_stdata()
    def get_measurements(self) -> list[Measurement]:
        return self.measurements

    # Load all the measurements from the .stdata file
    def load_from_stdata(self, filename: Path) -> list[Measurement]:
        measurements = []
        try:
            with open(filename, 'rb') as f:
                dctx = ZstdDecompressor()
                with dctx.stream_reader(f) as decompressor:
                    text_stream = TextIOWrapper(decompressor, encoding='utf-8')
                    for line in text_stream:
                        if line.strip():
                            meas = json.loads(line)
                            measurements.append(meas)
            self.measurements = measurements
        except Exception as e:
            ConsoleOutput.print(f'Warning: unable to load measurements from {filename}: {e}')
            self.measurements = []
        return self.measurements

    def load_from_csvs(self, klipper_CSVs: list[Path]) -> list[Measurement]:
        for logname in klipper_CSVs:
            try:
                if logname.suffix != '.csv':
                    ConsoleOutput.print(f'Warning: {logname} is not a CSV file. It will be ignored by Shake&Tune!')
                    continue
                with open(logname) as f:
                    header = None
                    for line in f:
                        cleaned_line = line.strip()
                        # Check for a PSD file generated by Klipper and raise a warning
                        if cleaned_line.startswith('#freq,psd_x,psd_y,psd_z,psd_xyz'):
                            ConsoleOutput.print(
                                f'Warning: {logname} does not contain raw Klipper accelerometer data. '
                                'Please use the official Klipper script to process it instead. '
                            )
                            continue
                        # Check for the expected legacy header used in Shake&Tune (raw accelerometer data from Klipper)
                        elif cleaned_line.startswith('#time,accel_x,accel_y,accel_z'):
                            header = cleaned_line
                            break
                    if not header:
                        ConsoleOutput.print(
                            f"Warning: file {logname} doesn't seem to be a Klipper raw accelerometer data file. "
                            f"Expected '#time,accel_x,accel_y,accel_z', but got '{header}'. "
                            'This file will be ignored by Shake&Tune!'
                        )
                        continue
                    # If we have the correct raw data header, proceed to load the data
                    data = np.loadtxt(logname, comments='#', delimiter=',', skiprows=1)
                    if data.ndim == 1 or data.shape[1] != 4:
                        ConsoleOutput.print(
                            f'Warning: {logname} does not have the correct data format; expected 4 columns. '
                            'It will be ignored by Shake&Tune!'
                        )
                        continue

                    # Add the parsed klipper raw accelerometer data to Shake&Tune measurements object
                    samples = [tuple(row) for row in data]
                    if os.environ.get('SHAKETUNE_IN_CLI') != '1':
                        # When running as a Klipper plugin, we can use the standard add_measurement method
                        self.add_measurement(name=logname.stem, samples=samples)
                    else:
                        # When running as a CLI, we need to manually append the samples to the measurements object
                        # as the add_measurement method requires a temp file to be set up for writing and that
                        # is not available when running like this or would need workarounds to be implemented.
                        # But it's not a big deal as the CLI mode is only used for single shot runs.
                        self.measurements.append({'name': logname.stem, 'samples': samples})
            except Exception as err:
                ConsoleOutput.print(f'Error while reading {logname}: {err}. It will be ignored by Shake&Tune!')
                continue

        return self.measurements

    def __del__(self):
        try:
            if self._temp_file is not None and self._temp_file.exists():
                self._temp_file.unlink()
        except Exception:
            pass  # Ignore errors during cleanup


class Accelerometer:
    def __init__(self, klipper_accelerometer, k_reactor):
        self._k_accelerometer = klipper_accelerometer
        self._k_reactor = k_reactor
        self._bg_client = None
        self._measurements_manager: Optional[MeasurementsManager] = None
        self._samples_ready = False
        self._sample_error = None

    @staticmethod
    def find_axis_accelerometer(printer, axis: str = 'xy'):
        accel_chip_names = printer.lookup_object('resonance_tester').accel_chip_names
        for chip_axis, chip_name in accel_chip_names:
            if axis in {'x', 'y'} and chip_axis == 'xy':
                return chip_name
            elif chip_axis == axis:
                return chip_name
        return None

    def start_recording(
        self, measurements_manager: MeasurementsManager, name: Optional[str] = None, append_time: bool = True
    ):
        if self._bg_client is None:
            self._bg_client = self._k_accelerometer.start_internal_client()

            timestamp = time.strftime('%Y%m%d_%H%M%S')
            if name is None:
                name = timestamp
            elif append_time:
                name += f'_{timestamp}'

            if not name.replace('-', '').replace('_', '').isalnum():
                raise ValueError('invalid measurement name!')

            self._measurements_manager = measurements_manager
            self._measurements_manager.add_measurement(name=name)
        else:
            raise ValueError('recording already started!')

    def stop_recording(self) -> Optional[MeasurementsManager]:
        if self._bg_client is None:
            ConsoleOutput.print('Warning: no recording to stop!')
            return None

        manager = self._measurements_manager
        if manager is None:
            ConsoleOutput.print('Warning: no measurement manager configured for active recording!')
            self._bg_client = None
            return None

        try:
            self._bg_client.finish_measurements()
            samples = getattr(self._bg_client, 'samples', None)
            if samples is None or (isinstance(samples, list) and len(samples) == 0):
                samples = self._bg_client.get_samples()
            manager.append_samples_to_current_measurement(samples)
        except Exception as e:
            ConsoleOutput.print(f'Error during accelerometer data retrieval: {e}')
        finally:
            self._bg_client = None

        return manager
