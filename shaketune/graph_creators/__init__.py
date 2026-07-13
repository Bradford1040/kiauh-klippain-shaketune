# Shake&Tune: 3D printer analysis tools
#
#
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: __init__.py
# Description: Imports various graph creator classes for the Shake&Tune package.

import inspect
import os
import sys


# Klipper API compatibility detection cache
_klipper_api_cache = {}


def _has_name_param_in_process_accel_data(shaper_calibrate):
    """Detect if process_accelerometer_data requires name parameter (new Klipper API after Dec 2024)"""
    if 'has_name_param' not in _klipper_api_cache:
        try:
            sig = inspect.signature(shaper_calibrate.process_accelerometer_data)
            # Check by parameter name for robustness against signature reordering
            _klipper_api_cache['has_name_param'] = 'name' in sig.parameters
        except (ValueError, TypeError):
            _klipper_api_cache['has_name_param'] = False
    return _klipper_api_cache['has_name_param']


def _normalize_find_best_shaper_result(result):
    """Normalize find_best_shaper return to (shaper, results) tuple for all Klipper versions"""
    if isinstance(result, list):
        # New API (Klipper commit baf188b): [shaper] + results
        return result[0], result[1:]
    elif isinstance(result, tuple) and len(result) == 2:
        # Intermediate API (Klipper commit c339bb0): (shaper, results)
        return result
    elif hasattr(result, 'name'):
        # Old API: just shaper object (has name attribute like 'mzv', 'zv', etc.)
        return result, []
    else:
        # Unexpected format - return as-is and let downstream code handle it
        # This helps with debugging if Klipper API changes unexpectedly
        return result, []


def process_accelerometer_data_compat(shaper_calibrate, data, name=None):
    """Call process_accelerometer_data with correct signature for the Klipper version"""
    if _has_name_param_in_process_accel_data(shaper_calibrate):
        return shaper_calibrate.process_accelerometer_data(name, data)
    else:
        return shaper_calibrate.process_accelerometer_data(data)


def find_best_shaper_compat(shaper_calibrate, *args, **kwargs):
    """Call find_best_shaper and normalize return value to (shaper, results) tuple"""
    result = shaper_calibrate.find_best_shaper(*args, **kwargs)
    return _normalize_find_best_shaper_result(result)


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
    'get_shaper_calibrate_module',
    'process_accelerometer_data_compat',
    'find_best_shaper_compat',
]