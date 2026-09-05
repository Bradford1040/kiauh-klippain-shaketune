# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2023-2026  Shake&Tune contributors Bradford Alden Adams aka (Bradford1040)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: static_graph_creator.py
# Description: Static frequency graph creator implementation

from typing import Any, Optional

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

    def configure(self, *args: Any, **kwargs: Any) -> None:
        """Configure the static frequency analysis parameters"""
        self._freq = kwargs.get('freq', args[0] if len(args) > 0 else None)
        self._duration = kwargs.get('duration', args[1] if len(args) > 1 else None)
        self._accel_per_hz = kwargs.get('accel_per_hz', args[2] if len(args) > 2 else None)

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
