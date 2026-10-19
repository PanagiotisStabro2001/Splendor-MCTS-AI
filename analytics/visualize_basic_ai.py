"""
Visualize Basic AI accuracy analysis.
Run this after a game to see detailed move-by-move accuracy.
"""

import json
import sys
from pathlib import Path


def analyze_basic_ai(json_file: str):
    """
    Display Basic AI accuracy analysis from saved game data.
    
    Args:
        json_file: Path to accuracy JSON file
    """
    # Load data
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print("="*70)
    print("BASIC AI ACCURACY ANALYSIS")
    print("="*70)
    print(f"\nGame ID: {data['game_id']}")
    print(f"Player Analyzed: Player {data['basic_player_id'] + 1} (Basic AI)")
    print("\n" + "="*70)
    
    # Overall stats
    print("\n📊 OVERALL STATISTICS")
    print("-"*70)
    print(f"  Total Moves Analyzed:     {data.get('total_moves_analyzed', 0)}")
    print(f"  Accuracy:                 {data['accuracy_percent']:.1f}%")
    print(f"  Total Point Loss:         {data['total_point_loss']:.2f}")
    print(f"  Avg Point Loss per Move:  {data['average_point_loss']:.2f}")
    print("-"*70)
    
    # Move-by-move breakdown
    comparisons = data.get('detailed_comparisons', [])
    
    if comparisons:
        print("\n📋 MOVE-BY-MOVE BREAKDOWN")
        print("-"*70)
        print(f"{'Turn':<6} {'Basic AI Action':<35} {'Match':<10}")
        print("-"*70)
        
        for comp in comparisons:
            turn = comp['turn']
            action = comp['basic_action'][:32] + '...' if len(comp['basic_action']) > 32 else comp['basic_action']
            match = "[OK] YES" if comp['match'] else "✗ NO"
            
            print(f"{turn:<6} {action:<35} {match:<10}")
        
        print("-"*70)
    
    print("\n" + "="*70)
    print("Analysis Complete!")
    print("="*70)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # File specified via command line
        analyze_basic_ai(sys.argv[1])
    else:
        # Find most recent accuracy file
        data_dir = Path(__file__).parent.parent / "data"
        json_files = list(data_dir.glob("accuracy_*.json"))
        
        if json_files:
            latest = max(json_files, key=lambda p: p.stat().st_mtime)
            print(f"Loading most recent file: {latest.name}\n")
            analyze_basic_ai(str(latest))
        else:
            print("No accuracy files found in data/ folder.")
            print("\nUsage: python analytics/visualize_basic_ai.py [path/to/accuracy.json]")
