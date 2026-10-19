"""
Example Dashboard Visualizations for Deep Dive Analytics
Use this script to create comparison graphs from game_log data.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def load_game_data(json_path):
    """Load game data from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def plot_win_probability_comparison(game_log, output_path='data/win_probability_comparison.png'):
    """
    Plot win probability over time for both players.
    This is the KEY metric - now fair for both agents thanks to MCTS Critic!
    """
    # Separate by player
    p1_data = [(t['turn_number'], t['win_probability']) 
               for t in game_log if t['active_player'] == 0 and t['win_probability'] is not None]
    p2_data = [(t['turn_number'], t['win_probability']) 
               for t in game_log if t['active_player'] == 1 and t['win_probability'] is not None]
    
    if not p1_data or not p2_data:
        print("No win probability data available")
        return
    
    p1_turns, p1_probs = zip(*p1_data)
    p2_turns, p2_probs = zip(*p2_data)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Plot both players
    ax.plot(p1_turns, p1_probs, 'o-', label='Player 1 (Heuristic)', 
            color='#3498db', linewidth=2, markersize=6, alpha=0.8)
    ax.plot(p2_turns, p2_probs, 's-', label='Player 2 (MCTS)', 
            color='#e74c3c', linewidth=2, markersize=6, alpha=0.8)
    
    # Add 50% line
    ax.axhline(y=0.5, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Even (50%)')
    
    # Styling
    ax.set_xlabel('Turn Number', fontsize=14, fontweight='bold')
    ax.set_ylabel('Win Probability', fontsize=14, fontweight='bold')
    ax.set_title('Win Probability Comparison (MCTS Evaluated)', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=12)
    ax.set_ylim(0, 1)
    
    # Add statistics
    p1_avg = np.mean(p1_probs)
    p2_avg = np.mean(p2_probs)
    stats_text = (
        f"Average Win Probability:\n"
        f"  Heuristic: {p1_avg:.2%}\n"
        f"  MCTS: {p2_avg:.2%}\n"
        f"  Difference: {abs(p2_avg - p1_avg):.2%}"
    )
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
           fontsize=11, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7),
           family='monospace')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] Win probability comparison saved: {output_path}")


def plot_card_acquisition_strategy(game_log, output_path='data/card_strategy_comparison.png'):
    """Plot card acquisition by tier over time."""
    # Get card data by player
    p1_data = [(t['turn_number'], t['cards_owned_by_tier']) 
               for t in game_log if t['active_player'] == 0]
    p2_data = [(t['turn_number'], t['cards_owned_by_tier']) 
               for t in game_log if t['active_player'] == 1]
    
    if not p1_data or not p2_data:
        print("No card data available")
        return
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Player 1
    p1_turns = [t[0] for t in p1_data]
    p1_tier1 = [t[1][0] for t in p1_data]
    p1_tier2 = [t[1][1] for t in p1_data]
    p1_tier3 = [t[1][2] for t in p1_data]
    
    ax1.stackplot(p1_turns, p1_tier1, p1_tier2, p1_tier3,
                 labels=['Tier 1', 'Tier 2', 'Tier 3'],
                 colors=['#95a5a6', '#3498db', '#9b59b6'], alpha=0.8)
    ax1.set_xlabel('Turn Number', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Card Count', fontsize=12, fontweight='bold')
    ax1.set_title('Player 1 (Heuristic) - Card Strategy', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    # Player 2
    p2_turns = [t[0] for t in p2_data]
    p2_tier1 = [t[1][0] for t in p2_data]
    p2_tier2 = [t[1][1] for t in p2_data]
    p2_tier3 = [t[1][2] for t in p2_data]
    
    ax2.stackplot(p2_turns, p2_tier1, p2_tier2, p2_tier3,
                 labels=['Tier 1', 'Tier 2', 'Tier 3'],
                 colors=['#95a5a6', '#e74c3c', '#e67e22'], alpha=0.8)
    ax2.set_xlabel('Turn Number', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Card Count', fontsize=12, fontweight='bold')
    ax2.set_title('Player 2 (MCTS) - Card Strategy', fontsize=14, fontweight='bold')
    ax2.legend(loc='upper left', fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] Card strategy comparison saved: {output_path}")


def plot_mcts_confidence(game_log, output_path='data/mcts_confidence.png'):
    """Plot MCTS decision confidence over time."""
    # Get MCTS turns with visit distribution
    mcts_data = [(t['turn_number'], t['visit_distribution']) 
                 for t in game_log 
                 if t['player_type'] == 'MCTS' and t['visit_distribution']]
    
    if not mcts_data:
        print("No MCTS visit distribution data available")
        return
    
    # Calculate confidence (percentage of visits on top move)
    turns = []
    confidences = []
    
    for turn_num, visit_dist in mcts_data:
        if len(visit_dist) >= 2:
            total_visits = sum(m['visits'] for m in visit_dist)
            top_visits = visit_dist[0]['visits']
            confidence = (top_visits / total_visits) * 100
            turns.append(turn_num)
            confidences.append(confidence)
    
    if not turns:
        print("Insufficient visit distribution data")
        return
    
    # Create plot
    fig, ax = plt.subplots(figsize=(14, 7))
    
    ax.plot(turns, confidences, 'o-', color='#e74c3c', 
            linewidth=2, markersize=8, alpha=0.8)
    ax.axhline(y=50, color='orange', linestyle='--', 
              linewidth=2, alpha=0.7, label='Low Confidence (50%)')
    ax.axhline(y=70, color='green', linestyle='--', 
              linewidth=2, alpha=0.7, label='High Confidence (70%)')
    
    ax.set_xlabel('Turn Number', fontsize=14, fontweight='bold')
    ax.set_ylabel('Confidence (%)', fontsize=14, fontweight='bold')
    ax.set_title('MCTS Decision Confidence (Top Move Visit %)', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=12)
    ax.set_ylim(0, 100)
    
    # Add statistics
    avg_confidence = np.mean(confidences)
    stats_text = (
        f"Average Confidence: {avg_confidence:.1f}%\n"
        f"Min: {min(confidences):.1f}%\n"
        f"Max: {max(confidences):.1f}%"
    )
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
           fontsize=11, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7),
           family='monospace')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] MCTS confidence plot saved: {output_path}")


def plot_performance_metrics(game_log, output_path='data/performance_comparison.png'):
    """Plot simulation count and decision time comparison."""
    p1_data = [(t['turn_number'], t['simulation_count'], t['duration_ms']) 
               for t in game_log if t['active_player'] == 0]
    p2_data = [(t['turn_number'], t['simulation_count'], t['duration_ms']) 
               for t in game_log if t['active_player'] == 1]
    
    if not p1_data or not p2_data:
        print("No performance data available")
        return
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Simulation counts
    p1_turns = [t[0] for t in p1_data]
    p1_sims = [t[1] for t in p1_data]
    p2_turns = [t[0] for t in p2_data]
    p2_sims = [t[1] for t in p2_data]
    
    ax1.plot(p1_turns, p1_sims, 'o-', label='Player 1 (Heuristic + Critic)', 
            color='#3498db', linewidth=2, markersize=6, alpha=0.8)
    ax1.plot(p2_turns, p2_sims, 's-', label='Player 2 (MCTS Full)', 
            color='#e74c3c', linewidth=2, markersize=6, alpha=0.8)
    ax1.set_xlabel('Turn Number', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Simulation Count', fontsize=12, fontweight='bold')
    ax1.set_title('MCTS Simulations per Turn', fontsize=14, fontweight='bold')
    ax1.legend(loc='best', fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    # Decision times
    p1_times = [t[2] for t in p1_data]
    p2_times = [t[2] for t in p2_data]
    
    ax2.plot(p1_turns, p1_times, 'o-', label='Player 1 (Heuristic)', 
            color='#3498db', linewidth=2, markersize=6, alpha=0.8)
    ax2.plot(p2_turns, p2_times, 's-', label='Player 2 (MCTS)', 
            color='#e74c3c', linewidth=2, markersize=6, alpha=0.8)
    ax2.set_xlabel('Turn Number', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Decision Time (ms)', fontsize=12, fontweight='bold')
    ax2.set_title('Decision Time per Turn', fontsize=14, fontweight='bold')
    ax2.legend(loc='best', fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[OK] Performance comparison saved: {output_path}")


def generate_all_dashboards(json_path):
    """Generate all dashboard visualizations from a game log."""
    print("\n" + "=" * 60)
    print("DEEP DIVE ANALYTICS - DASHBOARD GENERATOR")
    print("=" * 60 + "\n")
    
    # Load data
    print(f"Loading game data from: {json_path}")
    data = load_game_data(json_path)
    game_log = data.get('game_log', [])
    
    if not game_log:
        print("✗ No game_log found in JSON file!")
        print("  Make sure you're using a game played after implementing Deep Dive Analytics.")
        return
    
    print(f"[OK] Loaded {len(game_log)} turn entries\n")
    
    # Generate all plots
    print("Generating visualizations...\n")
    plot_win_probability_comparison(game_log)
    plot_card_acquisition_strategy(game_log)
    plot_mcts_confidence(game_log)
    plot_performance_metrics(game_log)
    
    print("\n" + "=" * 60)
    print("ALL DASHBOARDS GENERATED!")
    print("=" * 60)
    print("\nCheck the 'data/' folder for output images:")
    print("  - win_probability_comparison.png")
    print("  - card_strategy_comparison.png")
    print("  - mcts_confidence.png")
    print("  - performance_comparison.png")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    import sys
    
    # Find the most recent game log
    log_files = sorted(Path('logs').glob('game_*.json'), reverse=True)
    
    if len(sys.argv) > 1:
        # Use specified file
        json_path = sys.argv[1]
    elif log_files:
        # Use most recent
        json_path = str(log_files[0])
        print(f"Using most recent game log: {json_path}")
    else:
        print("No game logs found!")
        print("\nUsage:")
        print("  python visualize_dashboard.py [path/to/game_log.json]")
        print("\nOr run a game first:")
        print("  python main.py")
        sys.exit(1)
    
    generate_all_dashboards(json_path)
