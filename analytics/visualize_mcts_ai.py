"""
Visualize MCTS AI performance analysis.
Run this after a game to see detailed move statistics.
"""

import json
import sys
from pathlib import Path


def analyze_mcts_ai(json_file: str):
    """
    Display MCTS AI performance analysis from saved game data.
    
    Args:
        json_file: Path to game log JSON file
    """
    # Load data
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    metadata = data['metadata']
    moves = data['moves']
    
    print("="*70)
    print("MCTS AI PERFORMANCE ANALYSIS")
    print("="*70)
    print(f"\nGame ID: {metadata['game_id']}")
    print(f"Winner: Player {metadata['winner'] + 1}")
    print(f"Total Turns: {metadata['total_turns']}")
    print(f"Game Duration: {metadata.get('total_duration_seconds', 0):.1f} seconds")
    print("\n" + "="*70)
    
    # Separate moves by player
    mcts_moves = [m for m in moves if m['player_type'] == 'MCTS']
    basic_moves = [m for m in moves if m['player_type'] == 'Basic']
    
    # MCTS Statistics
    if mcts_moves:
        print("\n🤖 MCTS AI STATISTICS")
        print("-"*70)
        print(f"  Total Moves:              {len(mcts_moves)}")
        
        total_time = sum(m['duration_ms'] for m in mcts_moves)
        avg_time = total_time / len(mcts_moves) if mcts_moves else 0
        
        print(f"  Avg Computation Time:     {avg_time:.0f} ms")
        print(f"  Total Thinking Time:      {total_time/1000:.1f} seconds")
        
        # Action type breakdown
        action_types = {}
        for move in mcts_moves:
            action_type = move['action_type']
            action_types[action_type] = action_types.get(action_type, 0) + 1
        
        print(f"\n  Action Breakdown:")
        for action, count in sorted(action_types.items()):
            pct = (count / len(mcts_moves) * 100)
            print(f"    - {action:<20} {count:>3} moves ({pct:>5.1f}%)")
        
        print("-"*70)
    
    # Basic AI Statistics (for comparison)
    if basic_moves:
        print("\n🎯 BASIC AI STATISTICS (Comparison)")
        print("-"*70)
        print(f"  Total Moves:              {len(basic_moves)}")
        
        total_time = sum(m['duration_ms'] for m in basic_moves)
        avg_time = total_time / len(basic_moves) if basic_moves else 0
        
        print(f"  Avg Computation Time:     {avg_time:.1f} ms")
        print(f"  Total Thinking Time:      {total_time/1000:.2f} seconds")
        
        # Action type breakdown
        action_types = {}
        for move in basic_moves:
            action_type = move['action_type']
            action_types[action_type] = action_types.get(action_type, 0) + 1
        
        print(f"\n  Action Breakdown:")
        for action, count in sorted(action_types.items()):
            pct = (count / len(basic_moves) * 100)
            print(f"    - {action:<20} {count:>3} moves ({pct:>5.1f}%)")
        
        print("-"*70)
    
    # Move-by-move timeline
    print("\n📋 MOVE TIMELINE")
    print("-"*70)
    print(f"{'Turn':<6} {'Player':<10} {'Action':<25} {'Time (ms)':<12}")
    print("-"*70)
    
    for move in moves[:20]:  # Show first 20 moves
        turn = move['turn_id']
        player = f"P{move['player_id'] + 1} ({move['player_type']})"
        action = move['action_type'][:22] + '...' if len(move['action_type']) > 22 else move['action_type']
        time_ms = f"{move['duration_ms']:.0f}"
        
        print(f"{turn:<6} {player:<10} {action:<25} {time_ms:<12}")
    
    if len(moves) > 20:
        print(f"  ... ({len(moves) - 20} more moves)")
    
    print("-"*70)
    
    # Final scores
    print("\n🏆 FINAL SCORES")
    print("-"*70)
    for player_id, score in metadata['final_scores'].items():
        player_num = int(player_id) + 1
        winner_mark = " 👑 WINNER" if int(player_id) == metadata['winner'] else ""
        print(f"  Player {player_num}: {score} points{winner_mark}")
    print("-"*70)
    
    print("\n" + "="*70)
    print("Analysis Complete!")
    print("="*70)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # File specified via command line
        analyze_mcts_ai(sys.argv[1])
    else:
        # Find most recent game log file
        logs_dir = Path(__file__).parent.parent / "logs"
        json_files = list(logs_dir.glob("game_*.json"))
        
        if json_files:
            latest = max(json_files, key=lambda p: p.stat().st_mtime)
            print(f"Loading most recent file: {latest.name}\n")
            analyze_mcts_ai(str(latest))
        else:
            print("No game log files found in logs/ folder.")
            print("\nUsage: python analytics/visualize_mcts_ai.py [path/to/game.json]")
