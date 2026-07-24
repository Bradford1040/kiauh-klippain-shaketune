# Shake&Tune: 3D printer analysis tools
#
#
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: spectrogram.py
# Description: Contains the spectrogram computation function for accelerometer data
#              analysis, optimized for low-RAM embedded systems like Raspberry Pi.

import numpy as np


def compute_spectrogram(data):
    """Compute power spectral density spectrogram from accelerometer data.
    This implementation is optimized for low-memory systems (e.g., Raspberry Pi)
    by using a pre-allocated buffer and processing segments sequentially rather
    than using memory-intensive stride tricks.
    Args:
        data: numpy array with shape (N, 4) where columns are [time, x, y, z]
    Returns:
        Tuple of (pdata, t, f) where:
            - pdata: 2D array of power spectral density values
            - t: 1D array of time values for each segment
            - f: 1D array of frequency values
    """
    n = data.shape[0]
    if n < 2:
        raise ValueError('Not enough data samples')

    # Sampling frequency
    fs = n / (data[-1, 0] - data[0, 0])

    # Round up to a power of 2 for faster FFT
    nperseg = 1 << int(0.5 * fs - 1).bit_length()
    noverlap = nperseg // 2

    # Guard against data too short to form one full segment
    if n < nperseg:
        raise ValueError(f'Input data too short for nperseg={nperseg}')

    window = np.kaiser(nperseg, 6.0)

    # Step between segments and number of segments
    step = nperseg - noverlap
    n_segments = 1 + (n - nperseg) // step
    n_freqs = nperseg // 2 + 1

    # Time and frequency arrays
    t = np.arange(n_segments) * step / fs + nperseg / (2 * fs)
    f = np.fft.rfftfreq(nperseg, 1 / fs)

    # Output PSD accumulator
    pdata = np.zeros((n_freqs, n_segments))
    window_norm = 1.0 / (fs * (window**2).sum())

    # Process each axis (x, y, z) using a reusable buffer for memory efficiency
    segment_buffer = np.empty(nperseg)
    for axis_idx in (1, 2, 3):
        axis_data = data[:, axis_idx]

        for i in range(n_segments):
            start = i * step
            end = start + nperseg

            # Load each segment into the buffer and detrend in-place
            np.copyto(segment_buffer, axis_data[start:end])
            segment_buffer -= segment_buffer.mean()

            # Apply window function and compute the FFT
            segment_buffer *= window
            fft_result = np.fft.rfft(segment_buffer, n=nperseg)

            # Compute the power spectral density
            psd = np.abs(fft_result) ** 2
            psd *= window_norm

            # Double for one-sided spectrum (except for DC and Nyquist)
            if nperseg % 2 == 0:
                psd[1:-1] *= 2
            else:
                psd[1:] *= 2

            pdata[:, i] += psd

    return pdata, t, f
