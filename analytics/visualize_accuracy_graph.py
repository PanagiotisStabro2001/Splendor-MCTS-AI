"""
Visualize move accuracy with graphs for both AI players.
Creates a visual comparison chart.
"""

import json
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def visualize_accuracy(json_file: str):
    """
    Display move-by-move accuracy graph for both players.
    
    Args:
        json_file: Path to analysis JSON file
    """
    # Load data
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    player_analyses = data.get('player_analyses', {})
    
    if not player_analyses:
        print("No player analysis data found.")
        return
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('AI Player Move Quality Analysis', fontsize=16, fontweight='bold')
    
    # Colors
    colors = ['#3498db', '#e74c3c']  # Blue for P1, Red for P2
    
    # Plot 1: Move-by-move quality scores
    max_moves = 0
    for player_id_str, analysis in player_analyses.items():
        player_id = int(player_id_str)
        move_scores = analysis.get('move_scores', [])
        
        if move_scores:
            max_moves = max(max_moves, len(move_scores))
            moves = list(range(1, len(move_scores) + 1))
            
            ax1.plot(moves, move_scores, 
                    color=colors[player_id], 
                    linewidth=2, 
                    marker='o', 
                    markersize=4,
                    label=f'Player {player_id + 1}',
                    alpha=0.7)
    
    ax1.set_xlabel('Move Number', fontsize=12)
    ax1.set_ylabel('Move Quality Score (0-100)', fontsize=12)
    ax1.set_title('Move-by-Move Quality Comparison', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='best', fontsize=11)
    ax1.set_ylim(0, 110)
    
    # Add average line for each player
    for player_id_str, analysis in player_analyses.items():
        player_id = int(player_id_str)
        move_scores = analysis.get('move_scores', [])
        
        if move_scores:
            avg_score = sum(move_scores) / len(move_scores)
            ax1.axhline(y=avg_score, color=colors[player_id], 
                       linestyle='--', alpha=0.5, linewidth=1.5)
    
    # Plot 2: Overall comparison bars
    player_names = []
    quality_scores = []
    vp_percentages = []
    buy_percentages = []
    
    for player_id_str, analysis in player_analyses.items():
        player_id = int(player_id_str)
        player_names.append(f'Player {player_id + 1}')
        quality_scores.append(analysis.get('quality_score', 0))
        vp_percentages.append(analysis.get('vp_move_percent', 0))
        buy_percentages.append(analysis.get('buy_move_percent', 0))
    
    x_pos = range(len(player_names))
    bar_width = 0.25
    
    bars1 = ax2.bar([p - bar_width for p in x_pos], quality_scores, 
                    bar_width, label='Overall Quality', color='#2ecc71', alpha=0.8)
    bars2 = ax2.bar(x_pos, vp_percentages, 
                    bar_width, label='VP Moves %', color='#f39c12', alpha=0.8)
    bars3 = ax2.bar([p + bar_width for p in x_pos], buy_percentages, 
                    bar_width, label='Buy Moves %', color='#9b59b6', alpha=0.8)
    
    ax2.set_xlabel('Player', fontsize=12)
    ax2.set_ylabel('Score / Percentage', fontsize=12)
    ax2.set_title('Overall Performance Metrics', fontsize=14, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(player_names)
    ax2.legend(loc='best', fontsize=11)
    ax2.grid(True, axis='y', alpha=0.3)
    ax2.set_ylim(0, 110)
    
    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=9)
    
    # Add summary text box
    summary_text = "TOTAL ACCURACY SCORES\n" + "="*30 + "\n"
    
    for player_id_str, analysis in player_analyses.items():
        player_id = int(player_id_str)
        quality = analysis.get('quality_score', 0)
        total_moves = analysis.get('total_moves', 0)
        vp_pct = analysis.get('vp_move_percent', 0)
        
        summary_text += f"\nPlayer {player_id + 1}:\n"
        summary_text += f"  Quality Score: {quality:.1f}/100\n"
        summary_text += f"  Total Moves: {total_moves}\n"
        summary_text += f"  VP Moves: {vp_pct:.1f}%\n"
    
    # Add text box to figure
    fig.text(0.02, 0.02, summary_text, 
            fontsize=10, 
            family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout(rect=[0, 0.12, 1, 0.96])
    
    # Save figure
    output_path = Path(json_file).parent / f"accuracy_graph_{Path(json_file).stem}.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n[OK] Graph saved to: {output_path}")
    
    # Show plot
    plt.show()
    
    # Print summary to console
    print("\n" + "="*60)
    print("TOTAL ACCURACY SUMMARY")
    print("="*60)
    
    for player_id_str, analysis in player_analyses.items():
        player_id = int(player_id_str)
        print(f"\nPlayer {player_id + 1}:")
        print(f"  Overall Quality Score: {analysis.get('quality_score', 0):.1f}/100")
        print(f"  Total Moves: {analysis.get('total_moves', 0)}")
        print(f"  VP-Scoring Moves: {analysis.get('vp_move_percent', 0):.1f}%")
        print(f"  Card Purchases: {analysis.get('buy_move_percent', 0):.1f}%")
        print(f"  Avg Move Time: {analysis.get('avg_time_ms', 0):.1f} ms")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    try:
        import matplotlib
        matplotlib.use('TkAgg')  # Use interactive backend
    except:
        pass
    
    if len(sys.argv) > 1:
        # File specified via command line
        visualize_accuracy(sys.argv[1])
    else:
        # Find most recent analysis file
        data_dir = Path(__file__).parent.parent / "data"
        json_files = list(data_dir.glob("analysis_*.json"))
        
        if json_files:
            latest = max(json_files, key=lambda p: p.stat().st_mtime)
            print(f"Loading most recent file: {latest.name}\n")
            visualize_accuracy(str(latest))
        else:
            print("No analysis files found in data/ folder.")
            print("\nUsage: python analytics/visualize_accuracy_graph.py [path/to/analysis.json]")
