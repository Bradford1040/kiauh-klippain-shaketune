# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: base_models.py
# Description: Base data models and interfaces for graph creators

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from matplotlib.figure import Figure

from ..helpers.accelerometer import Measurement


@dataclass
class GraphMetadata:
    """Metadata for graph generation"""

    title: str
    subtitle: Optional[str] = None
    version: str = 'unknown'
    timestamp: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComputationResult(ABC):
    """Base class for computation results"""

    metadata: GraphMetadata
    measurements: List[Measurement]

    @abstractmethod
    def get_plot_data(self) -> Dict[str, Any]:
        """Return data formatted for plotting"""
        pass


@runtime_checkable
class Plotter(Protocol):
    """Protocol for plotter implementations"""

    def plot(self, data: ComputationResult) -> Figure:
        """Create a plot from computation result"""
        ...


@runtime_checkable
class Computation(Protocol):
    """Protocol for computation implementations"""

    def compute(self) -> ComputationResult:
        """Perform computation and return results"""
        ...


class PlotterStrategy(ABC):
    """Base class for plotting strategies"""

    KLIPPAIN_COLORS = {
        'purple': '#70088C',
        'orange': '#FF8D32',
        'dark_purple': '#150140',
        'dark_orange': '#F24130',
        'red_pink': '#F2055C',
    }

    def __init__(self):
        self._logo_image = None
        self._load_logo()

    def _load_logo(self):
        """Load the logo image"""
        import os

        import matplotlib.pyplot as plt

        current_dir = os.path.dirname(__file__)
        image_path = os.path.join(current_dir, 'klippain.png')
        if os.path.exists(image_path):
            self._logo_image = plt.imread(image_path)

    @abstractmethod
    def plot(self, data: ComputationResult) -> Figure:
        """Create a plot from computation result"""
        pass

    def add_logo(self, fig: Figure, position: List[float] = None) -> None:
        """Add logo to the figure"""
        if position is None:
            position = [0.001, 0.894, 0.105, 0.105]
        if self._logo_image is not None:
            ax_logo = fig.add_axes(position, anchor='NW')
            ax_logo.imshow(self._logo_image)
            ax_logo.axis('off')

    def add_version_text(self, fig: Figure, version: str, position: tuple = (0.995, 0.980)) -> None:
        """Add version text to the figure"""
        if version != 'unknown':
            fig.text(
                position[0],
                position[1],
                version,
                ha='right',
                va='bottom',
                fontsize=8,
                color=self.KLIPPAIN_COLORS['purple'],
            )

    def add_title(self, fig: Figure, title_lines: List[Dict[str, Any]]) -> None:
        """Add title lines to the figure"""
        for line in title_lines:
            fig.text(
                line['x'],
                line['y'],
                line['text'],
                ha=line.get('ha', 'left'),
                va=line.get('va', 'bottom'),
                fontsize=line.get('fontsize', 16),
                color=line.get('color', self.KLIPPAIN_COLORS['dark_purple']),
                weight=line.get('weight', 'normal'),
            )
