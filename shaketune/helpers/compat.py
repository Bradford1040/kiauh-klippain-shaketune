# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: compat.py
# Description: Handles compatibility with different versions of Klipper using feature-based detection.

from collections import namedtuple

ResTesterConfig = namedtuple(
    'ResTesterConfig', ['default_min_freq', 'default_max_freq', 'default_accel_per_hz', 'test_points']
)


class KlipperCompatibility:
    """
    Handles compatibility with different Klipper versions using feature-based detection.
    Instead of categorizing versions as "old" vs "new", this class detects specific
    capabilities to provide appropriate fallbacks and method calls.
    """

    def __init__(self, config, res_tester=None):
        """Initialize with Klipper configuration and cache capability detection."""
        self.printer = config.get_printer()
        self.toolhead = self.printer.lookup_object('toolhead')
        self.res_tester = res_tester if res_tester is not None else self.printer.lookup_object('resonance_tester')

        # Cache capability detection results to avoid repeated hasattr calls
        self._capabilities = {}

    def _check_capability(self, capability_name, obj, attr_name):
        """Check and cache a specific capability."""
        if capability_name not in self._capabilities:
            self._capabilities[capability_name] = hasattr(obj, attr_name)
        return self._capabilities[capability_name]

    # Toolhead acceleration setting capabilities
    def can_set_max_velocities(self):
        """Check if toolhead supports the set_max_velocities method (newer Klipper)."""
        return self._check_capability('set_max_velocities', self.toolhead, 'set_max_velocities')

    def can_use_cmd_m204(self):
        """Check if toolhead supports the cmd_M204 method (older Klipper)."""
        return self._check_capability('cmd_m204', self.toolhead, 'cmd_M204')

    def can_limit_junction_speed(self):
        """Check if toolhead supports junction speed limiting (newer Klipper)."""
        return self._check_capability('limit_junction_speed', self.toolhead, 'limit_next_junction_speed')

    # Resonance tester API capabilities
    def has_legacy_res_tester_api(self):
        """Check if resonance tester uses the legacy API with .test attribute."""
        if self.res_tester is None:
            return False
        return self._check_capability('legacy_res_tester', self.res_tester, 'test')

    def has_modern_res_tester_api(self):
        """Check if resonance tester uses the modern API with generator."""
        if self.res_tester is None:
            return False
        return not self.has_legacy_res_tester_api()

    # Unified methods for common operations
    def set_toolhead_acceleration(self, gcode, accel):
        """
        Set toolhead acceleration using the best available method.
        Tries methods in order: set_max_velocities -> cmd_M204 -> gcode fallback.
        """
        if self.can_set_max_velocities():
            self.toolhead.set_max_velocities(None, abs(accel), None, None)
        elif self.can_use_cmd_m204():
            self.toolhead.cmd_M204(gcode.create_gcode_command('M204', 'M204', {'S': abs(accel)}))
        else:
            raise NotImplementedError('No method found to set toolhead acceleration. Klipper API likely changed.')

    def get_res_tester_config(self) -> ResTesterConfig:
        """
        Get resonance tester configuration using the appropriate API.
        Returns a ResTesterConfig namedtuple with default values and test points.
        """
        if self.has_legacy_res_tester_api():
            # Legacy API (before Dec 6, 2024: https://github.com/Klipper3d/klipper/commit/16b4b6b302ac3ffcd55006cd76265aad4e26ecc8)
            default_min_freq = self.res_tester.test.min_freq
            default_max_freq = self.res_tester.test.max_freq
            default_accel_per_hz = self.res_tester.test.accel_per_hz
            test_points = self.res_tester.test.get_start_test_points()
        else:
            # Modern API (after Dec 6, 2024) with the sweeping test
            default_min_freq = self.res_tester.generator.vibration_generator.min_freq
            default_max_freq = self.res_tester.generator.vibration_generator.max_freq
            default_accel_per_hz = self.res_tester.generator.vibration_generator.accel_per_hz
            test_points = self.res_tester.probe_points

        return ResTesterConfig(default_min_freq, default_max_freq, default_accel_per_hz, test_points)

    def get_res_tester_parameters(self):
        """
        Get resonance tester parameters for the ResonanceTestManager.
        Returns tuple compatible with existing get_parameters() method.
        """
        if self.res_tester is None:
            # Fallback for static frequency tests where res_tester is None
            return (50, 200, 75, 1, 0.0, None)

        if self.has_legacy_res_tester_api():
            return (
                self.res_tester.test.min_freq,
                self.res_tester.test.max_freq,
                self.res_tester.test.accel_per_hz,
                self.res_tester.test.hz_per_sec,
                0.0,  # sweeping_period=0 to force the old style pulse-only test
                None,  # sweeping_accel unused in old style pulse-only test
            )
        else:
            return (
                self.res_tester.generator.vibration_generator.min_freq,
                self.res_tester.generator.vibration_generator.max_freq,
                self.res_tester.generator.vibration_generator.accel_per_hz,
                self.res_tester.generator.vibration_generator.hz_per_sec,
                self.res_tester.generator.sweeping_period,
                self.res_tester.generator.sweeping_accel,
            )
