# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: plotting_utils.py
# Description: Common plotting utilities and helpers

from typing import List, Optional, Tuple

import matplotlib
import matplotlib.font_manager
import matplotlib.ticker
import numpy as np


class PlottingConstants:
    """Constants used across plotting functions"""

    KLIPPAIN_COLORS = {
        'purple': '#70088C',
        'orange': '#FF8D32',
        'dark_purple': '#150140',
        'dark_orange': '#F24130',
        'red_pink': '#F2055C',
    }

    # Spectrogram settings
    SPECTROGRAM_LOW_PERCENTILE_FILTER = 5

    # Belts tool
    ALPHABET = 'αβγδεζηθικλμνξοπρστυφχψω'  # Greek alphabet for paired peak names

    # Input shaper tool
    MAX_VIBRATIONS_PLOTTED = 80.0
    MAX_VIBRATIONS_PLOTTED_ZOOM = 1.25


class AxesConfiguration:
    """Helper class for configuring matplotlib axes"""

    @staticmethod
    def configure_axes(
        ax: matplotlib.axes.Axes,
        xlabel: str = '',
        ylabel: str = '',
        zlabel: str = '',
        title: str = '',
        grid: bool = True,
        sci_axes: str = '',
        legend: bool = False,
    ) -> matplotlib.font_manager.FontProperties:
        """Configure axes with common settings"""
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        fontP = matplotlib.font_manager.FontProperties()
        fontP.set_size('x-small')

        if zlabel != '':
            ax.set_zlabel(zlabel)

        if title != '':
            ax.set_title(title, fontsize=14, color=PlottingConstants.KLIPPAIN_COLORS['dark_orange'], weight='bold')

        if grid:
            ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
            ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
            ax.grid(which='major', color='grey')
            ax.grid(which='minor', color='lightgrey')

        if 'x' in sci_axes:
            ax.ticklabel_format(axis='x', style='scientific', scilimits=(0, 0))
        if 'y' in sci_axes:
            ax.ticklabel_format(axis='y', style='scientific', scilimits=(0, 0))

        if legend:
            ax.legend(loc='upper left', prop=fontP)

        return fontP


class SpectrogramHelper:
    """Helper class for spectrogram plotting"""

    @staticmethod
    def plot_spectrogram(
        ax: matplotlib.axes.Axes,
        pdata: np.ndarray,
        t: np.ndarray,
        bins: np.ndarray,
        max_freq: float,
        percentile_filter: float = PlottingConstants.SPECTROGRAM_LOW_PERCENTILE_FILTER,
    ) -> None:
        """Plot a time-frequency spectrogram"""
        vmin_value = np.percentile(pdata, percentile_filter)

        ax.imshow(
            pdata.T,
            norm=matplotlib.colors.LogNorm(vmin=vmin_value),
            cmap='inferno',
            aspect='auto',
            extent=[t[0], t[-1], bins[0], bins[-1]],
            origin='lower',
            interpolation='antialiased',
        )

        ax.set_xlim([0.0, max_freq])


class TableHelper:
    """Helper class for creating tables in plots"""

    @staticmethod
    def create_table(
        ax: matplotlib.axes.Axes,
        data: List[List[str]],
        columns: List[str],
        bbox: List[float],
        fontsize: int = 10,
        column_widths: Optional[List[int]] = None,
    ) -> matplotlib.table.Table:
        """Create a formatted table on the axes"""
        table = ax.table(cellText=data, colLabels=columns, bbox=bbox, loc='upper right', cellLoc='center')

        table.auto_set_font_size(False)
        table.set_fontsize(fontsize)

        if column_widths:
            table.auto_set_column_width(column_widths)
        else:
            table.auto_set_column_width(list(range(len(columns))))

        table.set_zorder(100)

        # Style the table
        bold_font = matplotlib.font_manager.FontProperties(weight='bold')
        for key, cell in table.get_celld().items():
            row, col = key
            cell.set_text_props(ha='center', va='center')

            if row == 0:  # Header row
                cell.get_text().set_fontproperties(bold_font)
                cell.get_text().set_color(PlottingConstants.KLIPPAIN_COLORS['dark_orange'])
            elif col == 0:  # First column
                cell.get_text().set_fontproperties(bold_font)
                cell.get_text().set_color(PlottingConstants.KLIPPAIN_COLORS['dark_purple'])

        return table


class PeakAnnotator:
    """Helper class for annotating peaks on plots"""

    @staticmethod
    def annotate_peak(
        ax: matplotlib.axes.Axes,
        x: float,
        y: float,
        label: str,
        color: str = 'black',
        fontsize: int = 13,
        weight: str = 'normal',
        offset: Tuple[int, int] = (8, 5),
    ) -> None:
        """Annotate a peak on the plot"""
        ax.annotate(
            label,
            (x, y),
            textcoords='offset points',
            xytext=offset,
            ha='left',
            fontsize=fontsize,
            color=color,
            weight=weight,
        )

    @staticmethod
    def mark_peaks(
        ax: matplotlib.axes.Axes,
        x_values: np.ndarray,
        y_values: np.ndarray,
        marker: str = 'x',
        color: str = 'black',
        markersize: int = 8,
    ) -> None:
        """Mark peaks with markers"""
        ax.plot(x_values, y_values, marker, color=color, markersize=markersize)
