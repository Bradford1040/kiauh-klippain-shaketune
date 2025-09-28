# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: vibrations_plotter.py
# Description: Plotter for machine vibrations analysis graphs

from datetime import datetime
from typing import Any, Dict

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from ..base_models import PlotterStrategy
from ..computation_results import VibrationsResult
from ..plotting_utils import AxesConfiguration, PlottingConstants


class VibrationsPlotter(PlotterStrategy):
    """Plotter for machine vibrations analysis graphs"""

    def plot(self, result: VibrationsResult) -> Figure:
        """Create machine vibrations analysis graph"""
        data = result.get_plot_data()

        fig = plt.figure(figsize=(20, 11.5))
        gs = fig.add_gridspec(
            2,
            3,
            height_ratios=[1, 1],
            width_ratios=[4, 8, 6],
            bottom=0.050,
            top=0.890,
            left=0.040,
            right=0.985,
            hspace=0.166,
            wspace=0.138,
        )
        ax_1 = fig.add_subplot(gs[0, 0], projection='polar')
        ax_4 = fig.add_subplot(gs[1, 0], projection='polar')
        ax_2 = fig.add_subplot(gs[0, 1])
        ax_3 = fig.add_subplot(gs[0, 2])
        ax_5 = fig.add_subplot(gs[1, 1])
        ax_6 = fig.add_subplot(gs[1, 2])

        # Add titles and logo
        self._add_titles(fig, data)
        self.add_logo(fig, position=[0.001, 0.924, 0.075, 0.075])
        self.add_version_text(fig, data['st_version'], position=(0.995, 0.985))

        # Plot motor info if available
        self._plot_motor_info(fig, data)

        # Plot angle energy profile (Polar plot)
        self._plot_angle_energy_profile(ax_1, data)

        # Plot polar vibrations heatmap
        self._plot_polar_heatmap(ax_4, data)

        # Plot global speed energy profile
        self._plot_speed_energy_profile(ax_2, data)

        # Plot angular speed energy profiles
        self._plot_angular_speed_profiles(ax_3, data)

        # Plot vibrations heatmap
        self._plot_vibrations_heatmap(ax_5, data)

        # Plot motor profiles
        self._plot_motor_profiles(ax_6, data)

        return fig

    def _add_titles(self, fig: Figure, data: Dict[str, Any]) -> None:
        """Add title lines to the figure"""
        try:
            filename_parts = data['measurements'][0]['name'].split('_')
            dt = datetime.strptime(f'{filename_parts[4]} {filename_parts[5].split("-")[0]}', '%Y%m%d %H%M%S')
            title_line2 = dt.strftime('%x %X')
            if data['accel'] is not None:
                title_line2 += f' at {data["accel"]} mm/s² -- {data["kinematics"].upper()} kinematics'
        except Exception:
            title_line2 = data['measurements'][0]['name']

        title_lines = [
            {
                'x': 0.060,
                'y': 0.965,
                'text': 'MACHINE VIBRATIONS ANALYSIS TOOL',
                'fontsize': 20,
                'color': PlottingConstants.KLIPPAIN_COLORS['purple'],
                'weight': 'bold',
            },
            {'x': 0.060, 'y': 0.957, 'va': 'top', 'text': title_line2},
        ]
        self.add_title(fig, title_lines)

    def _plot_motor_info(self, fig: Figure, data: Dict[str, Any]) -> None:
        """Plot motor information if available"""
        motors = data.get('motors')
        if motors is not None and len(motors) == 2:
            motor_details = [(motors[0], 'X motor'), (motors[1], 'Y motor')]
            distance = 0.27 if motors[0].get_config('autotune_enabled') else 0.16

            if motors[0].get_config('autotune_enabled'):
                config_blocks = [
                    f'| {lbl}: {mot.get_config("motor").upper()} on {mot.get_config("tmc").upper()} @ {mot.get_config("voltage"):0.1f}V {mot.get_config("run_current"):0.2f}A - {mot.get_config("microsteps")}usteps'
                    for mot, lbl in motor_details
                ]
                config_blocks.append(
                    f'| TMC Autotune enabled (PWM freq target: X={int(motors[0].get_config("pwm_freq_target") / 1000)}kHz / Y={int(motors[1].get_config("pwm_freq_target") / 1000)}kHz)'
                )
            else:
                config_blocks = [
                    f'| {lbl}: {mot.get_config("tmc").upper()} @ {mot.get_config("run_current"):0.2f}A - {mot.get_config("microsteps")}usteps'
                    for mot, lbl in motor_details
                ]
                config_blocks.append('| TMC Autotune not detected')

            for idx, block in enumerate(config_blocks):
                fig.text(
                    0.41,
                    0.990 - 0.015 * idx,
                    block,
                    ha='left',
                    va='top',
                    fontsize=10,
                    color=PlottingConstants.KLIPPAIN_COLORS['dark_purple'],
                )

            tmc_registers = motors[0].get_registers()
            idx = -1
            for idx, (register, settings) in enumerate(tmc_registers.items()):
                settings_str = ' '.join(f'{k}={v}' for k, v in settings.items())
                tmc_block = f'| {register.upper()}: {settings_str}'
                fig.text(
                    0.41 + distance,
                    0.990 - 0.015 * idx,
                    tmc_block,
                    ha='left',
                    va='top',
                    fontsize=10,
                    color=PlottingConstants.KLIPPAIN_COLORS['dark_purple'],
                )

            if data.get('motors_config_differences') is not None:
                differences_text = f'| Y motor diff: {data["motors_config_differences"]}'
                fig.text(
                    0.41 + distance,
                    0.990 - 0.015 * (idx + 1),
                    differences_text,
                    ha='left',
                    va='top',
                    fontsize=10,
                    color=PlottingConstants.KLIPPAIN_COLORS['dark_purple'],
                )

    def _plot_angle_energy_profile(self, ax, data: Dict[str, Any]) -> None:
        """Plot angle energy profile on polar plot"""
        all_angles = data['all_angles']
        all_angles_energy = data['all_angles_energy']
        good_angles = data.get('good_angles')

        angles_radians = np.deg2rad(all_angles)
        ymax = all_angles_energy.max() * 1.05

        ax.plot(angles_radians, all_angles_energy, color=PlottingConstants.KLIPPAIN_COLORS['purple'], zorder=5)
        ax.fill(angles_radians, all_angles_energy, color=PlottingConstants.KLIPPAIN_COLORS['purple'], alpha=0.3)
        ax.set_xlim([0, np.deg2rad(360)])
        ax.set_ylim([0, ymax])
        ax.set_theta_zero_location('E')
        ax.set_theta_direction(1)
        ax.set_thetagrids([theta * 15 for theta in range(360 // 15)])
        ax.text(
            0,
            0,
            f'Symmetry: {data["symmetry_factor"]:.1f}%',
            ha='center',
            va='center',
            color=PlottingConstants.KLIPPAIN_COLORS['red_pink'],
            fontsize=12,
            fontweight='bold',
            zorder=6,
        )

        if good_angles is not None:
            for start, end, _ in good_angles:
                ax.axvline(
                    angles_radians[start],
                    all_angles_energy[start] / ymax,
                    color=PlottingConstants.KLIPPAIN_COLORS['red_pink'],
                    linestyle='dotted',
                    linewidth=1.5,
                )
                ax.axvline(
                    angles_radians[end],
                    all_angles_energy[end] / ymax,
                    color=PlottingConstants.KLIPPAIN_COLORS['red_pink'],
                    linestyle='dotted',
                    linewidth=1.5,
                )
                ax.fill_between(
                    angles_radians[start:end],
                    all_angles_energy[start:end],
                    all_angles_energy.max() * 1.05,
                    color='green',
                    alpha=0.2,
                )

        AxesConfiguration.configure_axes(ax, title='Polar angle energy profile')

        # Polar plot doesn't follow the gridspec margin, so we adjust it manually here
        pos = ax.get_position()
        new_pos = [pos.x0 - 0.01, pos.y0 - 0.01, pos.width, pos.height]
        ax.set_position(new_pos)

    def _plot_polar_heatmap(self, ax, data: Dict[str, Any]) -> None:
        """Plot polar vibrations heatmap"""
        all_speeds = data['all_speeds']
        all_angles = data['all_angles']
        spectrogram_data = data['spectrogram_data']

        angles_radians = np.deg2rad(all_angles)
        radius, theta = np.meshgrid(all_speeds, angles_radians)

        ax.pcolormesh(theta, radius, spectrogram_data, norm=matplotlib.colors.LogNorm(), cmap='inferno', shading='auto')
        ax.set_theta_zero_location('E')
        ax.set_theta_direction(1)
        ax.set_thetagrids([theta * 15 for theta in range(360 // 15)])
        ax.set_ylim([0, max(all_speeds)])
        AxesConfiguration.configure_axes(ax, title='Polar vibrations heatmap', grid=False)

        ax.tick_params(axis='y', which='both', colors='white', labelsize='medium')

        # Polar plot doesn't follow the gridspec margin, so we adjust it manually here
        pos = ax.get_position()
        new_pos = [pos.x0 - 0.01, pos.y0 - 0.01, pos.width, pos.height]
        ax.set_position(new_pos)

    def _plot_speed_energy_profile(self, ax, data: Dict[str, Any]) -> None:
        """Plot global speed energy profile"""
        all_speeds = data['all_speeds']
        sp_min_energy = data['sp_min_energy']
        sp_max_energy = data['sp_max_energy']
        sp_variance_energy = data['sp_variance_energy']
        vibration_metric = data['vibration_metric']
        vibration_peaks = data.get('vibration_peaks')
        good_speeds = data.get('good_speeds')
        num_peaks = data['num_peaks']

        ax.plot(
            all_speeds, sp_min_energy, label='Minimum', color=PlottingConstants.KLIPPAIN_COLORS['dark_purple'], zorder=5
        )
        ax.plot(all_speeds, sp_max_energy, label='Maximum', color=PlottingConstants.KLIPPAIN_COLORS['purple'], zorder=5)
        ax.plot(
            all_speeds,
            sp_variance_energy,
            label='Variance',
            color=PlottingConstants.KLIPPAIN_COLORS['orange'],
            zorder=5,
            linestyle='--',
        )
        ax.set_xlim([all_speeds.min(), all_speeds.max()])
        ax.set_ylim([0, sp_max_energy.max() * 1.15])

        # Add a secondary axis to plot the vibration metric
        ax_2 = ax.twinx()
        ax_2.yaxis.set_visible(False)
        ax_2.plot(
            all_speeds,
            vibration_metric,
            label=f'Vibration metric ({num_peaks} bad peaks)',
            color=PlottingConstants.KLIPPAIN_COLORS['red_pink'],
            zorder=5,
        )
        ax_2.set_ylim([-(vibration_metric.max() * 0.025), vibration_metric.max() * 1.07])

        if vibration_peaks is not None and len(vibration_peaks) > 0:
            ax_2.plot(
                all_speeds[vibration_peaks],
                vibration_metric[vibration_peaks],
                'x',
                color='black',
                markersize=8,
                zorder=10,
            )
            for idx, peak in enumerate(vibration_peaks):
                ax_2.annotate(
                    f'{idx + 1}',
                    (all_speeds[peak], vibration_metric[peak]),
                    textcoords='offset points',
                    xytext=(5, 5),
                    fontweight='bold',
                    ha='left',
                    fontsize=13,
                    color=PlottingConstants.KLIPPAIN_COLORS['red_pink'],
                    zorder=10,
                )

        if good_speeds is not None:
            for idx, (start, end, _) in enumerate(good_speeds):
                ax_2.fill_between(
                    all_speeds[start:end],
                    -(vibration_metric.max() * 0.025),
                    vibration_metric[start:end],
                    color='green',
                    alpha=0.2,
                    label=f'Zone {idx + 1}: {all_speeds[start]:.1f} to {all_speeds[end]:.1f} mm/s',
                )

        fontP = AxesConfiguration.configure_axes(
            ax, xlabel='Speed (mm/s)', ylabel='Energy', title='Global speed energy profile', legend=True
        )
        ax_2.legend(loc='upper right', prop=fontP)

    def _plot_angular_speed_profiles(self, ax, data: Dict[str, Any]) -> None:
        """Plot angular speed energy profiles"""
        all_speeds = data['all_speeds']
        all_angles = data['all_angles']
        spectrogram_data = data['spectrogram_data']
        kinematics = data['kinematics']

        angle_settings = {
            0: ('X (0 deg)', 'purple', 10),
            90: ('Y (90 deg)', 'dark_purple', 5),
            45: ('A (45 deg)' if kinematics in {'corexy', 'limited_corexy'} else '45 deg', 'orange', 10),
            135: ('B (135 deg)' if kinematics in {'corexy', 'limited_corexy'} else '135 deg', 'dark_orange', 5),
        }

        for angle, (label, color, zorder) in angle_settings.items():
            idx = np.searchsorted(all_angles, angle, side='left')
            ax.plot(
                all_speeds,
                spectrogram_data[idx],
                label=label,
                color=PlottingConstants.KLIPPAIN_COLORS[color],
                zorder=zorder,
            )

        ax.set_xlim([all_speeds.min(), all_speeds.max()])
        max_value = max(
            spectrogram_data[np.searchsorted(all_angles, angle, side='left')].max() for angle in angle_settings
        )
        ax.set_ylim([0, max_value * 1.1])
        fontP = AxesConfiguration.configure_axes(
            ax, xlabel='Speed (mm/s)', ylabel='Energy', title='Angular speed energy profiles', legend=False
        )
        ax.legend(loc='upper right', prop=fontP)

    def _plot_vibrations_heatmap(self, ax, data: Dict[str, Any]) -> None:
        """Plot vibrations heatmap"""
        all_speeds = data['all_speeds']
        all_angles = data['all_angles']
        spectrogram_data = data['spectrogram_data']
        vibration_peaks = data.get('vibration_peaks')

        ax.imshow(
            spectrogram_data,
            norm=matplotlib.colors.LogNorm(),
            cmap='inferno',
            aspect='auto',
            extent=[all_speeds[0], all_speeds[-1], all_angles[0], all_angles[-1]],
            origin='lower',
            interpolation='antialiased',
        )

        # Add vibrations peaks lines in the spectrogram
        if vibration_peaks is not None and len(vibration_peaks) > 0:
            for idx, peak in enumerate(vibration_peaks):
                ax.axvline(all_speeds[peak], color='cyan', linewidth=0.75)
                ax.annotate(
                    f'Peak {idx + 1} ({all_speeds[peak]:.1f} mm/s)',
                    (all_speeds[peak], all_angles[-1] * 0.9),
                    textcoords='data',
                    color='cyan',
                    rotation=90,
                    fontsize=10,
                    verticalalignment='top',
                    horizontalalignment='right',
                )

        AxesConfiguration.configure_axes(
            ax, xlabel='Speed (mm/s)', ylabel='Angle (deg)', title='Vibrations heatmap', grid=False
        )

    def _plot_motor_profiles(self, ax, data: Dict[str, Any]) -> None:
        """Plot motor frequency profiles"""
        target_freqs = data['target_freqs']
        global_motor_profile = data['global_motor_profile']
        motor_profiles = data['motor_profiles']
        main_angles = data['main_angles']
        max_freq = data['max_freq']
        motor_res_idx = data['motor_res_idx']
        motor_fr = data['motor_fr']
        motor_zeta = data.get('motor_zeta')
        kinematics = data['kinematics']

        angle_settings = {
            0: ('X (0 deg)', 'purple', 10),
            90: ('Y (90 deg)', 'dark_purple', 5),
            45: ('A (45 deg)' if kinematics in {'corexy', 'limited_corexy'} else '45 deg', 'orange', 10),
            135: ('B (135 deg)' if kinematics in {'corexy', 'limited_corexy'} else '135 deg', 'dark_orange', 5),
        }

        ax.plot(
            target_freqs,
            global_motor_profile,
            label='Combined',
            color=PlottingConstants.KLIPPAIN_COLORS['purple'],
            zorder=5,
        )
        max_value = global_motor_profile.max()

        for angle in main_angles:
            profile_max = motor_profiles[angle].max()
            if profile_max > max_value:
                max_value = profile_max
            label = f'{angle_settings.get(angle, (f"{angle} deg",))[0]}'
            ax.plot(target_freqs, motor_profiles[angle], linestyle='--', label=label, zorder=2)

        ax.set_xlim([0, max_freq])
        ax.set_ylim([0, max_value * 1.1])

        # Add the motor resonance peak to the graph
        ax.plot(target_freqs[motor_res_idx], global_motor_profile[motor_res_idx], 'x', color='black', markersize=10)
        ax.annotate(
            'R',
            (target_freqs[motor_res_idx], global_motor_profile[motor_res_idx]),
            textcoords='offset points',
            xytext=(15, 5),
            ha='right',
            fontsize=14,
            color=PlottingConstants.KLIPPAIN_COLORS['red_pink'],
            weight='bold',
        )

        ax_2 = ax.twinx()
        ax_2.yaxis.set_visible(False)
        ax_2.plot([], [], ' ', label=f'Motor resonant frequency (ω0): {motor_fr:.1f}Hz')
        if motor_zeta is not None:
            ax_2.plot([], [], ' ', label=f'Motor damping ratio (ζ): {motor_zeta:.3f}')
        else:
            ax_2.plot([], [], ' ', label='No damping ratio computed')

        fontP = AxesConfiguration.configure_axes(
            ax, xlabel='Frequency (Hz)', ylabel='Energy', title='Motor frequency profile', sci_axes='y', legend=True
        )
        ax_2.legend(loc='upper right', prop=fontP)
