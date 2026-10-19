"""
Game move recorder for analytics.
"""

import json
import csv
import time
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from game_engine.components import Action


class MoveRecord:
    """Represents a single move record."""
    
    def __init__(self, turn_id: int, player_id: int, player_type: str,
                 action: Action, state_hash: str, duration_ms: float):
        self.turn_id = turn_id
        self.player_id = player_id
        self.player_type = player_type  # "Basic" or "MCTS"
        self.action = action
        self.action_type = action.type
        self.action_data = action.data
        self.state_hash = state_hash
        self.duration_ms = duration_ms
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'turn_id': self.turn_id,
            'player_id': self.player_id,
            'player_type': self.player_type,
            'action_type': self.action_type,
            'action_data': str(self.action_data),
            'state_hash': self.state_hash,
            'duration_ms': self.duration_ms,
            'timestamp': self.timestamp
        }


class GameRecorder:
    """
    Records all moves in a game for post-game analysis.
    
    Saves to both JSON and CSV formats.
    """
    
    def __init__(self, game_id: str = None):
        """
        Initialize recorder.
        
        Args:
            game_id: Unique identifier for this game
        """
        self.game_id = game_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.moves: List[MoveRecord] = []
        self.game_log: List[Dict[str, Any]] = []  # Deep dive analytics
        self.game_start_time = time.time()
        self.game_metadata = {
            'game_id': self.game_id,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'winner': None,
            'total_turns': 0,
            'final_scores': {}
        }
    
    def record_move(self, turn_id: int, player_id: int, player_type: str,
                   action: Action, state_hash: str, duration_ms: float):
        """
        Record a move.
        
        Args:
            turn_id: Turn number
            player_id: Player who made the move
            player_type: Type of player ("Basic" or "MCTS")
            action: The action taken
            state_hash: Hash of game state (for uniqueness)
            duration_ms: Time taken to compute move
        """
        record = MoveRecord(turn_id, player_id, player_type, action, 
                           state_hash, duration_ms)
        self.moves.append(record)
    
    def finalize_game(self, winner: int, final_scores: Dict[int, int]):
        """
        Finalize game recording.
        
        Args:
            winner: Winning player ID
            final_scores: Dictionary of player scores
        """
        self.game_metadata['end_time'] = datetime.now().isoformat()
        self.game_metadata['winner'] = winner
        self.game_metadata['total_turns'] = len(self.moves)
        self.game_metadata['final_scores'] = final_scores
        self.game_metadata['total_duration_seconds'] = time.time() - self.game_start_time
    
    def save_json(self, directory: str = "logs"):
        """
        Save game log as JSON.
        
        Args:
            directory: Output directory
        """
        Path(directory).mkdir(exist_ok=True)
        
        filepath = Path(directory) / f"game_{self.game_id}.json"
        
        data = {
            'metadata': self.game_metadata,
            'moves': [move.to_dict() for move in self.moves],
            'game_log': self.game_log  # Include deep dive analytics
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath
    
    def save_csv(self, directory: str = "logs"):
        """
        Save game log as CSV.
        
        Args:
            directory: Output directory
        """
        Path(directory).mkdir(exist_ok=True)
        
        filepath = Path(directory) / f"game_{self.game_id}.csv"
        
        with open(filepath, 'w', newline='') as f:
            fieldnames = ['turn_id', 'player_id', 'player_type', 'action_type',
                         'action_data', 'state_hash', 'duration_ms', 'timestamp']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for move in self.moves:
                writer.writerow(move.to_dict())
        
        return filepath
    
    def get_player_moves(self, player_id: int) -> List[MoveRecord]:
        """Get all moves for a specific player."""
        return [move for move in self.moves if move.player_id == player_id]
    
    def get_average_move_time(self, player_id: int) -> float:
        """Get average move computation time for a player."""
        player_moves = self.get_player_moves(player_id)
        if not player_moves:
            return 0.0
        return sum(m.duration_ms for m in player_moves) / len(player_moves)
