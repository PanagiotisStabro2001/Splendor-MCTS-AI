"""
Comprehensive Post-Game Analytics Generator for Splendor AI Battle

Generates 5 professional visualizations after each game:
1. Game Momentum & Win Probability Evolution
2. Move Quality Assessment (Accuracy Metrics)
3. Strategic Profiling ("Strategy DNA")
4. Computational Intensity & Search Depth
5. Decision Tree Visualization (already implemented via mcts_brain)

Usage:
    Run this on a game folder in data/game_YYYYMMDD_HHMMSS/
    Or run automatically after game completion in main.py
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np


class PostGameAnalytics:
    """Generate comprehensive analytics visualizations for completed games."""
    
    def __init__(self, game_folder: str):
        """
        Initialize analytics generator.
        
        Args:
            game_folder: Path to game data folder (e.g., data/game_20260119_215803)
        """
        self.game_folder = Path(game_folder)
        self.game_log = self._load_game_log()
        self.players = self._identify_players()
        
    def _load_game_log(self) -> List[Dict]:
        """Load game log JSON from logs/ folder."""
        # Extract game_id from folder name
        game_id = self.game_folder.name.replace('game_', '')
        log_path = Path('logs') / f'game_{game_id}.json'
        
        if not log_path.exists():
            raise FileNotFoundError(f"Game log not found: {log_path}")
        
        with open(log_path, 'r') as f:
            data = json.load(f)
            # Handle case where data might be a list directly or wrapped
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'game_log' in data:
                return data['game_log']
            else:
                raise ValueError(f"Unexpected game log format in {log_path}")
    
    def _identify_players(self) -> Dict[int, Dict]:
        """Identify players and their types."""
        players = {}
        for entry in self.game_log:
            player_id = entry['active_player']
            if player_id not in players:
                players[player_id] = {
                    'type': entry['player_type'],
                    'name': f"Player {player_id + 1} ({entry['player_type']})"
                }
        return players
    
    def generate_all_visualizations(self):
        """Generate all 5 visualization categories."""
        print(f"\n{'='*60}")
        print(f"Generating Post-Game Analytics: {self.game_folder.name}")
        print(f"{'='*60}\n")
        
        # 1. Win Probability Evolution
        self.visual_1_win_probability_evolution()
        
        # 1B. Points Evolution
        self.visual_1b_points_evolution()
        
        # 2. Move Quality Assessment
        self.visual_2_move_quality_assessment()
        
        # 3. Strategic Profiling (Strategy DNA)
        self.visual_3_strategy_dna()
        
        # 4. Computational Intensity & Search Depth
        self.visual_4_computational_intensity()
        
        # 5. Already generated: Decision Tree (mcts_brain)
        print("[OK] Visual 5: Decision Tree already generated (mcts_brain_*.html)")
        
        print(f"\n{'='*60}")
        print(f"All Analytics Generated Successfully!")
        print(f"Location: {self.game_folder}")
        print(f"{'='*60}\n")
    
    def visual_1_win_probability_evolution(self):
        """
        Visual 1: Win Probability Evolution for Both Players
        
        Shows each player's win probability as separate lines.
        """
        print("Generating Visual 1: Win Probability Evolution...")
        
        # Extract data for both players
        player_data = {pid: [] for pid in self.players.keys()}
        
        for entry in self.game_log:
            player_id = entry['active_player']
            player_data[player_id].append({
                'turn': entry['turn_number'],
                'win_prob': entry['win_probability'],
                'points': entry['player_points']
            })
        
        if not any(player_data.values()):
            print("  ⚠ No data found, skipping...")
            return
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Plot win probabilities for both players
        colors = ['#2E86AB', '#E74C3C']
        
        for idx, (player_id, player_info) in enumerate(self.players.items()):
            data = player_data[player_id]
            if not data:
                continue
                
            turns = [d['turn'] for d in data]
            win_probs = [d['win_prob'] * 100 for d in data]  # Convert to percentage
            
            ax.plot(turns, win_probs, color=colors[idx], linewidth=3, 
                   marker='o', markersize=6, label=f"{player_info['name']}", 
                   alpha=0.85)
        
        ax.set_xlabel('Turn Number', fontsize=13, fontweight='bold')
        ax.set_ylabel('Win Probability (%)', fontsize=13, fontweight='bold')
        ax.set_ylim(-5, 105)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Add confidence zones
        ax.axhspan(0, 40, alpha=0.05, color='red', label='Losing Position')
        ax.axhspan(40, 60, alpha=0.05, color='gray', label='Even Position')
        ax.axhspan(60, 100, alpha=0.05, color='green', label='Winning Position')
        ax.axhline(y=50, color='black', linestyle=':', linewidth=1.5, alpha=0.5)
        
        # Find turning point (largest swing in win probability)
        all_turns = []
        all_diffs = []
        for player_id in self.players.keys():
            data = player_data[player_id]
            if len(data) > 1:
                turns = [d['turn'] for d in data]
                probs = [d['win_prob'] * 100 for d in data]
                for i in range(1, len(probs)):
                    diff = abs(probs[i] - probs[i-1])
                    all_turns.append(turns[i])
                    all_diffs.append(diff)
        
        if all_diffs:
            max_diff_idx = all_diffs.index(max(all_diffs))
            turning_turn = all_turns[max_diff_idx]
            ax.axvline(x=turning_turn, color='red', linestyle='--', linewidth=2, alpha=0.7)
            ax.annotate(f'Critical Turn {turning_turn}',
                       xy=(turning_turn, 50),
                       xytext=(turning_turn + 2, 75),
                       fontsize=11, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', lw=2, color='red'))
        
        # Title and legend
        plt.title("Win Probability Evolution: Both Players",
                 fontsize=15, fontweight='bold', pad=20)
        ax.legend(loc='best', fontsize=11, framealpha=0.9)
        
        fig.tight_layout()
        output_path = self.game_folder / 'visual_1_win_probability.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  [OK] Saved: {output_path}")
    
    def visual_1b_points_evolution(self):
        """
        Visual 1B: Points Evolution Over Time
        
        Shows how victory points accumulate for both players throughout the game.
        """
        print("Generating Visual 1B: Points Evolution...")
        
        # Extract data for both players
        player_data = {pid: [] for pid in self.players.keys()}
        
        for entry in self.game_log:
            player_id = entry['active_player']
            player_data[player_id].append({
                'turn': entry['turn_number'],
                'points': entry['player_points']
            })
        
        if not any(player_data.values()):
            print("  ⚠ No data found, skipping...")
            return
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Plot points for both players
        colors = ['#2E86AB', '#E74C3C']
        markers = ['o', 's']
        
        for idx, (player_id, player_info) in enumerate(self.players.items()):
            data = player_data[player_id]
            if not data:
                continue
                
            turns = [d['turn'] for d in data]
            points = [d['points'] for d in data]
            
            ax.plot(turns, points, color=colors[idx], linewidth=3, 
                   marker=markers[idx], markersize=7, label=player_info['name'], 
                   alpha=0.85)
            
            # Fill area under curve
            ax.fill_between(turns, points, alpha=0.2, color=colors[idx])
        
        # Add winning threshold line
        ax.axhline(y=15, color='gold', linestyle='--', linewidth=2.5, 
                  label='Winning Threshold (15 points)', alpha=0.7)
        
        ax.set_xlabel('Turn Number', fontsize=13, fontweight='bold')
        ax.set_ylabel('Victory Points', fontsize=13, fontweight='bold')
        ax.set_ylim(0, max([max([d['points'] for d in player_data[pid]]) 
                           for pid in self.players.keys()]) + 2)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Calculate final point difference
        final_points = {}
        for player_id, player_info in self.players.items():
            data = player_data[player_id]
            if data:
                final_points[player_info['name']] = data[-1]['points']
        
        if len(final_points) == 2:
            names = list(final_points.keys())
            diff = abs(final_points[names[0]] - final_points[names[1]])
            winner = names[0] if final_points[names[0]] > final_points[names[1]] else names[1]
            
            # Add result annotation
            ax.text(0.98, 0.02, 
                   f"Final: {names[0]}: {final_points[names[0]]} pts\n"
                   f"Final: {names[1]}: {final_points[names[1]]} pts\n"
                   f"Winner: {winner} (+{diff} pts)",
                   transform=ax.transAxes,
                   fontsize=10, verticalalignment='bottom', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8),
                   family='monospace')
        
        # Title and legend
        plt.title("Victory Points Evolution",
                 fontsize=15, fontweight='bold', pad=20)
        ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
        
        fig.tight_layout()
        output_path = self.game_folder / 'visual_1b_points_evolution.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  [OK] Saved: {output_path}")
    
    def visual_2_move_quality_assessment(self):
        """
        Visual 2: Move Quality Assessment (Accuracy Metrics)
        
        Strip plot showing move classifications for both players.
        Uses MCTS as "Ground Truth" judge.
        """
        print("Generating Visual 2: Move Quality Assessment...")
        
        # Define move quality categories and colors
        quality_map = {
            'Best': {'score': 100, 'color': '#27AE60', 'label': 'Best Move'},
            'Good': {'score': 75, 'color': '#52B788', 'label': 'Inaccuracy'},
            'Inaccuracy': {'score': 50, 'color': '#F39C12', 'label': 'Mistake'},
            'Mistake': {'score': 25, 'color': '#E67E22', 'label': 'Mistake'},
            'Blunder': {'score': 0, 'color': '#E74C3C', 'label': 'Blunder'}
        }
        
        # Collect move quality data
        player_moves = {pid: [] for pid in self.players.keys()}
        
        for entry in self.game_log:
            player_id = entry['active_player']
            classification = entry.get('move_classification', 'Unknown')
            
            if classification in quality_map:
                player_moves[player_id].append({
                    'turn': entry['turn_number'],
                    'classification': classification,
                    'score': quality_map[classification]['score'],
                    'color': quality_map[classification]['color'],
                    'accuracy_loss': entry.get('accuracy_loss', 0)
                })
        
        # Create figure
        fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharey=True)
        
        for idx, (player_id, player_info) in enumerate(self.players.items()):
            ax = axes[idx]
            moves = player_moves[player_id]
            
            if not moves:
                ax.text(0.5, 0.5, 'No Data Available', 
                       ha='center', va='center', fontsize=14)
                ax.set_title(player_info['name'], fontsize=13, fontweight='bold')
                continue
            
            # Create strip plot
            turns = [m['turn'] for m in moves]
            scores = [m['score'] for m in moves]
            colors = [m['color'] for m in moves]
            
            # Plot points
            ax.scatter(turns, scores, c=colors, s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
            
            # Add horizontal lines for categories
            for cat, info in quality_map.items():
                ax.axhline(y=info['score'], color=info['color'], 
                          linestyle='--', alpha=0.3, linewidth=1)
            
            # Calculate statistics
            total_moves = len(moves)
            best_count = sum(1 for m in moves if m['classification'] == 'Best')
            blunder_count = sum(1 for m in moves if m['classification'] == 'Blunder')
            avg_score = np.mean(scores)
            
            # Add stats box
            stats_text = (
                f"Total Moves: {total_moves}\n"
                f"Best Moves: {best_count} ({best_count/total_moves*100:.1f}%)\n"
                f"Blunders: {blunder_count} ({blunder_count/total_moves*100:.1f}%)\n"
                f"Avg Quality: {avg_score:.1f}/100"
            )
            
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                   family='monospace')
            
            # Styling
            ax.set_xlabel('Turn Number', fontsize=12, fontweight='bold')
            if idx == 0:
                ax.set_ylabel('Move Quality Score', fontsize=12, fontweight='bold')
            ax.set_title(player_info['name'], fontsize=13, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
            ax.set_ylim(-10, 110)
        
        # Global title and legend
        plt.suptitle('Move Quality Strip Plot: Performance Comparison',
                    fontsize=15, fontweight='bold', y=0.98)
        
        # Create custom legend
        legend_elements = [
            mpatches.Patch(color=info['color'], label=info['label'])
            for cat, info in quality_map.items()
        ]
        fig.legend(handles=legend_elements, loc='lower center', 
                  ncol=len(quality_map), fontsize=10, framealpha=0.9,
                  bbox_to_anchor=(0.5, -0.02))
        
        fig.tight_layout(rect=[0, 0.02, 1, 0.96])
        output_path = self.game_folder / 'visual_2_move_quality_strip_plot.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  [OK] Saved: {output_path}")
    
    def visual_3_strategy_dna(self):
        """
        Visual 3: Strategic Profiling ("Strategy DNA")
        
        Comparative bar chart showing card tier distributions.
        Demonstrates qualitative difference in playstyle.
        """
        print("Generating Visual 3: Strategy DNA...")
        
        # Track final card tier distribution for each player
        player_cards = {pid: {'Tier 1': 0, 'Tier 2': 0, 'Tier 3': 0, 'Nobles': 0} 
                       for pid in self.players.keys()}
        
        # Get final state for each player
        for player_id in self.players.keys():
            player_moves = [e for e in self.game_log if e['active_player'] == player_id]
            if player_moves:
                final_move = player_moves[-1]
                tiers = final_move['cards_owned_by_tier']
                player_cards[player_id]['Tier 1'] = tiers[0]
                player_cards[player_id]['Tier 2'] = tiers[1]
                player_cards[player_id]['Tier 3'] = tiers[2]
                player_cards[player_id]['Nobles'] = final_move['nobles_owned']
        
        # Create grouped bar chart
        fig, ax = plt.subplots(figsize=(12, 7))
        
        categories = ['Tier 1\n(Cheap)', 'Tier 2\n(Medium)', 'Tier 3\n(Expensive)', 'Nobles']
        x = np.arange(len(categories))
        width = 0.35
        
        # Colors for each player
        colors = ['#3498DB', '#E74C3C']
        
        for idx, (player_id, player_info) in enumerate(self.players.items()):
            values = list(player_cards[player_id].values())
            offset = width * (idx - 0.5)
            bars = ax.bar(x + offset, values, width, label=player_info['name'],
                         color=colors[idx], alpha=0.8, edgecolor='black', linewidth=1.5)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}',
                           ha='center', va='bottom', fontweight='bold', fontsize=11)
        
        # Calculate strategy insights
        for player_id, player_info in self.players.items():
            cards = player_cards[player_id]
            total_cards = cards['Tier 1'] + cards['Tier 2'] + cards['Tier 3']
            
            if total_cards > 0:
                tier1_pct = cards['Tier 1'] / total_cards * 100
                tier3_pct = cards['Tier 3'] / total_cards * 100
                
                if tier1_pct > 60:
                    strategy = "\"Quantity over Quality\""
                elif tier3_pct > 30:
                    strategy = "\"Quality over Quantity\""
                else:
                    strategy = "\"Balanced\""
                
                print(f"    {player_info['name']}: {strategy} "
                     f"(T1: {tier1_pct:.0f}%, T3: {tier3_pct:.0f}%)")
        
        # Styling
        ax.set_xlabel('Development Card Tier', fontsize=13, fontweight='bold')
        ax.set_ylabel('Cards Acquired', fontsize=13, fontweight='bold')
        ax.set_title('Strategy DNA: Card Tier Distribution Comparison',
                    fontsize=15, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=11)
        ax.legend(fontsize=11, loc='upper right', framealpha=0.9)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add interpretation box
        interpretation = (
            "Interpretation:\n"
            "• High Tier 1 = Greedy/Fast strategy (low points)\n"
            "• High Tier 3 = Investor strategy (high points)\n"
            "• Nobles = Strategic positioning bonus"
        )
        ax.text(0.02, 0.98, interpretation, transform=ax.transAxes,
               fontsize=9, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8),
               family='monospace')
        
        fig.tight_layout()
        output_path = self.game_folder / 'visual_3_strategy_dna.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  [OK] Saved: {output_path}")
    
    def visual_4_computational_intensity(self):
        """
        Visual 4: Computational Intensity & Decision Time Comparison
        
        Shows both agents' decision-making patterns and computational effort.
        """
        print("Generating Visual 4: Computational Intensity...")
        
        # Extract data for both players
        player_data = {pid: [] for pid in self.players.keys()}
        
        for entry in self.game_log:
            player_id = entry['active_player']
            player_data[player_id].append({
                'turn': entry['turn_number'],
                'simulations': entry.get('simulation_count', 0),
                'depth': entry.get('search_depth', 0),
                'time_ms': entry['duration_ms'],
                'player_type': entry['player_type']
            })
        
        # Create figure with multiple subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Colors for each player
        colors = ['#2E86AB', '#E74C3C']
        
        # Subplot 1: Decision Time Comparison (Both Players)
        for idx, (player_id, player_info) in enumerate(self.players.items()):
            data = player_data[player_id]
            if not data:
                continue
                
            turns = [d['turn'] for d in data]
            times = [d['time_ms'] / 1000 for d in data]  # Convert to seconds
            
            ax1.plot(turns, times, color=colors[idx], linewidth=2.5,
                    marker='o', markersize=4, label=player_info['name'], alpha=0.7)
        
        ax1.set_xlabel('Turn Number', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax1.set_title('Decision Time Comparison', fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='best', fontsize=10)
        
        # Subplot 2: MCTS Simulations per Turn
        mcts_player = next((pid for pid, pinfo in self.players.items() if pinfo['type'] == 'MCTS'), None)
        if mcts_player is not None and player_data[mcts_player]:
            mcts_data = player_data[mcts_player]
            turns = [d['turn'] for d in mcts_data]
            simulations = [d['simulations'] for d in mcts_data]
            
            ax2.plot(turns, simulations, color='#2E86AB', linewidth=2.5, 
                    marker='o', markersize=5, label='MCTS Simulations')
            ax2.fill_between(turns, simulations, alpha=0.3, color='#2E86AB')
            
            # Add average line
            avg_sims = np.mean(simulations)
            ax2.axhline(y=avg_sims, color='red', linestyle='--', 
                       linewidth=2, alpha=0.6, label=f'Avg: {avg_sims:.0f}')
            
            ax2.set_xlabel('Turn Number', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Simulations Count', fontsize=12, fontweight='bold')
            ax2.set_title('MCTS Thinking Effort', fontsize=13, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.legend(loc='best', fontsize=10)
        else:
            ax2.text(0.5, 0.5, 'No MCTS data', ha='center', va='center', fontsize=14)
            ax2.set_title('MCTS Thinking Effort', fontsize=13, fontweight='bold')
        
        # Subplot 3: MCTS Search Depth
        if mcts_player is not None and player_data[mcts_player]:
            mcts_data = player_data[mcts_player]
            turns = [d['turn'] for d in mcts_data]
            depths = [d['depth'] for d in mcts_data]
            
            ax3.plot(turns, depths, color='#A23B72', linewidth=2.5,
                    marker='s', markersize=5, label='Search Depth')
            ax3.fill_between(turns, depths, alpha=0.3, color='#A23B72')
            
            ax3.set_xlabel('Turn Number', fontsize=12, fontweight='bold')
            ax3.set_ylabel('Max Search Depth', fontsize=12, fontweight='bold')
            ax3.set_title('MCTS Search Depth', fontsize=13, fontweight='bold')
            ax3.grid(True, alpha=0.3)
            ax3.legend(loc='best', fontsize=10)
        else:
            ax3.text(0.5, 0.5, 'No MCTS data', ha='center', va='center', fontsize=14)
            ax3.set_title('MCTS Search Depth', fontsize=13, fontweight='bold')
        
        # Subplot 4: Average Decision Time Bar Chart
        avg_times = []
        player_names = []
        
        for player_id, player_info in self.players.items():
            data = player_data[player_id]
            if data:
                times = [d['time_ms'] / 1000 for d in data]
                avg_times.append(np.mean(times))
                player_names.append(player_info['name'])
        
        if avg_times:
            bars = ax4.bar(player_names, avg_times, color=colors[:len(avg_times)], 
                          alpha=0.7, edgecolor='black', linewidth=2)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.3f}s',
                        ha='center', va='bottom', fontweight='bold', fontsize=11)
            
            ax4.set_ylabel('Average Time (seconds)', fontsize=12, fontweight='bold')
            ax4.set_title('Average Decision Time per Move', fontsize=13, fontweight='bold')
            ax4.grid(True, alpha=0.3, axis='y')
        else:
            ax4.text(0.5, 0.5, 'No data', ha='center', va='center', fontsize=14)
            ax4.set_title('Average Decision Time', fontsize=13, fontweight='bold')
        
        # Add statistics box for MCTS if available
        if mcts_player is not None and player_data[mcts_player]:
            mcts_data = player_data[mcts_player]
            simulations = [d['simulations'] for d in mcts_data]
            depths = [d['depth'] for d in mcts_data]
            times = [d['time_ms'] / 1000 for d in mcts_data]
            
            stats_text = (
                f"MCTS Statistics:\n"
                f"Avg Sims: {np.mean(simulations):.0f}\n"
                f"Max Sims: {max(simulations)}\n"
                f"Avg Depth: {np.mean(depths):.1f}\n"
                f"Max Depth: {max(depths)}\n"
                f"Avg Time: {np.mean(times):.2f}s"
            )
            
            fig.text(0.98, 0.5, stats_text, fontsize=10,
                    verticalalignment='center', horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
                    family='monospace')
        
        plt.suptitle('Computational Intensity & Decision Time Comparison',
                    fontsize=15, fontweight='bold', y=0.995)
        
        fig.tight_layout(rect=[0, 0, 0.95, 0.99])
        output_path = self.game_folder / 'visual_4_computational_intensity.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  [OK] Saved: {output_path}")
        
        # Print insights
        if mcts_player is not None and player_data[mcts_player]:
            mcts_data = player_data[mcts_player]
            simulations = [d['simulations'] for d in mcts_data]
            depths = [d['depth'] for d in mcts_data]
            times = [d['time_ms'] / 1000 for d in mcts_data]
            
            print(f"    Insights:")
            print(f"      • Adaptive Depth: {'Yes' if max(depths) > min(depths) + 2 else 'No (consistent)'}")
            print(f"      • Performance: {np.mean(simulations):.0f} sims/turn in {np.mean(times):.2f}s avg")
            
            # Compare decision times
            for player_id, player_info in self.players.items():
                data = player_data[player_id]
                if data:
                    times = [d['time_ms'] / 1000 for d in data]
                    print(f"      • {player_info['name']}: {np.mean(times)*1000:.1f}ms avg per move")


def generate_analytics_for_game(game_folder: str):
    """
    Convenience function to generate all analytics for a game.
    
    Args:
        game_folder: Path to game folder (e.g., 'data/game_20260119_215803')
    """
    try:
        analytics = PostGameAnalytics(game_folder)
        analytics.generate_all_visualizations()
        return True
    except Exception as e:
        print(f"❌ Error generating analytics: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """CLI entry point for manual analytics generation."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python generate_post_game_analytics.py <game_folder>")
        print("Example: python generate_post_game_analytics.py data/game_20260119_215803")
        sys.exit(1)
    
    game_folder = sys.argv[1]
    success = generate_analytics_for_game(game_folder)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
