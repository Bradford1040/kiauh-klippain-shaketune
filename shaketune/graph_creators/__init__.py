# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2026  Bradford Adams <bradfordaldenadams@gmail.com> (Bradford1040 or 𝔅яа∂ƒøя∂¹⁰⁴⁰)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: __init__.py
# Description: Imports various graph creator classes for the Shake&Tune package.

import os
import sys


def get_shaper_calibrate_module():
    # In CLI mode, the modules are pre-loaded.
    if os.environ.get('SHAKETUNE_IN_CLI') == '1':
        shaper_calibrate = sys.modules['shaper_calibrate']
        shaper_defs = sys.modules['shaper_defs']
        return shaper_calibrate.ShaperCalibrate(printer=None), shaper_defs

    # In Klipper plugin mode, we need to find the modules.
    try:
        # This will work if Klipper is in the python path or if the IDE
        # is configured with extraPaths (recommended for development).
        from importlib import import_module
        klippy_extras = import_module('klippy.extras')
        shaper_calibrate = klippy_extras.shaper_calibrate
        shaper_defs = klippy_extras.shaper_defs
    except ImportError as e:
        # Fallback for when running as a Klipper plugin where the path might
        # not be configured in the environment.
        klipper_path = os.path.expanduser('~/klipper')
        klipper_extras_path = os.path.join(klipper_path, 'klippy', 'extras')

        if klipper_extras_path not in sys.path:
            sys.path.insert(0, klipper_extras_path)

        try:
            shaper_calibrate = import_module('shaper_calibrate')
            shaper_defs = import_module('shaper_defs')
        except ImportError:
            # If both methods fail, raise a comprehensive error message.
            raise ImportError(
                "Could not import shaper_calibrate from Klipper. Please ensure Klipper is installed "
                "at '~/klipper' or that the path is configured in your environment (e.g. VSCode's extraPaths)."
            ) from e

    return shaper_calibrate.ShaperCalibrate(printer=None), shaper_defs


from .axes_map_graph_creator import AxesMapGraphCreator as AxesMapGraphCreator  # noqa: E402
from .belts_graph_creator import BeltsGraphCreator as BeltsGraphCreator  # noqa: E402
from .graph_creator import GraphCreator as GraphCreator  # noqa: E402
from .graph_creator_factory import GraphCreatorFactory as GraphCreatorFactory  # noqa: E402
from .shaper_graph_creator import ShaperGraphCreator as ShaperGraphCreator  # noqa: E402
from .static_graph_creator import StaticGraphCreator as StaticGraphCreator  # noqa: E402
from .vibrations_graph_creator import VibrationsGraphCreator as VibrationsGraphCreator  # noqa: E402
