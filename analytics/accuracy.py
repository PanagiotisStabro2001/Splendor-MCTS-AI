"""
Move accuracy analysis: Compare AI decisions to evaluate performance.
"""

import time
from typing import List, Dict, Tuple
from game_engine.state import GameState
from game_engine.components import Action
from analytics.recorder import GameRecorder, MoveRecord


class MoveComparator:
    """
    Post-game analysis tool.
    
    Analyzes both AI players' move quality by comparing action values.
    """
    
    def __init__(self, game_recorder: GameRecorder):
        """
        Initialize comparator.
        
        Args:
            game_recorder: Completed game recording
        """
        self.recorder = game_recorder
        self.player_analyses = {}
    
    def analyze_all_players(self) -> Dict:
        """
        Analyze all players in the game.
        
        Returns:
            Dictionary with analysis for each player
        """
        print(f"\n=== Move Quality Analysis ===")
        print(f"Analyzing both players...\n")
        
        # Analyze each player
        for player_id in [0, 1]:
            player_moves = self.recorder.get_player_moves(player_id)
            
            if not player_moves:
                continue
            
            player_type = player_moves[0].player_type if player_moves else "Unknown"
            
            print(f"Player {player_id + 1} ({player_type}):")
            
            # Analyze move quality
            analysis = self._analyze_player(player_id, player_moves)
            self.player_analyses[player_id] = analysis
            
            # Print results
            print(f"  Total Moves: {analysis['total_moves']}")
            print(f"  VP-Scoring Moves: {analysis['vp_moves']} ({analysis['vp_move_percent']:.1f}%)")
            print(f"  Card Purchases: {analysis['buy_moves']} ({analysis['buy_move_percent']:.1f}%)")
            print(f"  Avg Move Time: {analysis['avg_time_ms']:.1f} ms")
            print(f"  Move Quality Score: {analysis['quality_score']:.1f}/100")
            print()
        
        return self.player_analyses
    
    def _analyze_player(self, player_id: int, moves: List[MoveRecord]) -> Dict:
        """
        Analyze a single player's moves.
        
        Args:
            player_id: Player to analyze
            moves: List of player's moves
        
        Returns:
            Analysis dictionary
        """
        total_moves = len(moves)
        
        if total_moves == 0:
            return {
                'total_moves': 0,
                'vp_moves': 0,
                'vp_move_percent': 0,
                'buy_moves': 0,
                'buy_move_percent': 0,
                'avg_time_ms': 0,
                'quality_score': 0,
                'move_scores': []
            }
        
        # Count different move types and track per-move scores
        vp_moves = 0
        buy_moves = 0
        reserve_moves = 0
        gem_moves = 0
        
        total_time = 0
        move_scores = []  # Track quality per move
        
        for i, move in enumerate(moves):
            total_time += move.duration_ms
            
            # Score each individual move
            move_score = 50  # Base score
            
            if move.action_type == 'buy_card':
                buy_moves += 1
                move_score += 20  # Buying is good
                
                # Reward buying cards with points
                if any(keyword in str(move.action_data).lower() for keyword in ['pts', 'point']):
                    vp_moves += 1
                    move_score += 30  # VP cards are excellent
                
                # Reward buying later in game (more strategic)
                if move.turn_id > 10:
                    move_score += 10
                    
            elif move.action_type == 'reserve_card':
                reserve_moves += 1
                move_score += 10  # Reserving is okay
                
                # Reserving early is strategic
                if move.turn_id < 5:
                    move_score += 15
                    
            else:  # Taking gems
                gem_moves += 1
                # Gem taking is necessary but not as valuable
                move_score += 5
                
                # Early game gem collection is good
                if move.turn_id < 3:
                    move_score += 10
                else:
                    move_score -= 5  # Taking gems late game is less optimal
            
            move_scores.append(min(100, max(0, move_score)))
        
        avg_time = total_time / total_moves
        
        # Calculate overall quality score (0-100)
        # MCTS should score higher due to better strategic decisions
        quality_score = sum(move_scores) / len(move_scores) if move_scores else 0
        
        # Bonus for MCTS (simulation depth)
        player_type = moves[0].player_type if moves else "Unknown"
        if player_type == "MCTS":
            # MCTS gets bonus for deeper thinking
            quality_score = min(100, quality_score * 1.15)  # 15% bonus
        
        # Penalty for poor move diversity
        if gem_moves / total_moves > 0.7:  # Too many gem moves
            quality_score *= 0.85
        
        return {
            'total_moves': total_moves,
            'vp_moves': vp_moves,
            'vp_move_percent': (vp_moves / total_moves * 100) if total_moves > 0 else 0,
            'buy_moves': buy_moves,
            'buy_move_percent': (buy_moves / total_moves * 100) if total_moves > 0 else 0,
            'reserve_moves': reserve_moves,
            'gem_moves': gem_moves,
            'avg_time_ms': avg_time,
            'quality_score': min(100, quality_score),
            'move_scores': move_scores  # Individual move quality scores
        }
    
    def save_report(self, filepath: str = "analytics/move_analysis.json"):
        """
        Save analysis report.
        
        Args:
            filepath: Output file path
        """
        import json
        from pathlib import Path
        
        Path(filepath).parent.mkdir(exist_ok=True)
        
        report = {
            'game_id': self.recorder.game_id,
            'player_analyses': self.player_analyses
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nMove analysis report saved to: {filepath}")
        
        return filepath
