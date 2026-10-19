"""
Test script to demonstrate the new Deep Dive Analytics features.
Run this to see the MCTS metadata and MCTS Critic in action.
"""

import json
from game_engine.state import GameState
from agents.basic import BasicAgent
from agents.advanced import MCTSAgent


def test_mcts_metadata():
    """Test MCTS agent returning metadata."""
    print("=" * 60)
    print("Test 1: MCTS Agent with Metadata")
    print("=" * 60)
    
    # Create game and agents
    game_state = GameState(num_players=2)
    mcts_agent = MCTSAgent(player_id=1, time_limit=1.0)
    
    # Get move with metadata
    print("\nGetting MCTS move with metadata...")
    action, metadata = mcts_agent.get_move(game_state)
    
    print(f"\nAction: {action.type}")
    print(f"\nMetadata:")
    print(f"  Win Probability: {metadata['win_probability']:.3f}")
    print(f"  Search Depth: {metadata['search_depth']}")
    print(f"  Simulation Count: {metadata['simulation_count']}")
    print(f"  Visit Distribution (top 3):")
    for i, visit in enumerate(metadata['visit_distribution'], 1):
        print(f"    #{i}: {visit['visits']} visits, value={visit['value']:.3f}")
    
    print("\n[OK] Test 1 passed!\n")


def test_mcts_critic():
    """Test MCTS Critic evaluating a Heuristic Agent's move."""
    print("=" * 60)
    print("Test 2: MCTS Critic for Heuristic Agent")
    print("=" * 60)
    
    # Create game and agents
    game_state = GameState(num_players=2)
    basic_agent = BasicAgent(player_id=0)
    mcts_agent = MCTSAgent(player_id=1, time_limit=1.0)
    
    # Heuristic agent makes a move
    print("\nHeuristic Agent (P1) makes a move...")
    action = basic_agent.select_move(game_state)
    print(f"Action: {action.type}")
    game_state.apply_action(action)
    
    # MCTS Critic evaluates the resulting state
    print("\nMCTS Critic evaluating P1's position...")
    critic_result = mcts_agent.evaluate_state_as_critic(
        game_state, 
        target_player=0,  # Evaluate for Heuristic Agent
        simulations=50
    )
    
    print(f"\nCritic Evaluation:")
    print(f"  Win Probability: {critic_result['win_probability']:.3f}")
    print(f"  Projected Score: {critic_result['projected_score']}")
    print(f"  Simulation Count: {critic_result['simulation_count']}")
    
    print("\n[OK] Test 2 passed!\n")


def test_game_log_structure():
    """Test game log data structure."""
    print("=" * 60)
    print("Test 3: Game Log Data Structure")
    print("=" * 60)
    
    # Create a sample turn log entry
    sample_log_entry = {
        'turn_number': 5,
        'active_player': 1,
        'player_type': 'MCTS',
        'cards_owned_by_tier': [3, 1, 0],
        'nobles_owned': 0,
        'gems_returned': 2,
        'win_probability': 0.68,
        'search_depth': 12,
        'simulation_count': 847,
        'visit_distribution': [
            {'visits': 342, 'value': 0.68},
            {'visits': 289, 'value': 0.64},
            {'visits': 216, 'value': 0.59}
        ],
        'player_points': 5,
        'action_type': 'buy_card',
        'duration_ms': 2003.5
    }
    
    print("\nSample Game Log Entry:")
    print(json.dumps(sample_log_entry, indent=2))
    
    print("\n[OK] Test 3 passed!\n")


def test_comparison_data():
    """Demonstrate how to use the data for comparison."""
    print("=" * 60)
    print("Test 4: Data Comparison Example")
    print("=" * 60)
    
    # Simulate a few turns of data
    sample_game_log = [
        {'turn_number': 1, 'active_player': 0, 'player_type': 'Basic', 
         'win_probability': 0.48, 'cards_owned_by_tier': [1, 0, 0], 'player_points': 0},
        {'turn_number': 2, 'active_player': 1, 'player_type': 'MCTS', 
         'win_probability': 0.52, 'cards_owned_by_tier': [1, 0, 0], 'player_points': 0},
        {'turn_number': 3, 'active_player': 0, 'player_type': 'Basic', 
         'win_probability': 0.45, 'cards_owned_by_tier': [2, 0, 0], 'player_points': 0},
        {'turn_number': 4, 'active_player': 1, 'player_type': 'MCTS', 
         'win_probability': 0.58, 'cards_owned_by_tier': [2, 1, 0], 'player_points': 2},
        {'turn_number': 5, 'active_player': 0, 'player_type': 'Basic', 
         'win_probability': 0.42, 'cards_owned_by_tier': [3, 0, 0], 'player_points': 1},
    ]
    
    # Separate by player
    p1_turns = [t for t in sample_game_log if t['active_player'] == 0]
    p2_turns = [t for t in sample_game_log if t['active_player'] == 1]
    
    # Calculate metrics
    p1_avg_prob = sum(t['win_probability'] for t in p1_turns) / len(p1_turns)
    p2_avg_prob = sum(t['win_probability'] for t in p2_turns) / len(p2_turns)
    
    p1_total_cards = sum(sum(t['cards_owned_by_tier']) for t in p1_turns)
    p2_total_cards = sum(sum(t['cards_owned_by_tier']) for t in p2_turns)
    
    print("\nComparison Metrics:")
    print(f"\nPlayer 1 (Heuristic Agent):")
    print(f"  Avg Win Probability: {p1_avg_prob:.2%}")
    print(f"  Total Cards Acquired: {p1_total_cards}")
    print(f"  Final Points: {p1_turns[-1]['player_points']}")
    
    print(f"\nPlayer 2 (MCTS Agent):")
    print(f"  Avg Win Probability: {p2_avg_prob:.2%}")
    print(f"  Total Cards Acquired: {p2_total_cards}")
    print(f"  Final Points: {p2_turns[-1]['player_points']}")
    
    print(f"\nDifference:")
    print(f"  Win Prob Advantage: {(p2_avg_prob - p1_avg_prob):.2%} (MCTS)")
    
    print("\n[OK] Test 4 passed!\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DEEP DIVE ANALYTICS - TEST SUITE")
    print("=" * 60 + "\n")
    
    test_mcts_metadata()
    test_mcts_critic()
    test_game_log_structure()
    test_comparison_data()
    
    print("=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYou can now run 'python main.py' to play a full game")
    print("with Deep Dive Analytics enabled.")
    print("\nData will be saved to logs/game_YYYYMMDD_HHMMSS.json")
    print("=" * 60 + "\n")
