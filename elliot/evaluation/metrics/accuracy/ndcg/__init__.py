"""
This is the nDCG metric module.

This module contains and expose the recommendation metric.
"""

__version__ = '0.1'
__author__ = 'Vito Walter Anelli, Claudio Pomo'
__email__ = 'vitowalter.anelli@poliba.it, claudio.pomo@poliba.it'

from .ndcg import NDCG
from .ndcg_rendle2020 import NDCGRendle2020
