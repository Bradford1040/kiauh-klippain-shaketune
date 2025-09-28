# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: axes_map_plotter.py
# Description: Plotter for axes map detection graphs

from datetime import datetime
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from ..base_models import PlotterStrategy
from ..computation_results import AxesMapResult
from ..plotting_utils import AxesConfiguration, PlottingConstants


class AxesMapPlotter(PlotterStrategy):
    """Plotter for axes map detection graphs"""

    def plot(self, result: AxesMapResult) -> Figure:
        """Create axes map detection graph"""
        data = result.get_plot_data()

        fig = plt.figure(figsize=(15, 7))
        gs = fig.add_gridspec(
            1, 2, width_ratios=[5, 3], bottom=0.080, top=0.840, left=0.055, right=0.960, hspace=0.166, wspace=0.060
        )
        ax_1 = fig.add_subplot(gs[0])
        ax_2 = fig.add_subplot(gs[1], projection='3d')

        # Add titles and logo
        self._add_titles(fig, data)
        self.add_logo(fig)
        self.add_version_text(fig, data['st_version'])

        # Plot acceleration data
        self._plot_acceleration_data(ax_1, data)

        # Plot 3D movement
        self._plot_3d_movement(ax_2, data)

        return fig

    def _add_titles(self, fig: Figure, data: Dict[str, Any]) -> None:
        """Add title lines to the figure"""
        try:
            filename = data['measurements'][0]['name']
            dt = datetime.strptime(f'{filename.split("_")[2]} {filename.split("_")[3]}', '%Y%m%d %H%M%S')
            title_line2 = dt.strftime('%x %X')
            if data['accel'] is not None:
                title_line2 += f' -- at {data["accel"]:0.0f} mm/s²'
        except Exception:
            title_line2 = data['measurements'][0]['name'] + ' ...'

        title_lines = [
            {
                'x': 0.060,
                'y': 0.947,
                'text': 'AXES MAP CALIBRATION TOOL',
                'fontsize': 20,
                'color': PlottingConstants.KLIPPAIN_COLORS['purple'],
                'weight': 'bold',
            },
            {'x': 0.060, 'y': 0.939, 'va': 'top', 'text': title_line2},
            {'x': 0.50, 'y': 0.985, 'va': 'top', 'text': f'| Detected axes_map: {data["formatted_direction_vector"]}'},
        ]
        self.add_title(fig, title_lines)

    def _plot_acceleration_data(self, ax, data: Dict[str, Any]) -> None:
        """Plot acceleration data on the first axes"""
        time_data = data['acceleration_data_0']
        accel_data = data['acceleration_data_1']

        for i, (time, (accel_x, accel_y, accel_z)) in enumerate(zip(time_data, accel_data)):
            ax.plot(
                time,
                accel_x,
                label='X' if i == 0 else '',
                color=PlottingConstants.KLIPPAIN_COLORS['purple'],
                linewidth=0.5,
                zorder=50 if i == 0 else 10,
            )
            ax.plot(
                time,
                accel_y,
                label='Y' if i == 0 else '',
                color=PlottingConstants.KLIPPAIN_COLORS['orange'],
                linewidth=0.5,
                zorder=50 if i == 1 else 10,
            )
            ax.plot(
                time,
                accel_z,
                label='Z' if i == 0 else '',
                color=PlottingConstants.KLIPPAIN_COLORS['red_pink'],
                linewidth=0.5,
                zorder=50 if i == 2 else 10,
            )

        # Add gravity and noise level to a secondary legend
        ax_2 = ax.twinx()
        ax_2.yaxis.set_visible(False)
        ax_2.plot([], [], ' ', label=data['average_noise_intensity_label'])
        ax_2.plot([], [], ' ', label=f'Measured gravity: {data["gravity"] / 1000:0.3f} m/s²')

        fontP = AxesConfiguration.configure_axes(
            ax,
            xlabel='Time (s)',
            ylabel='Acceleration (mm/s²)',
            title='Acceleration (gravity offset removed)',
            sci_axes='y',
            legend=True,
        )
        ax_2.legend(loc='upper right', prop=fontP)

    def _plot_3d_movement(self, ax, data: Dict[str, Any]) -> None:
        """Plot 3D movement on the second axes"""
        position_data = data['position_data']
        direction_vectors = data['direction_vectors']
        angle_errors = data['angle_errors']

        for i, ((position_x, position_y, position_z), average_direction_vector, angle_error) in enumerate(
            zip(position_data, direction_vectors, angle_errors)
        ):
            ax.plot(
                position_x,
                position_y,
                position_z,
                color=PlottingConstants.KLIPPAIN_COLORS['orange'],
                linestyle=':',
                linewidth=2,
            )
            ax.scatter(
                position_x[0],
                position_y[0],
                position_z[0],
                color=PlottingConstants.KLIPPAIN_COLORS['red_pink'],
                zorder=10,
            )
            ax.text(
                position_x[0] + 1,
                position_y[0],
                position_z[0],
                str(i + 1),
                color='black',
                fontsize=16,
                fontweight='bold',
                zorder=20,
            )

            # Plot average direction vector
            start_position = np.array([position_x[0], position_y[0], position_z[0]])
            end_position = start_position + average_direction_vector * np.linalg.norm(
                [position_x[-1] - position_x[0], position_y[-1] - position_y[0], position_z[-1] - position_z[0]]
            )
            ax.plot(
                [start_position[0], end_position[0]],
                [start_position[1], end_position[1]],
                [start_position[2], end_position[2]],
                label=f'{["X", "Y", "Z"][i]} angle: {angle_error:0.2f}°',
                color=PlottingConstants.KLIPPAIN_COLORS['purple'],
                linestyle='-',
                linewidth=2,
            )

        AxesConfiguration.configure_axes(
            ax,
            xlabel='X Position (mm)',
            ylabel='Y Position (mm)',
            zlabel='Z Position (mm)',
            title='Estimated movement in 3D space',
            legend=True,
        )
