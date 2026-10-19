"""
Move Accuracy Visualization - Strip Plot
Shows move quality classification for both players across all turns.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys


def load_game_log(json_path):
    """Load game_log from JSON file."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    game_log = data.get('game_log', [])
    if not game_log:
        raise ValueError("No game_log found in JSON file!")
    
    return game_log, data.get('metadata', {})


def plot_accuracy_strip_chart(game_log, output_path='data/move_accuracy_strip_plot.png'):
    """
    Create a "Move Quality Strip Plot" showing accuracy classification.
    
    X-Axis: Turn Number
    Y-Axis: Player (Player 1 vs Player 2)
    Visual: Colored dots for each move (Green=Best, Yellow=Inaccuracy, Orange=Mistake, Red=Blunder)
    """
    # Color mapping
    color_map = {
        'Best': '#27ae60',        # Green
        'Inaccuracy': '#f39c12',  # Yellow
        'Mistake': '#e67e22',     # Orange
        'Blunder': '#e74c3c'      # Red
    }
    
    # Separate data by player
    p1_data = [(t['turn_number'], t.get('move_classification', 'Unknown'), 
                t.get('accuracy_loss', 0)) 
               for t in game_log if t['active_player'] == 0]
    p2_data = [(t['turn_number'], t.get('move_classification', 'Unknown'), 
                t.get('accuracy_loss', 0)) 
               for t in game_log if t['active_player'] == 1]
    
    if not p1_data or not p2_data:
        print("⚠ Warning: Insufficient accuracy data")
        return
    
    # Create figure
    fig, ax = plt.subplots(figsize=(18, 11))
    fig.patch.set_facecolor('#f8f9fa')
    ax.set_facecolor('#ffffff')
    
    # Adjust for stats box below
    plt.subplots_adjust(bottom=0.23)
    
    # Plot Player 1 moves (y=1)
    for turn, classification, loss in p1_data:
        color = color_map.get(classification, '#95a5a6')  # Gray for unknown
        ax.scatter(turn, 1, s=200, c=color, edgecolors='#2c3e50', 
                  linewidth=2, alpha=0.9, zorder=3)
        
        # Add annotation for Blunders
        if classification == 'Blunder' and loss > 0:
            ax.annotate(f'-{loss*100:.0f}%', 
                       xy=(turn, 1), xytext=(0, 15),
                       textcoords='offset points', ha='center',
                       fontsize=9, fontweight='bold', color='#e74c3c',
                       bbox=dict(boxstyle='round,pad=0.3', 
                               facecolor='white', edgecolor='#e74c3c', 
                               linewidth=1.5, alpha=0.9))
    
    # Plot Player 2 moves (y=2)
    for turn, classification, loss in p2_data:
        color = color_map.get(classification, '#95a5a6')
        ax.scatter(turn, 2, s=200, c=color, edgecolors='#2c3e50', 
                  linewidth=2, alpha=0.9, zorder=3)
        
        # Add annotation for Blunders
        if classification == 'Blunder' and loss > 0:
            ax.annotate(f'-{loss*100:.0f}%', 
                       xy=(turn, 2), xytext=(0, 15),
                       textcoords='offset points', ha='center',
                       fontsize=9, fontweight='bold', color='#e74c3c',
                       bbox=dict(boxstyle='round,pad=0.3', 
                               facecolor='white', edgecolor='#e74c3c', 
                               linewidth=1.5, alpha=0.9))
    
    # Styling
    ax.set_xlabel('Turn Number', fontsize=16, fontweight='bold', color='#2c3e50')
    ax.set_ylabel('Player', fontsize=16, fontweight='bold', color='#2c3e50')
    ax.set_title('Move Quality Strip Plot\nAccuracy Classification by Turn (MCTS as Reference)', 
                 fontsize=20, fontweight='bold', color='#2c3e50', pad=20)
    
    # Y-axis configuration
    ax.set_yticks([1, 2])
    ax.set_yticklabels(['Player 1\n(Heuristic)', 'Player 2\n(MCTS)'], 
                       fontsize=13, fontweight='bold')
    ax.set_ylim(0.5, 2.5)
    
    # X-axis configuration
    max_turn = max(max(t[0] for t in p1_data), max(t[0] for t in p2_data))
    ax.set_xlim(0, max_turn + 1)
    ax.tick_params(axis='x', labelsize=12)
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=1, axis='x')
    ax.axhline(y=1.5, color='#95a5a6', linestyle='-', linewidth=1, alpha=0.3)
    ax.set_axisbelow(True)
    
    # Legend - create custom legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=color_map['Best'], edgecolor='#2c3e50', 
              linewidth=2, label='Best Move (Loss < 2%)'),
        Patch(facecolor=color_map['Inaccuracy'], edgecolor='#2c3e50', 
              linewidth=2, label='Inaccuracy (2-10%)'),
        Patch(facecolor=color_map['Mistake'], edgecolor='#2c3e50', 
              linewidth=2, label='Mistake (10-20%)'),
        Patch(facecolor=color_map['Blunder'], edgecolor='#2c3e50', 
              linewidth=2, label='Blunder (>20%)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=12, 
             framealpha=0.95, edgecolor='#2c3e50', fancybox=True, shadow=True)
    
    # Statistics box
    # Calculate stats for each player
    p1_classifications = [t[1] for t in p1_data]
    p2_classifications = [t[1] for t in p2_data]
    
    p1_best = p1_classifications.count('Best')
    p1_inaccuracy = p1_classifications.count('Inaccuracy')
    p1_mistake = p1_classifications.count('Mistake')
    p1_blunder = p1_classifications.count('Blunder')
    p1_total = len(p1_data)
    
    p2_best = p2_classifications.count('Best')
    p2_inaccuracy = p2_classifications.count('Inaccuracy')
    p2_mistake = p2_classifications.count('Mistake')
    p2_blunder = p2_classifications.count('Blunder')
    p2_total = len(p2_data)
    
    # Calculate accuracy score (weighted)
    def calc_accuracy_score(best, inaccuracy, mistake, blunder, total):
        if total == 0:
            return 0
        score = (best * 100 + inaccuracy * 90 + mistake * 70 + blunder * 40) / total
        return score
    
    p1_accuracy_score = calc_accuracy_score(p1_best, p1_inaccuracy, p1_mistake, p1_blunder, p1_total)
    p2_accuracy_score = calc_accuracy_score(p2_best, p2_inaccuracy, p2_mistake, p2_blunder, p2_total)
    
    # Average accuracy loss
    p1_avg_loss = np.mean([t[2] for t in p1_data if t[2] is not None])
    p2_avg_loss = np.mean([t[2] for t in p2_data if t[2] is not None])
    
    stats_text = (
        f"ACCURACY SUMMARY\n"
        f"{'─' * 40}\n"
        f"Player 1 (Heuristic):\n"
        f"  Best:       {p1_best}/{p1_total} ({p1_best/p1_total*100:.0f}%)\n"
        f"  Inaccuracy: {p1_inaccuracy}/{p1_total} ({p1_inaccuracy/p1_total*100:.0f}%)\n"
        f"  Mistake:    {p1_mistake}/{p1_total} ({p1_mistake/p1_total*100:.0f}%)\n"
        f"  Blunder:    {p1_blunder}/{p1_total} ({p1_blunder/p1_total*100:.0f}%)\n"
        f"  Avg Loss:   {p1_avg_loss*100:.1f}%\n"
        f"  Accuracy:   {p1_accuracy_score:.1f}/100\n"
        f"\n"
        f"Player 2 (MCTS):\n"
        f"  Best:       {p2_best}/{p2_total} ({p2_best/p2_total*100:.0f}%)\n"
        f"  Inaccuracy: {p2_inaccuracy}/{p2_total} ({p2_inaccuracy/p2_total*100:.0f}%)\n"
        f"  Mistake:    {p2_mistake}/{p2_total} ({p2_mistake/p2_total*100:.0f}%)\n"
        f"  Blunder:    {p2_blunder}/{p2_total} ({p2_blunder/p2_total*100:.0f}%)\n"
        f"  Avg Loss:   {p2_avg_loss*100:.1f}%\n"
        f"  Accuracy:   {p2_accuracy_score:.1f}/100\n"
        f"\n"
        f"Difference: {abs(p2_accuracy_score - p1_accuracy_score):.1f} pts"
    )
    
    # Place stats box below plot area
    fig.text(0.5, 0.10, stats_text,
            fontsize=10, verticalalignment='top', horizontalalignment='center',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='#ecf0f1', 
                     edgecolor='#2c3e50', linewidth=2, alpha=0.95),
            family='monospace', color='#2c3e50')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='#f8f9fa')
    plt.close()
    
    print(f"[OK] Move Accuracy Strip Plot saved: {output_path}")
    return output_path


def generate_accuracy_visualization(json_path):
    """Generate move accuracy visualization."""
    print("\n" + "=" * 70)
    print("MOVE ACCURACY VISUALIZATION")
    print("=" * 70 + "\n")
    
    # Load data
    print(f"Loading game data: {json_path}")
    try:
        game_log, metadata = load_game_log(json_path)
        print(f"[OK] Loaded {len(game_log)} turn entries")
        
        # Check if accuracy data exists
        has_accuracy = any(t.get('move_classification') is not None for t in game_log)
        if not has_accuracy:
            print("\n⚠ WARNING: No move accuracy data found in game log!")
            print("  Make sure you ran a game AFTER implementing the Accuracy Engine.")
            print("  Run: python main.py")
            return
        
        print()
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return
    
    # Ensure output directory exists
    Path('data').mkdir(exist_ok=True)
    
    # Generate visualization
    print("Generating move accuracy strip plot...\n")
    
    try:
        output = plot_accuracy_strip_chart(game_log)
        print("\n" + "=" * 70)
        print("VISUALIZATION COMPLETE!")
        print("=" * 70)
        print(f"\nOutput: {output}")
        print("\n" + "=" * 70 + "\n")
    except Exception as e:
        print(f"✗ Error generating visualization: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Find the most recent game log or use provided path
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        log_files = sorted(Path('logs').glob('game_*.json'), reverse=True)
        if log_files:
            json_path = str(log_files[0])
            print(f"Using most recent game log: {json_path}\n")
        else:
            print("✗ No game logs found!")
            print("\nUsage:")
            print("  python plot_move_accuracy.py [path/to/game_log.json]")
            print("\nOr run a game first:")
            print("  python main.py")
            sys.exit(1)
    
    generate_accuracy_visualization(json_path)
