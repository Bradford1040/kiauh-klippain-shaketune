# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: belts_plotter.py
# Description: Plotter for belts comparison graphs

from datetime import datetime
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from ..base_models import PlotterStrategy
from ..computation_results import BeltsResult
from ..plotting_utils import AxesConfiguration, PeakAnnotator, PlottingConstants


class BeltsPlotter(PlotterStrategy):
    """Plotter for belts comparison graphs"""

    def plot(self, result: BeltsResult) -> Figure:
        """Create belts comparison graph"""
        data = result.get_plot_data()

        fig, axes = plt.subplots(
            1,
            2,
            gridspec_kw={
                'width_ratios': [5, 3],
                'bottom': 0.080,
                'top': 0.840,
                'left': 0.050,
                'right': 0.985,
                'hspace': 0.166,
                'wspace': 0.138,
            },
            figsize=(15, 7),
        )
        ax_1, ax_2 = axes

        # Add titles and logo
        self._add_titles(fig, data)
        self.add_logo(fig)
        self.add_version_text(fig, data['st_version'])

        # Plot PSD signals
        self._plot_psd_signals(ax_1, data)

        # Plot cross-belts comparison
        self._plot_cross_comparison(ax_2, data)

        return fig

    def _add_titles(self, fig: Figure, data: Dict[str, Any]) -> None:
        """Add title lines to the figure"""
        try:
            filename = data['measurements'][0]['name']
            dt = datetime.strptime(f'{filename.split("_")[2]} {filename.split("_")[3]}', '%Y%m%d %H%M%S')
            title_line2 = dt.strftime('%x %X')
            if data['kinematics'] is not None:
                title_line2 += ' -- ' + data['kinematics'].upper() + ' kinematics'
        except Exception:
            title_line2 = data['measurements'][0]['name'] + ' / ' + data['measurements'][1]['name']

        mode, _, _, accel_per_hz, _, sweeping_accel, sweeping_period = data['test_params']
        title_line3 = f'| Mode: {mode}'
        title_line3 += f' -- ApH: {accel_per_hz}' if accel_per_hz is not None else ''
        if mode == 'SWEEPING':
            title_line3 += f' [sweeping period: {sweeping_period} s - accel: {sweeping_accel} mm/s²]'

        title_lines = [
            {
                'x': 0.060,
                'y': 0.947,
                'text': 'RELATIVE BELTS CALIBRATION TOOL',
                'fontsize': 20,
                'color': PlottingConstants.KLIPPAIN_COLORS['purple'],
                'weight': 'bold',
            },
            {'x': 0.060, 'y': 0.939, 'va': 'top', 'text': title_line2},
            {
                'x': 0.481,
                'y': 0.985,
                'va': 'top',
                'fontsize': 10,
                'text': title_line3,
            },
        ]

        if data['kinematics'] in {'limited_corexy', 'corexy', 'limited_corexz', 'corexz'}:
            title_lines.extend(
                [
                    {
                        'x': 0.480,
                        'y': 0.953,
                        'va': 'top',
                        'fontsize': 13,
                        'text': f'| Estimated similarity: {data["similarity_factor"]:.1f}%',
                    },
                    {'x': 0.480, 'y': 0.920, 'va': 'top', 'fontsize': 13, 'text': f'| {data["mhi"]} (experimental)'},
                ]
            )

        self.add_title(fig, title_lines)

    def _plot_psd_signals(self, ax, data: Dict[str, Any]) -> None:
        """Plot PSD signals and annotate peaks"""
        signal1 = data['signal1']
        signal2 = data['signal2']

        # Plot PSD curves
        ax.plot(
            signal1.freqs,
            signal1.psd,
            label='Belt ' + data['signal1_belt'],
            color=PlottingConstants.KLIPPAIN_COLORS['orange'],
        )
        ax.plot(
            signal2.freqs,
            signal2.psd,
            label='Belt ' + data['signal2_belt'],
            color=PlottingConstants.KLIPPAIN_COLORS['purple'],
        )

        psd_highest_max = max(signal1.psd.max(), signal2.psd.max())
        ax.set_xlim([0, data['max_freq']])
        ax.set_ylim([0, data['max_scale'] if data['max_scale'] is not None else psd_highest_max * 1.1])

        # Annotate peaks
        self._annotate_psd_peaks(ax, signal1, signal2, psd_highest_max)

        # Add unpaired peaks count to secondary legend
        unpaired_count = len(signal1.unpaired_peaks) + len(signal2.unpaired_peaks)
        ax_2 = ax.twinx()
        ax_2.yaxis.set_visible(False)
        ax_2.plot([], [], ' ', label=f'Number of unpaired peaks: {unpaired_count}')

        fontP = AxesConfiguration.configure_axes(
            ax,
            xlabel='Frequency (Hz)',
            ylabel='Power spectral density',
            title='Belts frequency profiles',
            sci_axes='y',
            legend=True,
        )
        ax_2.legend(loc='upper right', prop=fontP)

        # Add offset table if there are paired peaks
        if len(signal1.paired_peaks) > 0:
            self._add_offset_table(ax, signal1, psd_highest_max)

    def _annotate_psd_peaks(self, ax, signal1, signal2, psd_highest_max):
        """Annotate paired and unpaired peaks on PSD plot"""
        paired_peak_count = 0
        unpaired_peak_count = 0

        # Annotate paired peaks
        for _, (peak1, peak2) in enumerate(signal1.paired_peaks):
            label = PlottingConstants.ALPHABET[paired_peak_count]

            ax.plot(signal1.freqs[peak1[0]], signal1.psd[peak1[0]], 'x', color='black')
            ax.plot(signal2.freqs[peak2[0]], signal2.psd[peak2[0]], 'x', color='black')
            ax.plot(
                [signal1.freqs[peak1[0]], signal2.freqs[peak2[0]]],
                [signal1.psd[peak1[0]], signal2.psd[peak2[0]]],
                ':',
                color='gray',
            )

            PeakAnnotator.annotate_peak(ax, signal1.freqs[peak1[0]], signal1.psd[peak1[0]], label + '1')
            PeakAnnotator.annotate_peak(ax, signal2.freqs[peak2[0]], signal2.psd[peak2[0]], label + '2')
            paired_peak_count += 1

        # Annotate unpaired peaks
        for peak in signal1.unpaired_peaks:
            ax.plot(signal1.freqs[peak], signal1.psd[peak], 'x', color='black')
            PeakAnnotator.annotate_peak(
                ax, signal1.freqs[peak], signal1.psd[peak], str(unpaired_peak_count + 1), color='red', weight='bold'
            )
            unpaired_peak_count += 1

        for peak in signal2.unpaired_peaks:
            ax.plot(signal2.freqs[peak], signal2.psd[peak], 'x', color='black')
            PeakAnnotator.annotate_peak(
                ax, signal2.freqs[peak], signal2.psd[peak], str(unpaired_peak_count + 1), color='red', weight='bold'
            )
            unpaired_peak_count += 1

    def _add_offset_table(self, ax, signal1, psd_highest_max):
        """Add table showing frequency and amplitude offsets"""
        offsets_table_data = []

        for _, (peak1, peak2) in enumerate(signal1.paired_peaks):
            label = PlottingConstants.ALPHABET[_]
            amplitude_offset = abs(((signal1.psd[peak2[0]] - signal1.psd[peak1[0]]) / psd_highest_max) * 100)
            frequency_offset = abs(signal1.freqs[peak2[0]] - signal1.freqs[peak1[0]])
            offsets_table_data.append([f'Peaks {label}', f'{frequency_offset:.1f} Hz', f'{amplitude_offset:.1f} %'])

        columns = ['', 'Frequency delta', 'Amplitude delta']
        offset_table = ax.table(
            cellText=offsets_table_data,
            colLabels=columns,
            bbox=[0.66, 0.79, 0.33, 0.15],
            loc='upper right',
            cellLoc='center',
        )
        offset_table.auto_set_font_size(False)
        offset_table.set_fontsize(8)
        offset_table.auto_set_column_width([0, 1, 2])
        offset_table.set_zorder(100)
        for cell in offset_table.get_celld().values():
            cell.set_facecolor('white')
            cell.set_alpha(0.6)

    def _plot_cross_comparison(self, ax, data: Dict[str, Any]) -> None:
        """Plot cross-belts comparison"""
        signal1 = data['signal1']
        signal2 = data['signal2']

        # Plot ideal zone
        max_psd = max(np.max(signal1.psd), np.max(signal2.psd))
        ideal_line = np.linspace(0, max_psd * 1.1, 500)
        green_boundary = ideal_line + (0.35 * max_psd * np.exp(-ideal_line / (0.6 * max_psd)))

        ax.fill_betweenx(ideal_line, ideal_line, green_boundary, color='green', alpha=0.15)
        ax.fill_between(ideal_line, ideal_line, green_boundary, color='green', alpha=0.15, label='Good zone')
        ax.plot(ideal_line, ideal_line, '--', label='Ideal line', color='red', linewidth=2)

        # Plot data
        ax.plot(signal1.psd, signal2.psd, color='dimgrey', marker='o', markersize=1.5)
        ax.fill_betweenx(signal2.psd, signal1.psd, color=PlottingConstants.KLIPPAIN_COLORS['red_pink'], alpha=0.1)

        # Annotate peaks
        self._annotate_cross_peaks(ax, signal1, signal2)

        ax.set_xlim([0, max_psd * 1.1])
        ax.set_ylim([0, max_psd * 1.1])

        AxesConfiguration.configure_axes(
            ax,
            xlabel=f'Belt {data["signal1_belt"]}',
            ylabel=f'Belt {data["signal2_belt"]}',
            title='Cross-belts comparison plot',
            sci_axes='xy',
            legend=True,
        )

    def _annotate_cross_peaks(self, ax, signal1, signal2):
        """Annotate peaks on cross-comparison plot"""
        paired_peak_count = 0
        unpaired_peak_count = 0

        # Annotate paired peaks
        for _, (peak1, peak2) in enumerate(signal1.paired_peaks):
            label = PlottingConstants.ALPHABET[paired_peak_count]
            freq1 = signal1.freqs[peak1[0]]
            freq2 = signal2.freqs[peak2[0]]

            if abs(freq1 - freq2) < 1:
                ax.plot(signal1.psd[peak1[0]], signal2.psd[peak2[0]], marker='o', color='black', markersize=7)
                ax.annotate(
                    f'{label}1/{label}2',
                    (signal1.psd[peak1[0]], signal2.psd[peak2[0]]),
                    textcoords='offset points',
                    xytext=(-7, 7),
                    fontsize=13,
                    color='black',
                )
            else:
                ax.plot(
                    signal1.psd[peak2[0]],
                    signal2.psd[peak2[0]],
                    marker='o',
                    color=PlottingConstants.KLIPPAIN_COLORS['purple'],
                    markersize=7,
                )
                ax.plot(
                    signal1.psd[peak1[0]],
                    signal2.psd[peak1[0]],
                    marker='o',
                    color=PlottingConstants.KLIPPAIN_COLORS['orange'],
                    markersize=7,
                )
                ax.annotate(
                    f'{label}1',
                    (signal1.psd[peak1[0]], signal2.psd[peak1[0]]),
                    textcoords='offset points',
                    xytext=(0, 7),
                    fontsize=13,
                    color='black',
                )
                ax.annotate(
                    f'{label}2',
                    (signal1.psd[peak2[0]], signal2.psd[peak2[0]]),
                    textcoords='offset points',
                    xytext=(0, 7),
                    fontsize=13,
                    color='black',
                )
            paired_peak_count += 1

        # Annotate unpaired peaks
        for _, peak_index in enumerate(signal1.unpaired_peaks):
            ax.plot(
                signal1.psd[peak_index],
                signal2.psd[peak_index],
                marker='o',
                color=PlottingConstants.KLIPPAIN_COLORS['orange'],
                markersize=7,
            )
            ax.annotate(
                str(unpaired_peak_count + 1),
                (signal1.psd[peak_index], signal2.psd[peak_index]),
                textcoords='offset points',
                fontsize=13,
                weight='bold',
                color=PlottingConstants.KLIPPAIN_COLORS['red_pink'],
                xytext=(0, 7),
            )
            unpaired_peak_count += 1

        for _, peak_index in enumerate(signal2.unpaired_peaks):
            ax.plot(
                signal1.psd[peak_index],
                signal2.psd[peak_index],
                marker='o',
                color=PlottingConstants.KLIPPAIN_COLORS['purple'],
                markersize=7,
            )
            ax.annotate(
                str(unpaired_peak_count + 1),
                (signal1.psd[peak_index], signal2.psd[peak_index]),
                textcoords='offset points',
                fontsize=13,
                weight='bold',
                color=PlottingConstants.KLIPPAIN_COLORS['red_pink'],
                xytext=(0, 7),
            )
            unpaired_peak_count += 1
