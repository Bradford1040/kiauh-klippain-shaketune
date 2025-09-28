# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: vibrations_graph_creator.py
# Description: Machine vibrations graph creator implementation

from typing import List, Optional

from ..helpers.accelerometer import MeasurementsManager
from ..helpers.motors_config_parser import Motor
from ..shaketune_config import ShakeTuneConfig
from .computations.vibrations_computation import VibrationsComputation
from .graph_creator import GraphCreator
from .plotters.vibrations_plotter import VibrationsPlotter


@GraphCreator.register('vibrations profile')
class VibrationsGraphCreator(GraphCreator):
    """Machine vibrations graph creator using composition-based architecture"""

    def __init__(self, config: ShakeTuneConfig):
        super().__init__(config, VibrationsComputation, VibrationsPlotter)
        self._kinematics: Optional[str] = None
        self._accel: Optional[float] = None
        self._motors: Optional[List[Motor]] = None

    def configure(
        self,
        kinematics: str,
        accel: Optional[float] = None,
        motors: Optional[List[Motor]] = None,
    ) -> None:
        """Configure the vibrations analysis parameters"""
        self._kinematics = kinematics
        self._accel = accel
        self._motors = motors

    def _create_computation(self, measurements_manager: MeasurementsManager) -> VibrationsComputation:
        """Create the computation instance with proper configuration"""
        return VibrationsComputation(
            measurements=measurements_manager.get_measurements(),
            kinematics=self._kinematics,
            accel=self._accel,
            max_freq=self._config.max_freq_vibrations,
            motors=self._motors,
            st_version=self._version,
        )
