"""
Deep Dive Analytics - Comparison Visualizations
Generates 3 key comparison charts from game_log data.
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


def visual_1_battle_of_confidence(game_log, output_path='data/visual_1_battle_of_confidence.png'):
    """
    Visual 1: The "Battle of Confidence" (Line Chart)
    
    Shows win probability over time for both agents.
    MCTS confidence should rise steadily while Heuristic fluctuates.
    """
    # Separate data by player
    p1_data = [(t['turn_number'], t['win_probability']) 
               for t in game_log 
               if t['active_player'] == 0 and t['win_probability'] is not None]
    p2_data = [(t['turn_number'], t['win_probability']) 
               for t in game_log 
               if t['active_player'] == 1 and t['win_probability'] is not None]
    
    if not p1_data or not p2_data:
        print("⚠ Warning: Insufficient win probability data for Visual 1")
        return
    
    p1_turns, p1_probs = zip(*p1_data)
    p2_turns, p2_probs = zip(*p2_data)
    
    # Create figure with dramatic styling
    fig, ax = plt.subplots(figsize=(18, 11))
    fig.patch.set_facecolor('#f8f9fa')
    ax.set_facecolor('#ffffff')
    
    # Adjust subplot to make room for stats box below
    plt.subplots_adjust(bottom=0.20)
    
    # Plot both lines with strong visual distinction
    ax.plot(p1_turns, p1_probs, 
            color='#e74c3c', linewidth=3, marker='o', markersize=8, 
            label='Heuristic Agent (P1)', alpha=0.9, markeredgecolor='white', markeredgewidth=2)
    ax.plot(p2_turns, p2_probs, 
            color='#3498db', linewidth=3, marker='s', markersize=8, 
            label='MCTS Agent (P2)', alpha=0.9, markeredgecolor='white', markeredgewidth=2)
    
    # Add 50% reference line
    ax.axhline(y=0.5, color='#95a5a6', linestyle='--', linewidth=2, 
               alpha=0.6, label='Even Odds (50%)', zorder=0)
    
    # Fill area between lines to show dominance
    ax.fill_between(range(1, max(max(p1_turns), max(p2_turns)) + 1), 0.5, 1.0, 
                     alpha=0.1, color='#3498db', label='MCTS Advantage Zone')
    ax.fill_between(range(1, max(max(p1_turns), max(p2_turns)) + 1), 0.0, 0.5, 
                     alpha=0.1, color='#e74c3c', label='Heuristic Advantage Zone')
    
    # Styling
    ax.set_xlabel('Turn Number', fontsize=16, fontweight='bold', color='#2c3e50')
    ax.set_ylabel('Win Probability', fontsize=16, fontweight='bold', color='#2c3e50')
    ax.set_title('Visual 1: The "Battle of Confidence"\nWin Probability Evolution Over Time', 
                 fontsize=20, fontweight='bold', color='#2c3e50', pad=20)
    
    # Format y-axis as percentage
    ax.set_ylim(-0.05, 1.05)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'], fontsize=12)
    ax.tick_params(axis='x', labelsize=12)
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=1)
    ax.set_axisbelow(True)
    
    # Legend
    ax.legend(loc='best', fontsize=13, framealpha=0.95, edgecolor='#2c3e50', 
              fancybox=True, shadow=True)
    
    # Statistics box
    p1_avg = np.mean(p1_probs)
    p2_avg = np.mean(p2_probs)
    p1_final = p1_probs[-1]
    p2_final = p2_probs[-1]
    
    stats_text = (
        f"PERFORMANCE SUMMARY\n"
        f"{'─' * 35}\n"
        f"Heuristic Agent:\n"
        f"  Average:  {p1_avg:.1%}\n"
        f"  Final:    {p1_final:.1%}\n"
        f"\n"
        f"MCTS Agent:\n"
        f"  Average:  {p2_avg:.1%}\n"
        f"  Final:    {p2_final:.1%}\n"
        f"\n"
        f"Advantage: {abs(p2_avg - p1_avg):.1%} (MCTS)"
    )
    
    # Place stats box below plot area
    fig.text(0.5, 0.08, stats_text,
            fontsize=11, verticalalignment='top', horizontalalignment='center',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='#ecf0f1', 
                     edgecolor='#2c3e50', linewidth=2, alpha=0.95),
            family='monospace', color='#2c3e50')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='#f8f9fa')
    plt.close()
    
    print(f"[OK] Visual 1 (Battle of Confidence) saved: {output_path}")
    return output_path


def visual_2_thinking_effort(game_log, output_path='data/visual_2_thinking_effort.png'):
    """
    Visual 2: "Thinking Effort" (Dual-Axis Chart)
    
    Shows simulation count (bars) and search depth (line) for MCTS agent.
    Demonstrates how AI "thinks harder" in mid-game.
    """
    # Get MCTS agent data only (player 1, index 1)
    mcts_data = [(t['turn_number'], t['simulation_count'], t['search_depth']) 
                 for t in game_log 
                 if t['active_player'] == 1 and t['player_type'] == 'MCTS']
    
    if not mcts_data:
        print("⚠ Warning: No MCTS data found for Visual 2")
        return
    
    turns, sim_counts, depths = zip(*mcts_data)
    
    # Create figure with dual y-axes
    fig, ax1 = plt.subplots(figsize=(18, 11))
    fig.patch.set_facecolor('#f8f9fa')
    ax1.set_facecolor('#ffffff')
    
    # Adjust subplot to make room for stats box below
    plt.subplots_adjust(bottom=0.20)
    
    # Left Y-axis: Simulation Count (Bars)
    color_bars = '#3498db'
    bars = ax1.bar(turns, sim_counts, alpha=0.7, color=color_bars, 
                   edgecolor='#2c3e50', linewidth=1.5, label='Simulation Count', zorder=2)
    ax1.set_xlabel('Turn Number', fontsize=16, fontweight='bold', color='#2c3e50')
    ax1.set_ylabel('Simulation Count', fontsize=16, fontweight='bold', color=color_bars)
    ax1.tick_params(axis='y', labelcolor=color_bars, labelsize=12)
    ax1.tick_params(axis='x', labelsize=12)
    
    # Add value labels on bars
    for i, (turn, count) in enumerate(zip(turns, sim_counts)):
        if i % 2 == 0:  # Label every other bar to avoid clutter
            ax1.text(turn, count, f'{count}', ha='center', va='bottom', 
                    fontsize=9, fontweight='bold', color='#2c3e50')
    
    # Right Y-axis: Search Depth (Line)
    ax2 = ax1.twinx()
    color_line = '#e74c3c'
    line = ax2.plot(turns, depths, color=color_line, linewidth=4, 
                    marker='D', markersize=10, label='Max Search Depth', 
                    alpha=0.9, markeredgecolor='white', markeredgewidth=2, zorder=3)
    ax2.set_ylabel('Max Search Depth', fontsize=16, fontweight='bold', color=color_line)
    ax2.tick_params(axis='y', labelcolor=color_line, labelsize=12)
    
    # Title
    ax1.set_title('Visual 2: "Thinking Effort"\nMCTS Computational Intensity Over Time', 
                  fontsize=20, fontweight='bold', color='#2c3e50', pad=20)
    
    # Grid only on left axis
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=1, axis='y', zorder=0)
    ax1.set_axisbelow(True)
    
    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, 
              loc='upper left', fontsize=13, framealpha=0.95, 
              edgecolor='#2c3e50', fancybox=True, shadow=True)
    
    # Statistics box
    avg_sims = np.mean(sim_counts)
    max_sims = max(sim_counts)
    avg_depth = np.mean(depths)
    max_depth = max(depths)
    
    # Find mid-game (middle third)
    mid_start = len(turns) // 3
    mid_end = 2 * len(turns) // 3
    mid_game_depths = depths[mid_start:mid_end]
    early_game_depths = depths[:mid_start] if mid_start > 0 else [depths[0]]
    
    mid_avg_depth = np.mean(mid_game_depths) if mid_game_depths else 0
    early_avg_depth = np.mean(early_game_depths) if early_game_depths else 0
    
    stats_text = (
        f"COMPUTATIONAL EFFORT\n"
        f"{'─' * 35}\n"
        f"Simulations:\n"
        f"  Average:  {avg_sims:.0f}\n"
        f"  Peak:     {max_sims:.0f}\n"
        f"\n"
        f"Search Depth:\n"
        f"  Average:  {avg_depth:.1f}\n"
        f"  Maximum:  {max_depth}\n"
        f"\n"
        f"Mid-Game vs Early:\n"
        f"  Depth Increase: {((mid_avg_depth/early_avg_depth - 1) * 100):.1f}%"
    )
    
    # Place stats box outside plot area on the right
    fig.text(0.85, 0.75, stats_text,
            fontsize=11, verticalalignment='top', horizontalalignment='left',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='#ecf0f1', 
                     edgecolor='#2c3e50', linewidth=2, alpha=0.95),
            family='monospace', color='#2c3e50')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='#f8f9fa')
    plt.close()
    
    print(f"[OK] Visual 2 (Thinking Effort) saved: {output_path}")
    return output_path


def visual_3_strategy_dna(game_log, output_path='data/visual_3_strategy_dna.png'):
    """
    Visual 3: "Strategy DNA" (Stacked Bar Chart)
    
    Compares total cards purchased by tier for both players.
    Shows Heuristic focuses on Tier 1, while MCTS buys mix of Tier 2/3.
    """
    # Get final card counts for each player
    p1_final = None
    p2_final = None
    
    # Find the last turn for each player
    for turn in reversed(game_log):
        if turn['active_player'] == 0 and p1_final is None:
            p1_final = turn['cards_owned_by_tier']
        if turn['active_player'] == 1 and p2_final is None:
            p2_final = turn['cards_owned_by_tier']
        if p1_final and p2_final:
            break
    
    if not p1_final or not p2_final:
        print("⚠ Warning: Insufficient card data for Visual 3")
        return
    
    # Extract tier counts
    p1_tier1, p1_tier2, p1_tier3 = p1_final
    p2_tier1, p2_tier2, p2_tier3 = p2_final
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 13))
    fig.patch.set_facecolor('#f8f9fa')
    ax.set_facecolor('#ffffff')
    
    # Adjust subplot to make room for stats box below
    plt.subplots_adjust(bottom=0.22)
    
    # Data setup
    players = ['Heuristic Agent\n(Player 1)', 'MCTS Agent\n(Player 2)']
    tier1_counts = [p1_tier1, p2_tier1]
    tier2_counts = [p1_tier2, p2_tier2]
    tier3_counts = [p1_tier3, p2_tier3]
    
    # Bar positions
    x = np.arange(len(players))
    width = 0.6
    
    # Colors for tiers
    color_tier1 = '#27ae60'  # Green
    color_tier2 = '#f39c12'  # Yellow/Orange
    color_tier3 = '#3498db'  # Blue
    
    # Create stacked bars
    p1 = ax.bar(x, tier1_counts, width, label='Tier 1 (Entry)', 
                color=color_tier1, edgecolor='#2c3e50', linewidth=2)
    p2 = ax.bar(x, tier2_counts, width, bottom=tier1_counts, 
                label='Tier 2 (Mid)', color=color_tier2, 
                edgecolor='#2c3e50', linewidth=2)
    p3 = ax.bar(x, tier3_counts, width, 
                bottom=np.array(tier1_counts) + np.array(tier2_counts),
                label='Tier 3 (Premium)', color=color_tier3, 
                edgecolor='#2c3e50', linewidth=2)
    
    # Add value labels on each segment
    def add_labels(bars, values, bottoms=None):
        for i, (bar, val) in enumerate(zip(bars, values)):
            if val > 0:  # Only show if count > 0
                height = bar.get_height()
                y_pos = bar.get_y() + height / 2
                ax.text(bar.get_x() + bar.get_width() / 2, y_pos, 
                       f'{val}', ha='center', va='center',
                       fontsize=16, fontweight='bold', color='white',
                       bbox=dict(boxstyle='round,pad=0.3', 
                               facecolor='#2c3e50', alpha=0.8))
    
    add_labels(p1, tier1_counts)
    add_labels(p2, tier2_counts)
    add_labels(p3, tier3_counts)
    
    # Add total labels above bars
    p1_total = sum([p1_tier1, p1_tier2, p1_tier3])
    p2_total = sum([p2_tier1, p2_tier2, p2_tier3])
    totals = [p1_total, p2_total]
    
    for i, (player_x, total) in enumerate(zip(x, totals)):
        ax.text(player_x, total + 0.5, f'Total: {total}', 
               ha='center', va='bottom', fontsize=14, 
               fontweight='bold', color='#2c3e50',
               bbox=dict(boxstyle='round,pad=0.4', 
                       facecolor='#ecf0f1', alpha=0.9,
                       edgecolor='#2c3e50', linewidth=1.5))
    
    # Styling
    ax.set_ylabel('Total Cards Purchased', fontsize=16, fontweight='bold', color='#2c3e50')
    ax.set_title('Visual 3: "Strategy DNA"\nCard Tier Distribution by Player', 
                 fontsize=20, fontweight='bold', color='#2c3e50', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(players, fontsize=14, fontweight='bold')
    ax.tick_params(axis='y', labelsize=12)
    
    # Legend
    ax.legend(loc='upper right', fontsize=13, framealpha=0.95, 
             edgecolor='#2c3e50', fancybox=True, shadow=True)
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=1, axis='y')
    ax.set_axisbelow(True)
    
    # Analysis box
    # Calculate percentages
    p1_tier1_pct = (p1_tier1 / p1_total * 100) if p1_total > 0 else 0
    p1_tier2_pct = (p1_tier2 / p1_total * 100) if p1_total > 0 else 0
    p1_tier3_pct = (p1_tier3 / p1_total * 100) if p1_total > 0 else 0
    
    p2_tier1_pct = (p2_tier1 / p2_total * 100) if p2_total > 0 else 0
    p2_tier2_pct = (p2_tier2 / p2_total * 100) if p2_total > 0 else 0
    p2_tier3_pct = (p2_tier3 / p2_total * 100) if p2_total > 0 else 0
    
    analysis_text = (
        f"STRATEGY ANALYSIS\n"
        f"{'─' * 38}\n"
        f"Heuristic Agent:\n"
        f"  Tier 1: {p1_tier1_pct:.0f}%  (Entry cards)\n"
        f"  Tier 2: {p1_tier2_pct:.0f}%  (Mid-tier)\n"
        f"  Tier 3: {p1_tier3_pct:.0f}%  (Premium)\n"
        f"\n"
        f"MCTS Agent:\n"
        f"  Tier 1: {p2_tier1_pct:.0f}%  (Entry cards)\n"
        f"  Tier 2: {p2_tier2_pct:.0f}%  (Mid-tier)\n"
        f"  Tier 3: {p2_tier3_pct:.0f}%  (Premium)\n"
        f"\n"
        f"Strategic Focus:\n"
        f"  Heuristic: {'Tier 1' if p1_tier1_pct > 50 else 'Mixed'}\n"
        f"  MCTS: {'Balanced' if max(p2_tier1_pct, p2_tier2_pct, p2_tier3_pct) < 60 else 'Focused'}"
    )
    
    # Place analysis box below plot area
    fig.text(0.5, 0.09, analysis_text,
            fontsize=11, verticalalignment='top', horizontalalignment='center',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='#ecf0f1', 
                     edgecolor='#2c3e50', linewidth=2, alpha=0.95),
            family='monospace', color='#2c3e50')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='#f8f9fa')
    plt.close()
    
    print(f"[OK] Visual 3 (Strategy DNA) saved: {output_path}")
    return output_path


def generate_all_visuals(json_path):
    """Generate all three comparison visualizations."""
    print("\n" + "=" * 70)
    print("DEEP DIVE ANALYTICS - COMPARISON VISUALIZATIONS")
    print("=" * 70 + "\n")
    
    # Load data
    print(f"Loading game data: {json_path}")
    try:
        game_log, metadata = load_game_log(json_path)
        print(f"[OK] Loaded {len(game_log)} turn entries")
        
        if metadata:
            winner = metadata.get('winner')
            if winner is not None:
                print(f"[OK] Game winner: Player {winner + 1}")
        print()
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return
    
    # Ensure output directory exists
    Path('data').mkdir(exist_ok=True)
    
    # Generate all three visuals
    print("Generating visualizations...\n")
    
    outputs = []
    try:
        output = visual_1_battle_of_confidence(game_log)
        if output:
            outputs.append(output)
    except Exception as e:
        print(f"✗ Error generating Visual 1: {e}")
    
    try:
        output = visual_2_thinking_effort(game_log)
        if output:
            outputs.append(output)
    except Exception as e:
        print(f"✗ Error generating Visual 2: {e}")
    
    try:
        output = visual_3_strategy_dna(game_log)
        if output:
            outputs.append(output)
    except Exception as e:
        print(f"✗ Error generating Visual 3: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    if len(outputs) == 3:
        print("ALL VISUALIZATIONS GENERATED SUCCESSFULLY!")
    else:
        print(f"COMPLETED: {len(outputs)}/3 visualizations generated")
    print("=" * 70)
    
    if outputs:
        print("\nOutput files:")
        for path in outputs:
            print(f"  • {path}")
        
        print("\nTIP: For move accuracy analysis, run:")
        print("  python plot_move_accuracy.py")
        print()
    
    print("=" * 70 + "\n")


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
            print("  python generate_comparison_visuals.py [path/to/game_log.json]")
            print("\nOr run a game first:")
            print("  python main.py")
            sys.exit(1)
    
    generate_all_visuals(json_path)
