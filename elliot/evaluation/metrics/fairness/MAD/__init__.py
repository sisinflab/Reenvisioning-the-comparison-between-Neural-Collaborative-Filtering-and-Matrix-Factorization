"""
This is the Precision metric module.

This module contains and expose the recommendation metric.
"""

__version__ = '0.1'
__author__ = 'Vito Walter Anelli, Claudio Pomo'
__email__ = 'vitowalter.anelli@poliba.it, claudio.pomo@poliba.it'

from .UserMADrating import UserMADrating
from .ItemMADrating import ItemMADrating
from .UserMADranking import UserMADranking
from .ItemMADranking import ItemMADranking