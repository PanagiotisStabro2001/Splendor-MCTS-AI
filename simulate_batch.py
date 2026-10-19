import os
import sys
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use('Agg')

from game_engine.state import GameState
from agents.basic import BasicAgent
from agents.advanced import MCTSAgent
from analytics.recorder import GameRecorder

from main import hash_state, calculate_move_accuracy
from generate_comparison_visuals import (
    visual_1_battle_of_confidence,
    visual_2_thinking_effort,
    visual_3_strategy_dna
)
from plot_move_accuracy import plot_accuracy_strip_chart

def simulate_game(game_index: int, total_games: int):
    print(f"\n{'='*40}\nStarting Game {game_index}/{total_games}\n{'='*40}")
    game_state = GameState(num_players=2)
    
    # Initialize agents
    agents = [
        BasicAgent(player_id=0),
        MCTSAgent(player_id=1, time_limit=3.0) # Increased limit for stronger play
    ]
    
    recorder = GameRecorder(game_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{game_index}")
    recorder.game_log = []
    
    while not game_state.game_over:
        current_player = game_state.current_player
        agent = agents[current_player]
        mcts_engine = agents[1]
        
        start_time = time.time()
        
        if isinstance(agent, MCTSAgent):
            action, mcts_metadata = agent.get_move(game_state)
            win_probability = mcts_metadata.get('win_probability', 0.5)
            search_depth = mcts_metadata.get('search_depth', 0)
            simulation_count = mcts_metadata.get('simulation_count', 0)
            visit_distribution = mcts_metadata.get('visit_distribution', [])
        else:
            action = agent.select_move(game_state)
            win_probability = None
            search_depth = 0
            simulation_count = 0
            visit_distribution = []
            
        duration_ms = (time.time() - start_time) * 1000
        
        # Accuracy Engine
        accuracy_data = None
        if mcts_engine:
            accuracy_data = calculate_move_accuracy(game_state, current_player, action, mcts_engine)
            
        # Record move
        recorder.record_move(
            turn_id=game_state.turn_number,
            player_id=current_player,
            player_type="MCTS" if isinstance(agent, MCTSAgent) else "Basic",
            action=action,
            state_hash=hash_state(game_state),
            duration_ms=duration_ms
        )
        
        # Gems check
        gems_before = sum(game_state.player_gems[current_player].values())
        game_state.apply_action(action)
        gems_after = sum(game_state.player_gems[current_player].values())
        gems_returned = max(0, gems_before - gems_after) if gems_after <= 10 else 0
        
        # MCTS Critic for Basic agent
        if isinstance(agent, BasicAgent):
            critic_result = mcts_engine.evaluate_state_as_critic(
                game_state, target_player=current_player, simulations=50)
            win_probability = critic_result.get('win_probability', 0.5)
            
        # Log deep metrics
        cards_by_tier = [0, 0, 0]
        for card in game_state.player_cards[current_player]:
            if card.tier in [1, 2, 3]:
                cards_by_tier[card.tier - 1] += 1
                
        log_entry = {
            'turn_number': game_state.turn_number,
            'active_player': current_player,
            'player_type': "MCTS" if isinstance(agent, MCTSAgent) else "Basic",
            'cards_owned_by_tier': cards_by_tier,
            'nobles_owned': len(game_state.player_nobles[current_player]),
            'gems_returned': gems_returned,
            'win_probability': win_probability,
            'search_depth': search_depth,
            'simulation_count': simulation_count,
            'visit_distribution': visit_distribution,
            'player_points': game_state.player_points[current_player],
            'action_type': action.type,
            'duration_ms': duration_ms,
            'is_best_move': accuracy_data.get('is_best_move', False) if accuracy_data else None,
            'best_win_prob': accuracy_data.get('best_win_prob', 0) if accuracy_data else None,
            'actual_win_prob': accuracy_data.get('actual_win_prob', 0) if accuracy_data else None,
            'accuracy_loss': accuracy_data.get('accuracy_loss', 0) if accuracy_data else None,
            'move_classification': accuracy_data.get('move_classification', 'Unknown') if accuracy_data else None
        }
        recorder.game_log.append(log_entry)
        
        print(f"Turn {game_state.turn_number} - P{current_player+1} - {action.type}")

    # Game Over
    winner_id = -1
    max_points = -1
    for pid, points in enumerate(game_state.player_points):
        if points >= 15 and points > max_points:
            winner_id = pid
            max_points = points
            
    final_scores = {pid: points for pid, points in enumerate(game_state.player_points)}
    recorder.finalize_game(winner_id, final_scores)
    
    print(f"Game Over! Winner: Player {winner_id + 1} with {max_points} points.")
    
    # 1. Create Game Folder
    date_folder = Path("data/Games")
    date_folder.mkdir(parents=True, exist_ok=True)
    game_count = len([d for d in date_folder.iterdir() if d.is_dir()]) + 1
    game_folder = date_folder / f"game_{game_count}"
    game_folder.mkdir(parents=True, exist_ok=True)
    
    # 2. Generate Graphics
    print("Generating Analytics Graphics...")
    try:
        visual_1_battle_of_confidence(recorder.game_log, str(game_folder / 'visual_1_battle_of_confidence.png'))
        visual_2_thinking_effort(recorder.game_log, str(game_folder / 'visual_2_thinking_effort.png'))
        visual_3_strategy_dna(recorder.game_log, str(game_folder / 'visual_3_strategy_dna.png'))
        plot_accuracy_strip_chart(recorder.game_log, str(game_folder / 'move_accuracy_strip_plot.png'))
    except Exception as e:
        print(f"Failed to generate a graphic: {e}")
        
    # 3. Save JSON and append to master
    recorder.save_json(str(game_folder))
    
    master_file = Path("data/games.json")
    game_data = {
        'game_id': recorder.game_id,
        'date': datetime.now().strftime("%Y-%m-%d"),
        'metadata': recorder.game_metadata,
        'mcts_kb_size': len(agents[1].kb.memory) if hasattr(agents[1], 'kb') else 0
    }
    
    try:
        games_list = []
        if master_file.exists():
            with open(master_file, 'r') as f:
                games_list = json.load(f)
        games_list.append(game_data)
        with open(master_file, 'w') as f:
            json.dump(games_list, f, indent=2)
    except Exception as e:
        print(f"Failed to update games.json: {e}")
        
    # 4. Save Knowledge Base
    for agent in agents:
        if hasattr(agent, "kb") and hasattr(agent.kb, "save"):
            agent.kb.save()
            print(f"Saved KB for {agent.name}, current size: {len(agent.kb.memory)}")

def main():
    parser = argparse.ArgumentParser(description="Headless batch simulator for MCTS Splendor AI.")
    parser.add_argument("--games", type=int, default=50, help="Number of games to simulate")
    args = parser.parse_args()
    
    print(f"Simulating {args.games} games...")
    for i in range(1, args.games + 1):
        simulate_game(i, args.games)

if __name__ == "__main__":
    main()
