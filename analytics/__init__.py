"""
Package initialization for analytics.
"""

from analytics.recorder import GameRecorder, MoveRecord
from analytics.accuracy import MoveComparator

__all__ = ['GameRecorder', 'MoveRecord', 'MoveComparator']
