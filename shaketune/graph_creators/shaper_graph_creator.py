# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2023-2026  Shake&Tune contributors Bradford Alden Adams aka (Bradford1040)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: shaper_graph_creator.py
# Description: Input shaper graph creator implementation

from typing import Any, Optional

from ..helpers.accelerometer import MeasurementsManager
from ..shaketune_config import ShakeTuneConfig
from .computations.shaper_computation import ShaperComputation
from .graph_creator import GraphCreator
from .plotters.shaper_plotter import ShaperPlotter


@GraphCreator.register('input shaper')
class ShaperGraphCreator(GraphCreator):
    """Input shaper graph creator using composition-based architecture"""

    def __init__(self, config: ShakeTuneConfig):
        super().__init__(config, ShaperComputation, ShaperPlotter)
        self._max_smoothing: Optional[float] = None
        self._scv: float = 5.0  # Default square corner velocity
        self._test_params: Optional[Any] = None
        self._max_scale: Optional[float] = None

    def configure(self, *args: Any, **kwargs: Any) -> None:
        """Configure the input shaper parameters"""
        self._scv = float(kwargs.get('scv', args[0] if len(args) > 0 else 5.0))
        self._max_smoothing = kwargs.get('max_smoothing', args[1] if len(args) > 1 else None)
        self._test_params = kwargs.get('test_params', args[2] if len(args) > 2 else None)
        self._max_scale = kwargs.get('max_scale', args[3] if len(args) > 3 else None)

    def _create_computation(self, measurements_manager: MeasurementsManager) -> ShaperComputation:
        """Create the computation instance with proper configuration"""
        return ShaperComputation(
            measurements=measurements_manager.get_measurements(),
            max_smoothing=self._max_smoothing,
            scv=self._scv,
            max_freq=self._config.max_freq,
            test_params=self._test_params,
            max_scale=self._max_scale,
            st_version=self._version,
        )
