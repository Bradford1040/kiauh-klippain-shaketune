# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: axes_map_graph_creator.py
# Description: Axes map graph creator implementation

from typing import Optional

from ..helpers.accelerometer import MeasurementsManager
from ..shaketune_config import ShakeTuneConfig
from .computations.axes_map_computation import AxesMapComputation
from .graph_creator import GraphCreator
from .plotters.axes_map_plotter import AxesMapPlotter


@GraphCreator.register('axes map')
class AxesMapGraphCreator(GraphCreator):
    """Axes map graph creator using composition-based architecture"""

    def __init__(self, config: ShakeTuneConfig):
        super().__init__(config, AxesMapComputation, AxesMapPlotter)
        self._accel: Optional[int] = None
        self._segment_length: Optional[float] = None

    def configure(self, accel: int, segment_length: float) -> None:
        """Configure the axes map detection parameters"""
        self._accel = accel
        self._segment_length = segment_length

    def _create_computation(self, measurements_manager: MeasurementsManager) -> AxesMapComputation:
        """Create the computation instance with proper configuration"""
        return AxesMapComputation(
            measurements=measurements_manager.get_measurements(),
            accel=self._accel,
            fixed_length=self._segment_length,
            st_version=self._version,
        )
