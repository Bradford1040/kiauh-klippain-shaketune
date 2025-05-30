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
        # Non-CLI mode. Assume shaper_calibrate.py and shaper_defs.py
        # are at the project root (two levels up from this file's directory).
        # The project root is the parent directory of the 'shaketune' package.
        # current file: .../shaketune/graph_creators/__init__.py
        # project_root: .../ (e.g., kiauh-klippain-shaketune/)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        import shaper_calibrate
        import shaper_defs
    else:
        shaper_calibrate = sys.modules['shaper_calibrate']
        shaper_defs = sys.modules['shaper_defs']
    return shaper_calibrate.ShaperCalibrate(printer=None), shaper_defs


from .axes_map_graph_creator import AxesMapGraphCreator as AxesMapGraphCreator  # noqa: E402
from .belts_graph_creator import BeltsGraphCreator as BeltsGraphCreator  # noqa: E402
from .graph_creator import GraphCreator as GraphCreator  # noqa: E402
from .graph_creator_factory import GraphCreatorFactory as GraphCreatorFactory  # noqa: E402
from .shaper_graph_creator import ShaperGraphCreator as ShaperGraphCreator  # noqa: E402
from .static_graph_creator import StaticGraphCreator as StaticGraphCreator  # noqa: E402
from .vibrations_graph_creator import VibrationsGraphCreator as VibrationsGraphCreator  # noqa: E402
