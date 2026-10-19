"""
Splendor AI Battle - Main Entry Point

A fully playable GUI-based simulation of Splendor board game.
Features Basic AI vs MCTS AI with spectator mode and post-game analytics.
"""

import time
import random
import hashlib
from typing import Tuple
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving figures
import matplotlib.pyplot as plt
from pathlib import Path

from game_engine.state import GameState
from game_engine.components import Action
from agents.basic import BasicAgent
from agents.advanced import MCTSAgent
from gui.window import GameWindow
from analytics.recorder import GameRecorder
from analytics.accuracy import MoveComparator
from generate_post_game_analytics import PostGameAnalytics

# Seed random number generator for varied games
random.seed()


def hash_state(state: GameState) -> str:
    """Create a hash of the game state for tracking."""
    state_str = f"{state.turn_number}_{state.current_player}_{state.player_points}"
    return hashlib.md5(state_str.encode()).hexdigest()[:12]


def generate_player_graphs(analysis_data: dict, game_id: str, agents):
    """Generate individual graph for each player showing move accuracy."""
    try:
        player_analyses = analysis_data.get('player_analyses', {})
        
        if not player_analyses:
            print("⚠ No player analyses found for graph generation")
            return
        
        for player_id_str, analysis in player_analyses.items():
            player_id = int(player_id_str)
            move_scores = analysis.get('move_scores', [])
            
            if not move_scores:
                print(f"⚠ No move scores for Player {player_id + 1}, skipping graph")
                continue
            
            # Create figure
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Plot move scores
            moves = list(range(1, len(move_scores) + 1))
            color = '#3498db' if player_id == 0 else '#e74c3c'
            
            ax.plot(moves, move_scores, color=color, linewidth=2, 
                   marker='o', markersize=5, alpha=0.7)
            
            # Add average line
            avg_score = analysis.get('quality_score', 0)
            ax.axhline(y=avg_score, color=color, linestyle='--', 
                      linewidth=2, alpha=0.5, label=f'Average: {avg_score:.1f}')
            
            # Styling
            player_type = agents[player_id].name
            ax.set_xlabel('Move Number', fontsize=12, fontweight='bold')
            ax.set_ylabel('Move Quality Score (0-100)', fontsize=12, fontweight='bold')
            ax.set_title(f'Player {player_id + 1} ({player_type}) - Move-by-Move Quality Analysis', 
                        fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='best', fontsize=11)
            ax.set_ylim(0, 110)
            
            # Add statistics box
            stats_text = (
                f"Total Moves: {analysis.get('total_moves', 0)}\n"
                f"Quality Score: {avg_score:.1f}/100\n"
                f"VP Moves: {analysis.get('vp_move_percent', 0):.1f}%\n"
                f"Buy Moves: {analysis.get('buy_move_percent', 0):.1f}%\n"
                f"Avg Time: {analysis.get('avg_time_ms', 0):.1f} ms"
            )
            
            ax.text(0.98, 0.97, stats_text, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                   family='monospace')
            
            # Save figure
            output_path = f"data/player_{player_id + 1}_{player_type}_accuracy_{game_id}.png"
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            print(f"[OK] Player {player_id + 1} ({player_type}) graph saved: {output_path}")
    
    except Exception as e:
        print(f"✗ Error generating player graphs: {e}")
        import traceback
        traceback.print_exc()


def run_game():
    """
    Main game loop.
    
    Handles:
    - GUI initialization
    - Game state management
    - Agent move execution
    - Move logging
    - Post-game analytics
    """
    # Initialize window
    window = GameWindow()
    
    # Game state variables
    game_state: GameState = None
    agents = []
    recorder: GameRecorder = None
    
    game_started = False
    turn_timer = 0
    last_turn_time = time.time()
    
    print("="*60)
    print("Splendor AI Battle")
    print("="*60)
    print("\nControls:")
    print("  - Click 'Start Game' to begin")
    print("  - Click 'Next Turn' for manual stepping")
    print("  - Click 'Auto' to toggle auto-play mode")
    print("  - Drag speed slider to adjust auto-play speed")
    print("  - Scroll in log area to view move history")
    print("\n" + "="*60 + "\n")
    
    # Main loop
    while window.running:
        # Handle events
        event = window.handle_events()
        
        if event == "quit":
            break
        
        elif event == "start_game":
            # Initialize new game
            print("Starting new game...")
            game_state = GameState(num_players=2)
            
            # Create agents
            agents = [
                BasicAgent(player_id=0),
                MCTSAgent(player_id=1, time_limit=2.0)
            ]
            
            # Initialize recorder
            recorder = GameRecorder()
            
            # Initialize game_log for deep dive analytics
            recorder.game_log = []
            
            # Start window
            window.start_game(game_state)
            window.logger.add_log(f"Player 1: {agents[0].name}")
            window.logger.add_log(f"Player 2: {agents[1].name}")
            window.logger.add_log("---")
            
            game_started = True
            turn_timer = 0
            last_turn_time = time.time()
            
            print(f"  Player 1: {agents[0].name}")
            print(f"  Player 2: {agents[1].name}")
            print()
        
        elif event == "next_turn":
            if game_state and not game_state.game_over:
                execute_turn(game_state, agents, window, recorder)
        
        # Auto-play mode
        if game_started and window.auto_play and not game_state.game_over:
            current_time = time.time()
            elapsed = current_time - last_turn_time
            
            if elapsed >= window.game_speed:
                execute_turn(game_state, agents, window, recorder)
                last_turn_time = current_time
        
        # Check for game over
        if game_state and game_state.game_over and game_started:
            game_started = False
            handle_game_over(game_state, agents, window, recorder)
        
        # Draw and update
        window.draw()
        window.update()
    
    window.quit()


def calculate_move_accuracy(game_state: GameState, player_id: int, actual_action: Action, 
                           mcts_agent: MCTSAgent):
    """
    Calculate move accuracy by comparing actual move to MCTS best move.
    Treats MCTS top choice as the "Perfect Move" (100% accuracy).
    
    Args:
        game_state: Current game state (before move)
        player_id: Player making the move
        actual_action: The actual move the player will make
        mcts_agent: MCTS agent to use as accuracy engine
    
    Returns:
        Dictionary with accuracy metrics
    """
    # Run MCTS evaluation from current player's perspective
    original_player = mcts_agent.player_id
    mcts_agent.player_id = player_id
    
    try:
        # Get MCTS best move and metadata
        best_action, metadata = mcts_agent.get_move(game_state, max_simulations=100)
        best_win_prob = metadata.get('win_probability', 0.5)
        
        # Check if actual move matches best move
        if actual_action == best_action:
            # Perfect move!
            return {
                'is_best_move': True,
                'best_win_prob': best_win_prob,
                'actual_win_prob': best_win_prob,
                'accuracy_loss': 0.0,
                'move_classification': 'Best',
                'best_action': str(best_action.type)
            }
        
        # Find actual move's win probability in MCTS tree
        # We need to look at the visit distribution to find it
        visit_dist = metadata.get('visit_distribution', [])
        
        # Try to estimate actual move's value from visit distribution
        # Since we ran simulations, if the move was considered, it should be there
        actual_win_prob = None
        
        # Simple approach: run a quick evaluation of the actual move
        temp_state = game_state.get_state_copy()
        temp_state.apply_action(actual_action)
        
        # Quick MCTS evaluation (20 sims) of resulting position
        opponent_eval = mcts_agent.evaluate_state_as_critic(
            temp_state, 
            target_player=player_id, 
            simulations=20
        )
        actual_win_prob = opponent_eval.get('win_probability', 0.5)
        
        # Calculate accuracy loss
        accuracy_loss = best_win_prob - actual_win_prob
        
        # Classify the move
        if accuracy_loss < 0.02:
            classification = 'Best'
        elif accuracy_loss < 0.10:
            classification = 'Inaccuracy'
        elif accuracy_loss < 0.20:
            classification = 'Mistake'
        else:
            classification = 'Blunder'
        
        return {
            'is_best_move': False,
            'best_win_prob': best_win_prob,
            'actual_win_prob': actual_win_prob,
            'accuracy_loss': accuracy_loss,
            'move_classification': classification,
            'best_action': str(best_action.type)
        }
    
    finally:
        # Restore original player
        mcts_agent.player_id = original_player


def execute_turn(game_state: GameState, agents, window: GameWindow, 
                recorder: GameRecorder):
    """
    Execute a single turn.
    
    Args:
        game_state: Current game state
        agents: List of agents
        window: Game window
        recorder: Move recorder
    """
    current_player = game_state.current_player
    agent = agents[current_player]
    
    # Get the MCTS agent for accuracy engine (assumed to be agents[1])
    mcts_engine = agents[1] if isinstance(agents[1], MCTSAgent) else None
    
    # Get move from agent
    start_time = time.time()
    
    # Get action and metadata (if MCTS agent)
    if isinstance(agent, MCTSAgent):
        action, mcts_metadata = agent.get_move(game_state)
        win_probability = mcts_metadata.get('win_probability', 0.5)
        search_depth = mcts_metadata.get('search_depth', 0)
        simulation_count = mcts_metadata.get('simulation_count', 0)
        visit_distribution = mcts_metadata.get('visit_distribution', [])
        
        # Capture MCTS tree for visualization (store from a mid-game turn)
        # Store around turn 10-15 for interesting tree
        if 10 <= game_state.turn_number <= 15 and not hasattr(recorder, 'mcts_tree_snapshot'):
            # Save the root node that was just created during get_move
            # We need to run MCTS again to capture the tree
            from agents.advanced import MCTSNode
            snapshot_root = MCTSNode(game_state.get_state_copy())
            
            # Quick MCTS run to build tree
            import time as time_module
            snapshot_start = time_module.time()
            snapshot_sims = 0
            while time_module.time() - snapshot_start < 2.0:  # 2 second snapshot
                node = agent._select(snapshot_root, agent.player_id)
                result = agent._simulate(node.state)
                node.backpropagate(result)
                snapshot_sims += 1
            
            recorder.mcts_tree_snapshot = snapshot_root
            recorder.mcts_tree_turn = game_state.turn_number
            print(f"  [Tree Snapshot] Captured MCTS tree at turn {game_state.turn_number} ({snapshot_sims} sims)")
    else:
        # Basic agent - just get the move
        action = agent.select_move(game_state)
        win_probability = None  # Will be filled by MCTS Critic
        search_depth = 0
        simulation_count = 0
        visit_distribution = []
    
    duration_ms = (time.time() - start_time) * 1000
    
    # ACCURACY ENGINE: Calculate move accuracy before applying the move
    accuracy_data = None
    if mcts_engine:
        print(f"  [Accuracy Engine] Evaluating move quality...")
        accuracy_start = time.time()
        accuracy_data = calculate_move_accuracy(game_state, current_player, action, mcts_engine)
        accuracy_time = (time.time() - accuracy_start) * 1000
        
        classification = accuracy_data.get('move_classification', 'Unknown')
        loss = accuracy_data.get('accuracy_loss', 0)
        print(f"  [Accuracy Engine] Classification: {classification} (Loss: {loss:.3f}) [{accuracy_time:.0f}ms]")
    
    # Record move
    state_hash = hash_state(game_state)
    agent_type = "Basic" if isinstance(agent, BasicAgent) else "MCTS"
    recorder.record_move(
        turn_id=game_state.turn_number,
        player_id=current_player,
        player_type=agent_type,
        action=action,
        state_hash=state_hash,
        duration_ms=duration_ms
    )
    
    # Log to GUI
    move_desc = agent.get_move_description(action)
    log_text = f"P{current_player + 1}: {move_desc}"
    
    # Add MCTS simulations info if applicable
    if isinstance(agent, MCTSAgent):
        log_text += f" ({simulation_count} sims)"
    
    # Add to GUI with turn number
    window.logger.add_log(f"Turn {game_state.turn_number} | {log_text}")
    
    # Print to console
    print(f"  Turn {game_state.turn_number} | {log_text} [{duration_ms:.0f}ms]")
    
    # Apply move and track gems before application
    gems_before = sum(game_state.player_gems[current_player].values())
    game_state.apply_action(action)
    gems_after = sum(game_state.player_gems[current_player].values())
    
    # Calculate gems returned (if over 10 limit)
    gems_returned = max(0, gems_before - gems_after) if gems_after <= 10 else 0
    
    # For Basic Agent: Run MCTS Critic to evaluate the state after their move
    if isinstance(agent, BasicAgent):
        # Get the MCTS agent (assumed to be agents[1])
        mcts_critic = agents[1] if isinstance(agents[1], MCTSAgent) else None
        
        if mcts_critic:
            # Run brief MCTS evaluation from current player's perspective
            critic_result = mcts_critic.evaluate_state_as_critic(
                game_state, 
                target_player=current_player, 
                simulations=50
            )
            win_probability = critic_result.get('win_probability', 0.5)
            print(f"    [MCTS Critic] Win probability for P{current_player + 1}: {win_probability:.2f}")
    
    # Count cards owned by tier
    cards_by_tier = [0, 0, 0]  # Tier 1, 2, 3
    for card in game_state.player_cards[current_player]:
        if card.tier in [1, 2, 3]:
            cards_by_tier[card.tier - 1] += 1
    
    # Count nobles owned
    nobles_owned = len(game_state.player_nobles[current_player])
    
    # Create deep dive log entry
    log_entry = {
        'turn_number': game_state.turn_number,
        'active_player': current_player,
        'player_type': agent_type,
        'cards_owned_by_tier': cards_by_tier,
        'nobles_owned': nobles_owned,
        'gems_returned': gems_returned,
        'win_probability': win_probability,
        'search_depth': search_depth,
        'simulation_count': simulation_count,
        'visit_distribution': visit_distribution,
        'player_points': game_state.player_points[current_player],
        'action_type': action.type,
        'duration_ms': duration_ms,
        # Move Accuracy Metrics
        'is_best_move': accuracy_data.get('is_best_move', False) if accuracy_data else None,
        'best_win_prob': accuracy_data.get('best_win_prob', 0) if accuracy_data else None,
        'actual_win_prob': accuracy_data.get('actual_win_prob', 0) if accuracy_data else None,
        'accuracy_loss': accuracy_data.get('accuracy_loss', 0) if accuracy_data else None,
        'move_classification': accuracy_data.get('move_classification', 'Unknown') if accuracy_data else None,
        'best_action': accuracy_data.get('best_action', '') if accuracy_data else None
    }
    
    # Add to game_log
    if hasattr(recorder, 'game_log'):
        recorder.game_log.append(log_entry)
    else:
        recorder.game_log = [log_entry]


def handle_game_over(game_state: GameState, agents, window: GameWindow,
                    recorder: GameRecorder):
    """
    Handle game over: show results and run analytics.
    
    Args:
        game_state: Final game state
        agents: List of agents
        window: Game window
        recorder: Move recorder
    """
    winner = game_state.winner
    final_scores = {i: game_state.player_points[i] for i in range(game_state.num_players)}
    
    # Finalize recording
    recorder.finalize_game(winner, final_scores)
    
    # Log results
    window.logger.add_log("---")
    window.logger.add_log("GAME OVER!")
    window.logger.add_log(f"Winner: Player {winner + 1} ({agents[winner].name})")
    
    for i, score in final_scores.items():
        window.logger.add_log(f"  P{i + 1}: {score} points")
    
    # Print to console
    print("\n" + "="*60)
    print("GAME OVER!")
    print(f"Winner: Player {winner + 1} ({agents[winner].name})")
    print(f"Final Scores:")
    for i, score in final_scores.items():
        window.logger.add_log(f"  Player {i + 1}: {score} points")
    print("="*60)
    
    # Save individual logs
    json_path = recorder.save_json()
    csv_path = recorder.save_csv()
    
    # Save to master games file in data/games.json
    import json
    from pathlib import Path
    
    master_file = Path("data/games.json")
    master_file.parent.mkdir(parents=True, exist_ok=True)
    
    game_data = {
        'game_id': recorder.game_id,
        'metadata': recorder.game_metadata,
        'moves': [move.to_dict() for move in recorder.moves],
        'game_log': recorder.game_log
    }
    
    try:
        games_list = []
        if master_file.exists():
            with open(master_file, 'r') as f:
                try:
                    games_list = json.load(f)
                except json.JSONDecodeError:
                    games_list = []
        
        games_list.append(game_data)
        
        with open(master_file, 'w') as f:
            json.dump(games_list, f, indent=2)
            
        print(f"\nGame saved to master file: {master_file}")
    except Exception as e:
        print(f"\n⚠ Failed to save to master games file: {e}")
        
    print(f"Game logs also saved individually to:")
    print(f"  JSON: {json_path}")
    print(f"  CSV: {csv_path}")
    
    # Run analytics for BOTH players
    print("\n" + "="*60)
    print("Running Post-Game Analytics...")
    print("="*60)
    
    window.logger.add_log("---")
    window.logger.add_log("Analyzing game...")
    
    # Calculate comprehensive statistics from game_log
    game_log = recorder.game_log if hasattr(recorder, 'game_log') else []
    
    if game_log:
        # Separate by player
        p1_turns = [t for t in game_log if t['active_player'] == 0]
        p2_turns = [t for t in game_log if t['active_player'] == 1]
        
        # === PERFORMANCE SUMMARY ===
        print("\n" + "─" * 60)
        print("PERFORMANCE SUMMARY")
        print("─" * 60)
        
        if p1_turns and p2_turns:
            import numpy as np
            
            p1_probs = [t['win_probability'] for t in p1_turns if t.get('win_probability') is not None]
            p2_probs = [t['win_probability'] for t in p2_turns if t.get('win_probability') is not None]
            
            if p1_probs and p2_probs:
                p1_avg = np.mean(p1_probs)
                p2_avg = np.mean(p2_probs)
                p1_final = p1_probs[-1] if p1_probs else 0
                p2_final = p2_probs[-1] if p2_probs else 0
                
                print(f"Heuristic Agent:")
                print(f"  Average Win Probability: {p1_avg:.1%}")
                print(f"  Final Win Probability:   {p1_final:.1%}")
                print(f"\nMCTS Agent:")
                print(f"  Average Win Probability: {p2_avg:.1%}")
                print(f"  Final Win Probability:   {p2_final:.1%}")
                print(f"\nAdvantage: {abs(p2_avg - p1_avg):.1%} (MCTS)")
        
        # === ACCURACY SUMMARY ===
        has_accuracy = any(t.get('move_classification') is not None for t in game_log)
        if has_accuracy:
            print("\n" + "─" * 60)
            print("ACCURACY SUMMARY")
            print("─" * 60)
            
            p1_classifications = [t.get('move_classification', 'Unknown') for t in p1_turns]
            p2_classifications = [t.get('move_classification', 'Unknown') for t in p2_turns]
            
            p1_best = p1_classifications.count('Best')
            p1_inaccuracy = p1_classifications.count('Inaccuracy')
            p1_mistake = p1_classifications.count('Mistake')
            p1_blunder = p1_classifications.count('Blunder')
            p1_total = len(p1_turns)
            
            p2_best = p2_classifications.count('Best')
            p2_inaccuracy = p2_classifications.count('Inaccuracy')
            p2_mistake = p2_classifications.count('Mistake')
            p2_blunder = p2_classifications.count('Blunder')
            p2_total = len(p2_turns)
            
            p1_losses = [t.get('accuracy_loss', 0) for t in p1_turns if t.get('accuracy_loss') is not None]
            p2_losses = [t.get('accuracy_loss', 0) for t in p2_turns if t.get('accuracy_loss') is not None]
            
            import numpy as np
            p1_avg_loss = np.mean(p1_losses) if p1_losses else 0
            p2_avg_loss = np.mean(p2_losses) if p2_losses else 0
            
            # Calculate accuracy score
            def calc_accuracy_score(best, inaccuracy, mistake, blunder, total):
                if total == 0:
                    return 0
                return (best * 100 + inaccuracy * 90 + mistake * 70 + blunder * 40) / total
            
            p1_accuracy = calc_accuracy_score(p1_best, p1_inaccuracy, p1_mistake, p1_blunder, p1_total)
            p2_accuracy = calc_accuracy_score(p2_best, p2_inaccuracy, p2_mistake, p2_blunder, p2_total)
            
            print(f"Player 1 (Heuristic):")
            print(f"  Best:       {p1_best}/{p1_total} ({p1_best/p1_total*100:.0f}%)")
            print(f"  Inaccuracy: {p1_inaccuracy}/{p1_total} ({p1_inaccuracy/p1_total*100:.0f}%)")
            print(f"  Mistake:    {p1_mistake}/{p1_total} ({p1_mistake/p1_total*100:.0f}%)")
            print(f"  Blunder:    {p1_blunder}/{p1_total} ({p1_blunder/p1_total*100:.0f}%)")
            print(f"  Avg Loss:   {p1_avg_loss*100:.1f}%")
            print(f"  Accuracy:   {p1_accuracy:.1f}/100")
            
            print(f"\nPlayer 2 (MCTS):")
            print(f"  Best:       {p2_best}/{p2_total} ({p2_best/p2_total*100:.0f}%)")
            print(f"  Inaccuracy: {p2_inaccuracy}/{p2_total} ({p2_inaccuracy/p2_total*100:.0f}%)")
            print(f"  Mistake:    {p2_mistake}/{p2_total} ({p2_mistake/p2_total*100:.0f}%)")
            print(f"  Blunder:    {p2_blunder}/{p2_total} ({p2_blunder/p2_total*100:.0f}%)")
            print(f"  Avg Loss:   {p2_avg_loss*100:.1f}%")
            print(f"  Accuracy:   {p2_accuracy:.1f}/100")
            
            print(f"\nDifference: {abs(p2_accuracy - p1_accuracy):.1f} pts")
        
        # === STRATEGY ANALYSIS ===
        print("\n" + "─" * 60)
        print("STRATEGY ANALYSIS")
        print("─" * 60)
        
        p1_final_cards = p1_turns[-1]['cards_owned_by_tier'] if p1_turns else [0, 0, 0]
        p2_final_cards = p2_turns[-1]['cards_owned_by_tier'] if p2_turns else [0, 0, 0]
        
        p1_tier1, p1_tier2, p1_tier3 = p1_final_cards
        p2_tier1, p2_tier2, p2_tier3 = p2_final_cards
        
        p1_total_cards = sum(p1_final_cards)
        p2_total_cards = sum(p2_final_cards)
        
        print(f"Heuristic Agent:")
        print(f"  Tier 1: {p1_tier1}/{p1_total_cards} ({p1_tier1/p1_total_cards*100:.0f}% Entry cards)" if p1_total_cards > 0 else "  Tier 1: 0")
        print(f"  Tier 2: {p1_tier2}/{p1_total_cards} ({p1_tier2/p1_total_cards*100:.0f}% Mid-tier)" if p1_total_cards > 0 else "  Tier 2: 0")
        print(f"  Tier 3: {p1_tier3}/{p1_total_cards} ({p1_tier3/p1_total_cards*100:.0f}% Premium)" if p1_total_cards > 0 else "  Tier 3: 0")
        
        print(f"\nMCTS Agent:")
        print(f"  Tier 1: {p2_tier1}/{p2_total_cards} ({p2_tier1/p2_total_cards*100:.0f}% Entry cards)" if p2_total_cards > 0 else "  Tier 1: 0")
        print(f"  Tier 2: {p2_tier2}/{p2_total_cards} ({p2_tier2/p2_total_cards*100:.0f}% Mid-tier)" if p2_total_cards > 0 else "  Tier 2: 0")
        print(f"  Tier 3: {p2_tier3}/{p2_total_cards} ({p2_tier3/p2_total_cards*100:.0f}% Premium)" if p2_total_cards > 0 else "  Tier 3: 0")
        
        # === COMPUTATIONAL EFFORT ===
        print("\n" + "─" * 60)
        print("COMPUTATIONAL EFFORT (MCTS Agent)")
        print("─" * 60)
        
        p2_sims = [t.get('simulation_count', 0) for t in p2_turns]
        p2_depths = [t.get('search_depth', 0) for t in p2_turns]
        
        if p2_sims and p2_depths:
            import numpy as np
            avg_sims = np.mean(p2_sims)
            max_sims = max(p2_sims)
            avg_depth = np.mean(p2_depths)
            max_depth = max(p2_depths)
            
            print(f"Simulations:")
            print(f"  Average:  {avg_sims:.0f}")
            print(f"  Peak:     {max_sims:.0f}")
            print(f"\nSearch Depth:")
            print(f"  Average:  {avg_depth:.1f}")
            print(f"  Maximum:  {max_depth}")
    
    print("\n" + "="*60)
    
    # Auto-generate all visualizations
    print("="*60)
    print("Auto-Generating Visualizations...")
    print("="*60)
    
    # Create unique folder for this game's visualizations
    from datetime import datetime
    date_folder = Path('data/Games')
    date_folder.mkdir(parents=True, exist_ok=True)
    game_count = len([d for d in date_folder.iterdir() if d.is_dir()]) + 1
    game_folder = date_folder / f'game_{game_count}'
    game_folder.mkdir(parents=True, exist_ok=True)
    print(f"\nSaving visualizations to: {game_folder}/")
    
    # Import and run visualization functions
    try:
        from generate_comparison_visuals import (
            visual_1_battle_of_confidence,
            visual_2_thinking_effort,
            visual_3_strategy_dna
        )
        from plot_move_accuracy import plot_accuracy_strip_chart
        
        game_log = recorder.game_log if hasattr(recorder, 'game_log') else []
        
        if game_log:
            print("\nGenerating comparison visuals...")
            try:
                visual_1_battle_of_confidence(game_log, output_path=str(game_folder / 'visual_1_battle_of_confidence.png'))
            except Exception as e:
                print(f"  ⚠ Visual 1 skipped: {e}")
            
            try:
                visual_2_thinking_effort(game_log, output_path=str(game_folder / 'visual_2_thinking_effort.png'))
            except Exception as e:
                print(f"  ⚠ Visual 2 skipped: {e}")
            
            try:
                visual_3_strategy_dna(game_log, output_path=str(game_folder / 'visual_3_strategy_dna.png'))
            except Exception as e:
                print(f"  ⚠ Visual 3 skipped: {e}")
            
            # Check if accuracy data exists
            has_accuracy = any(t.get('move_classification') is not None for t in game_log)
            if has_accuracy:
                print("\nGenerating move accuracy plot...")
                try:
                    plot_accuracy_strip_chart(game_log, output_path=str(game_folder / 'move_accuracy_strip_plot.png'))
                except Exception as e:
                    print(f"  ⚠ Accuracy plot skipped: {e}")
            else:
                print("\n⚠ Skipping accuracy plot (no accuracy data)")
            
            # Generate MCTS tree visualization from captured snapshot
            print("\nGenerating MCTS tree visualization...")
            try:
                # Check if we captured a tree snapshot during gameplay
                if hasattr(recorder, 'mcts_tree_snapshot') and recorder.mcts_tree_snapshot:
                    from pyvis.network import Network
                    import json
                    from datetime import datetime
                    
                    # Find MCTS agent for export
                    mcts_agent = None
                    for agent in agents:
                        if isinstance(agent, MCTSAgent):
                            mcts_agent = agent
                            break
                    
                    if mcts_agent:
                        print(f"  Using captured tree from turn {recorder.mcts_tree_turn}")
                        
                        # Export the captured tree
                        tree_data = mcts_agent.export_tree_structure(
                            root_node=recorder.mcts_tree_snapshot,
                            max_depth=4,
                            top_k=4,
                            turn_number=recorder.mcts_tree_turn
                        )
                        
                        print(f"  Nodes: {len(tree_data['nodes'])}, Edges: {len(tree_data['edges'])}")
                        
                        # Create visualization
                        net = Network(
                            height='900px',
                            width='100%',
                            bgcolor='#222222',
                            font_color='white',
                            directed=True
                        )
                        
                        net.set_options("""
                        {
                            "physics": {
                                "enabled": true,
                                "barnesHut": {
                                    "gravitationalConstant": -8000,
                                    "centralGravity": 0.3,
                                    "springLength": 150,
                                    "springConstant": 0.04,
                                    "damping": 0.09
                                }
                            },
                            "layout": {
                                "hierarchical": {
                                    "enabled": true,
                                    "direction": "UD",
                                    "sortMethod": "directed",
                                    "levelSeparation": 150
                                }
                            },
                            "interaction": {
                                "navigationButtons": true,
                                "keyboard": true
                            }
                        }
                        """)
                        
                        # Add nodes and edges
                        for node in tree_data['nodes']:
                            net.add_node(
                                node['id'],
                                label=node['label'],
                                color=node['color'],
                                borderWidth=node.get('borderWidth', 2),
                                size=node['size'],
                                title=node['title']
                            )
                        
                        for edge in tree_data['edges']:
                            net.add_edge(
                                edge['from'], 
                                edge['to'], 
                                width=edge.get('width', 2),
                                color=edge.get('color', '#848484'),
                                arrows=edge.get('arrows', 'to'),
                                dashes=edge.get('dashes', False),
                                smooth=edge.get('smooth', {'type': 'curvedCW'})
                            )
                        
                        # Save HTML
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        html_filename = f"mcts_brain_{timestamp}.html"
                        html_filepath = game_folder / html_filename
                        net.save_graph(str(html_filepath))
                        
                        # Save JSON
                        json_filename = f"mcts_tree_{timestamp}.json"
                        json_filepath = game_folder / json_filename
                        with open(json_filepath, 'w') as f:
                            json.dump({
                                'turn_captured': recorder.mcts_tree_turn,
                                'tree_data': tree_data
                            }, f, indent=2)
                        
                        print(f"  [OK] Tree HTML: {html_filename}")
                        print(f"  [OK] Tree JSON: {json_filename}")
                    else:
                        print("  ⚠ No MCTS agent found")
                else:
                    print("  ⚠ No tree snapshot captured during gameplay")
                    print("     (Tree is captured during turns 10-15)")
            except Exception as e:
                print(f"  ⚠ Tree visualization skipped: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n" + "="*60)
            print(f"All visualizations saved to: {game_folder}/")
            print("="*60)
            
            # ===== NEW: Generate Comprehensive Post-Game Analytics =====
            print("\n" + "="*60)
            print("Generating Comprehensive Analytics Package...")
            print("="*60)
            
            try:
                analytics = PostGameAnalytics(str(game_folder))
                analytics.generate_all_visualizations()
            except Exception as e:
                print(f"❌ Comprehensive analytics failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("⚠ No game_log data available for visualizations")
            
        # Save MCTS Knowledge Base for persistent learning
        for agent in agents:
            if hasattr(agent, "kb") and hasattr(agent.kb, "save"):
                try:
                    agent.kb.save()
                    print(f"  [OK] Saved knowledge base for agent {agent.name}")
                except Exception as e:
                    print(f"  ⚠ Failed to save knowledge base for {agent.name}: {e}")
    
    except Exception as e:
        print(f"⚠ Visualization generation failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60 + "\n")
    
    # Stop auto-play
    window.auto_play = False


if __name__ == "__main__":
    run_game()
