# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2023-2026  Shake&Tune contributors Bradford Alden Adams aka (Bradford1040)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: vibrations_graph_creator.py
# Description: Machine vibrations graph creator implementation

from typing import Any, Optional

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
        self._kinematics: str = ''
        self._accel: float = 0.0
        self._motors: Optional[list[Motor]] = None

    def configure(self, *args: Any, **kwargs: Any) -> None:
        """Configure the vibrations analysis parameters"""
        self._kinematics = kwargs.get('kinematics', args[0] if len(args) > 0 else '')
        self._accel = float(kwargs.get('accel', args[1] if len(args) > 1 else 0.0))
        self._motors = kwargs.get('motors', args[2] if len(args) > 2 else None)

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
