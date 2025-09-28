# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: __init__.py
# Description: Imports various graph creator classes for the Shake&Tune package.

import os
import sys


def get_shaper_calibrate_module():
    if os.environ.get('SHAKETUNE_IN_CLI') != '1':
        from ... import shaper_calibrate, shaper_defs
    else:
        shaper_calibrate = sys.modules['shaper_calibrate']
        shaper_defs = sys.modules['shaper_defs']
    return shaper_calibrate.ShaperCalibrate(printer=None), shaper_defs


# Import graph creators
from .axes_map_graph_creator import AxesMapGraphCreator  # noqa: E402

# Import utilities
from .base_models import ComputationResult, PlotterStrategy  # noqa: E402
from .belts_graph_creator import BeltsGraphCreator  # noqa: E402

# Import main components
from .graph_creator import GraphCreator  # noqa: E402
from .graph_creator_factory import GraphCreatorFactory  # noqa: E402
from .plotting_utils import AxesConfiguration  # noqa: E402
from .plotting_utils import PeakAnnotator  # noqa: E402
from .plotting_utils import PlottingConstants  # noqa: E402
from .plotting_utils import SpectrogramHelper, TableHelper  # noqa: E402
from .shaper_graph_creator import ShaperGraphCreator  # noqa: E402
from .static_graph_creator import StaticGraphCreator  # noqa: E402
from .vibrations_graph_creator import VibrationsGraphCreator  # noqa: E402

__all__ = [
    'GraphCreator',
    'GraphCreatorFactory',
    'AxesMapGraphCreator',
    'BeltsGraphCreator',
    'ShaperGraphCreator',
    'StaticGraphCreator',
    'VibrationsGraphCreator',
    'ComputationResult',
    'PlotterStrategy',
    'PlottingConstants',
    'AxesConfiguration',
    'SpectrogramHelper',
    'TableHelper',
    'PeakAnnotator',
]
