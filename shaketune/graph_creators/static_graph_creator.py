# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: static_graph_creator.py
# Description: Static frequency graph creator implementation

from typing import Optional

from ..helpers.accelerometer import MeasurementsManager
from ..shaketune_config import ShakeTuneConfig
from .computations.static_frequency_computation import StaticFrequencyComputation
from .graph_creator import GraphCreator
from .plotters.static_frequency_plotter import StaticFrequencyPlotter


@GraphCreator.register('static frequency')
class StaticGraphCreator(GraphCreator):
    """Static frequency graph creator using composition-based architecture"""

    def __init__(self, config: ShakeTuneConfig):
        super().__init__(config, StaticFrequencyComputation, StaticFrequencyPlotter)
        self._freq: Optional[float] = None
        self._duration: Optional[float] = None
        self._accel_per_hz: Optional[float] = None

    def configure(self, freq: float = None, duration: float = None, accel_per_hz: Optional[float] = None) -> None:
        """Configure the static frequency analysis parameters"""
        self._freq = freq
        self._duration = duration
        self._accel_per_hz = accel_per_hz

    def _create_computation(self, measurements_manager: MeasurementsManager) -> StaticFrequencyComputation:
        """Create the computation instance with proper configuration"""
        return StaticFrequencyComputation(
            measurements=measurements_manager.get_measurements(),
            freq=self._freq,
            duration=self._duration,
            max_freq=self._config.max_freq,
            accel_per_hz=self._accel_per_hz,
            st_version=self._version,
        )
