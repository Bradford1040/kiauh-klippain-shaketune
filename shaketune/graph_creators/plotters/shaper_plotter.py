# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: shaper_plotter.py
# Description: Plotter for input shaper calibration graphs

from datetime import datetime
from typing import Any, Dict

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from ..base_models import PlotterStrategy
from ..computation_results import ShaperResult
from ..plotting_utils import AxesConfiguration, PlottingConstants, SpectrogramHelper


class ShaperPlotter(PlotterStrategy):
    """Plotter for input shaper calibration graphs"""

    def plot(self, result: ShaperResult) -> Figure:
        """Create input shaper calibration graph"""
        data = result.get_plot_data()

        fig = plt.figure(figsize=(15, 11.6))
        gs = fig.add_gridspec(
            2,
            2,
            height_ratios=[4, 3],
            width_ratios=[5, 4],
            bottom=0.050,
            top=0.890,
            left=0.048,
            right=0.966,
            hspace=0.169,
            wspace=0.150,
        )
        ax_1 = fig.add_subplot(gs[0, 0])
        ax_2 = fig.add_subplot(gs[1, 0])
        ax_3 = fig.add_subplot(gs[1, 1])

        # Add titles and logo
        self._add_titles(fig, data)
        self.add_logo(fig, position=[0.001, 0.924, 0.075, 0.075])
        self.add_version_text(fig, data['st_version'], position=(0.995, 0.985))

        # Plot Frequency Profile
        self._plot_frequency_profile(ax_1, data)

        # Plot time-frequency spectrogram
        self._plot_spectrogram(ax_2, data)

        # Remove ax_3 for now (TODO: re-add vibrations vs acceleration curves in next release)
        ax_3.remove()

        # Print shaper table
        self._add_shaper_table(fig, data)

        # Add filter recommendations
        self._add_recommendations(fig, data)

        return fig

    def _add_titles(self, fig: Figure, data: Dict[str, Any]) -> None:
        """Add title lines to the figure"""
        try:
            filename_parts = data['measurements'][0]['name'].split('_')
            dt = datetime.strptime(f'{filename_parts[2]} {filename_parts[3]}', '%Y%m%d %H%M%S')
            title_line2 = dt.strftime('%x %X') + ' -- ' + filename_parts[1].upper() + ' axis'
            if data['compat']:
                title_line3 = '| Older Klipper version detected, damping ratio'
                title_line4 = '| and SCV are not used for filter recommendations!'
            else:
                max_smoothing_string = (
                    f'default (={data["max_smoothing_computed"]:0.3f})'
                    if data['max_smoothing'] is None
                    else f'{data["max_smoothing"]:0.3f}'
                )
                title_line3 = f'| Square corner velocity: {data["scv"]} mm/s'
                title_line4 = f'| Allowed smoothing: {max_smoothing_string}'
        except Exception:
            title_line2 = data['measurements'][0]['name']
            title_line3 = ''
            title_line4 = ''

        mode, _, _, accel_per_hz, _, sweeping_accel, sweeping_period = data['test_params']
        title_line5 = f'| Mode: {mode}'
        title_line5 += f' -- ApH: {accel_per_hz}' if accel_per_hz is not None else ''
        if mode == 'SWEEPING':
            title_line5 += f' [sweeping period: {sweeping_period} s - accel: {sweeping_accel} mm/s²]'

        title_lines = [
            {
                'x': 0.065,
                'y': 0.965,
                'text': 'INPUT SHAPER CALIBRATION TOOL',
                'fontsize': 20,
                'color': PlottingConstants.KLIPPAIN_COLORS['purple'],
                'weight': 'bold',
            },
            {'x': 0.065, 'y': 0.957, 'va': 'top', 'text': title_line2},
            {'x': 0.481, 'y': 0.990, 'va': 'top', 'fontsize': 11, 'text': title_line5},
            {'x': 0.480, 'y': 0.970, 'va': 'top', 'fontsize': 14, 'text': title_line3},
            {'x': 0.480, 'y': 0.949, 'va': 'top', 'fontsize': 14, 'text': title_line4},
        ]
        self.add_title(fig, title_lines)

    def _plot_frequency_profile(self, ax, data: Dict[str, Any]) -> None:
        """Plot frequency profile with PSDs and shapers"""
        calibration_data = data['calibration_data']
        freqs = calibration_data.freqs
        psd = calibration_data.psd_sum
        px = calibration_data.psd_x
        py = calibration_data.psd_y
        pz = calibration_data.psd_z

        # Plot PSDs
        ax.plot(freqs, psd, label='X+Y+Z', color='purple', zorder=5)
        ax.plot(freqs, px, label='X', color='red')
        ax.plot(freqs, py, label='Y', color='green')
        ax.plot(freqs, pz, label='Z', color='blue')
        ax.set_xlim([0, data['max_freq']])
        ax.set_ylim([0, data['max_scale'] if data['max_scale'] is not None else psd.max() * 1.05])

        # Plot shaper filters on secondary axis
        ax_2 = ax.twinx()
        ax_2.yaxis.set_visible(False)
        for shaper in data['shapers']:
            ax_2.plot(freqs, shaper.vals, label=shaper.name.upper(), linestyle='dotted')

        # Draw shaper filtered PSDs
        shaper_choices = data['shaper_choices']
        for shaper in data['shaper_table_data']['shapers']:
            if shaper['type'] == shaper_choices[0]:
                ax.plot(freqs, psd * shaper['vals'], label=f'With {shaper_choices[0]} applied', color='cyan')
            if len(shaper_choices) > 1 and shaper['type'] == shaper_choices[1]:
                ax.plot(freqs, psd * shaper['vals'], label=f'With {shaper_choices[1]} applied', color='lime')

        # Draw detected peaks
        peaks = data['peaks']
        peaks_freqs = data['peaks_freqs']
        peaks_threshold = data['peaks_threshold']

        ax.plot(peaks_freqs, psd[peaks], 'x', color='black', markersize=8)
        for idx, peak in enumerate(peaks):
            fontcolor = 'red' if psd[peak] > peaks_threshold[1] else 'black'
            fontweight = 'bold' if psd[peak] > peaks_threshold[1] else 'normal'
            ax.annotate(
                f'{idx + 1}',
                (freqs[peak], psd[peak]),
                textcoords='offset points',
                xytext=(8, 5),
                ha='left',
                fontsize=13,
                color=fontcolor,
                weight=fontweight,
            )

        # Add threshold lines and regions
        ax.axhline(y=peaks_threshold[0], color='black', linestyle='--', linewidth=0.5)
        ax.axhline(y=peaks_threshold[1], color='black', linestyle='--', linewidth=0.5)
        ax.fill_between(freqs, 0, peaks_threshold[0], color='green', alpha=0.15, label='Relax Region')
        ax.fill_between(
            freqs, peaks_threshold[0], peaks_threshold[1], color='orange', alpha=0.2, label='Warning Region'
        )

        fontP = AxesConfiguration.configure_axes(
            ax,
            xlabel='Frequency (Hz)',
            ylabel='Power spectral density',
            title=f'Axis Frequency Profile (ω0={data["fr"]:.1f}Hz, ζ={data["zeta"]:.3f})',
            sci_axes='y',
            legend=True,
        )
        ax_2.legend(loc='upper right', prop=fontP)

    def _plot_spectrogram(self, ax, data: Dict[str, Any]) -> None:
        """Plot time-frequency spectrogram"""
        SpectrogramHelper.plot_spectrogram(
            ax,
            data['pdata'],
            data['t'],
            data['bins'],
            data['max_freq'],
            percentile_filter=PlottingConstants.SPECTROGRAM_LOW_PERCENTILE_FILTER,
        )

        # Add peaks lines in the spectrogram
        for idx, peak in enumerate(data['peaks_freqs']):
            ax.axvline(peak, color='cyan', linestyle='dotted', linewidth=1)
            ax.annotate(
                f'Peak {idx + 1} ({peak:.1f} Hz)',
                (peak, data['bins'][-1] * 0.9),
                textcoords='data',
                color='cyan',
                rotation=90,
                fontsize=10,
                verticalalignment='top',
                horizontalalignment='right',
            )

        ax.set_xlim([0.0, data['max_freq']])
        AxesConfiguration.configure_axes(
            ax, xlabel='Frequency (Hz)', ylabel='Time (s)', title='Time-Frequency Spectrogram', grid=False
        )

    def _add_shaper_table(self, fig: Figure, data: Dict[str, Any]) -> None:
        """Add shaper parameters table"""
        columns = ['Type', 'Frequency', 'Vibrations', 'Smoothing', 'Max Accel']
        table_data = [
            [
                shaper['type'].upper(),
                f'{shaper["frequency"]:.1f} Hz',
                f'{shaper["vibrations"] * 100:.1f} %',
                f'{shaper["smoothing"]:.3f}',
                f'{round(shaper["max_accel"] / 10) * 10:.0f}',
            ]
            for shaper in data['shaper_table_data']['shapers']
        ]

        table = plt.table(cellText=table_data, colLabels=columns, bbox=[1.100, 0.535, 0.830, 0.240], cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.auto_set_column_width([0, 1, 2, 3, 4])
        table.set_zorder(100)

        # Style the table
        bold_font = matplotlib.font_manager.FontProperties(weight='bold')
        for key, cell in table.get_celld().items():
            row, col = key
            cell.set_text_props(ha='center', va='center')
            if col == 0:
                cell.get_text().set_fontproperties(bold_font)
                cell.get_text().set_color(PlottingConstants.KLIPPAIN_COLORS['dark_purple'])
            if row == 0:
                cell.get_text().set_fontproperties(bold_font)
                cell.get_text().set_color(PlottingConstants.KLIPPAIN_COLORS['dark_orange'])

    def _add_recommendations(self, fig: Figure, data: Dict[str, Any]) -> None:
        """Add filter recommendations and damping ratio"""
        fig.text(
            0.575,
            0.897,
            'Recommended filters:',
            fontsize=15,
            fontweight='bold',
            color=PlottingConstants.KLIPPAIN_COLORS['dark_purple'],
        )

        recommendations = data['shaper_table_data']['recommendations']
        for idx, rec in enumerate(recommendations):
            fig.text(0.580, 0.867 - idx * 0.025, rec, fontsize=14, color=PlottingConstants.KLIPPAIN_COLORS['purple'])

        new_idx = len(recommendations)
        fig.text(
            0.580,
            0.867 - new_idx * 0.025,
            f'    -> Estimated damping ratio (ζ): {data["shaper_table_data"]["damping_ratio"]:.3f}',
            fontsize=14,
            color=PlottingConstants.KLIPPAIN_COLORS['purple'],
        )
