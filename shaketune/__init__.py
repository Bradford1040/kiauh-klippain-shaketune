# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2023-2026  Shake&Tune contributors Bradford Alden Adams aka (Bradford1040)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: __init__.py
# Description: Functions as a plugin within Klipper to enhance printer diagnostics by:
#              1. Diagnosing and pinpointing vibration sources in the printer.
#              2. Conducting standard axis input shaper tests on the machine axes.
#              3. Executing a specialized half-axis test for CoreXY/CoreXZ printers to analyze
#                 and compare the frequency profiles of individual belts.
#              4. ...


from typing import Any

from .shaketune import ShakeTune as ShakeTune


def load_config(config: Any) -> ShakeTune:
    return ShakeTune(config)
