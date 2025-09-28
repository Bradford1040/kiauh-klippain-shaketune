# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: belts_graph_creator.py
# Description: Belts graph creator implementation

from typing import Optional

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

    def configure(
        self,
        kinematics: Optional[str] = None,
        test_params: Optional[testParams] = None,
        max_scale: Optional[int] = None,
    ) -> None:
        """Configure the belts comparison parameters"""
        self._kinematics = kinematics
        self._test_params = test_params
        self._max_scale = max_scale

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
