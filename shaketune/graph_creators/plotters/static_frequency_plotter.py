# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: static_frequency_plotter.py
# Description: Plotter for static frequency graphs

from datetime import datetime
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from ..base_models import PlotterStrategy
from ..computation_results import StaticFrequencyResult
from ..plotting_utils import AxesConfiguration, PlottingConstants, SpectrogramHelper


class StaticFrequencyPlotter(PlotterStrategy):
    """Plotter for static frequency graphs"""

    def plot(self, result: StaticFrequencyResult) -> Figure:
        """Create static frequency graph"""
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

        # Plot spectrogram
        self._plot_spectrogram(ax_1, data)

        # Plot cumulative energy
        self._plot_cumulative_energy(ax_2, data)

        return fig

    def _add_titles(self, fig: Figure, data: Dict[str, Any]) -> None:
        """Add title lines to the figure"""
        try:
            filename_parts = data['measurements'][0]['name'].split('_')
            dt = datetime.strptime(f'{filename_parts[2]} {filename_parts[3]}', '%Y%m%d %H%M%S')
            title_line2 = dt.strftime('%x %X') + ' -- ' + filename_parts[1].upper() + ' axis'
        except Exception:
            title_line2 = data['measurements'][0]['name']

        title_line3 = f'| Maintained frequency: {data["freq"]}Hz' if data['freq'] is not None else ''
        title_line3 += f' for {data["duration"]}s' if data['duration'] is not None and title_line3 != '' else ''

        title_lines = [
            {
                'x': 0.060,
                'y': 0.947,
                'text': 'STATIC FREQUENCY HELPER TOOL',
                'fontsize': 20,
                'color': PlottingConstants.KLIPPAIN_COLORS['purple'],
                'weight': 'bold',
            },
            {'x': 0.060, 'y': 0.939, 'va': 'top', 'text': title_line2},
            {'x': 0.55, 'y': 0.985, 'va': 'top', 'fontsize': 14, 'text': title_line3},
            {
                'x': 0.55,
                'y': 0.950,
                'va': 'top',
                'fontsize': 11,
                'text': f'| Accel per Hz used: {data["accel_per_hz"]} mm/s²/Hz'
                if data['accel_per_hz'] is not None
                else '',
            },
        ]
        self.add_title(fig, title_lines)

    def _plot_spectrogram(self, ax, data: Dict[str, Any]) -> None:
        """Plot the time-frequency spectrogram"""
        SpectrogramHelper.plot_spectrogram(ax, data['pdata'], data['t'], data['bins'], data['max_freq'])

        AxesConfiguration.configure_axes(
            ax, xlabel='Frequency (Hz)', ylabel='Time (s)', grid=False, title='Time-Frequency Spectrogram'
        )

    def _plot_cumulative_energy(self, ax, data: Dict[str, Any]) -> None:
        """Plot cumulative energy"""
        cumulative_energy = np.trapz(data['pdata'], data['t'], axis=0)
        ax.plot(cumulative_energy, data['bins'], color=PlottingConstants.KLIPPAIN_COLORS['orange'])
        ax.set_ylim([data['bins'][0], data['bins'][-1]])

        AxesConfiguration.configure_axes(
            ax, xlabel='Cumulative Energy', ylabel='Time (s)', sci_axes='x', title='Vibrations', legend=False
        )
