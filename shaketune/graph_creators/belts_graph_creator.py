# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2023-2026  Shake&Tune contributors Bradford Alden Adams aka (Bradford1040)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: belts_graph_creator.py
# Description: Belts graph creator implementation

from typing import Any, Optional

from ..helpers.accelerometer import MeasurementsManager
from ..helpers.resonance_test import testParams
from ..shaketune_config import ShakeTuneConfig
from .computations.belts_computation import BeltsComputation
from .graph_creator import GraphCreator
from .plotters.belts_plotter import BeltsPlotter


@GraphCreator.register('belts comparison')
class BeltsGraphCreator(GraphCreator):
    """Belts graph creator using composition-based architecture"""

    def __init__(self, config: ShakeTuneConfig):
        super().__init__(config, BeltsComputation, BeltsPlotter)
        self._kinematics: Optional[str] = None
        self._test_params: Optional[testParams] = None
        self._max_scale: Optional[int] = None

    def configure(self, *args: Any, **kwargs: Any) -> None:
        """Configure the belts comparison parameters"""
        self._kinematics = kwargs.get('kinematics', args[0] if len(args) > 0 else None)
        self._test_params = kwargs.get('test_params', args[1] if len(args) > 1 else None)
        self._max_scale = kwargs.get('max_scale', args[2] if len(args) > 2 else None)

    def _create_computation(self, measurements_manager: MeasurementsManager) -> BeltsComputation:
        """Create the computation instance with proper configuration"""
        return BeltsComputation(
            measurements=measurements_manager.get_measurements(),
            kinematics=self._kinematics,
            max_freq=self._config.max_freq,
            test_params=self._test_params,
            max_scale=self._max_scale,
            st_version=self._version,
        )
