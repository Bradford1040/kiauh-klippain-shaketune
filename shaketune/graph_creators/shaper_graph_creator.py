# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
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

    def configure(
        self,
        scv: float = 5.0,
        max_smoothing: Optional[float] = None,
        test_params: Optional[Any] = None,
        max_scale: Optional[float] = None,
    ) -> None:
        """Configure the input shaper parameters"""
        self._scv = scv
        self._max_smoothing = max_smoothing
        self._test_params = test_params
        self._max_scale = max_scale

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
