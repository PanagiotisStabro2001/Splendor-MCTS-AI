import os
from game_engine.state import GameState
from agents.advanced import MCTSAgent

def test_persistent_learning():
    print("Testing MCTS Knowledge Base integration...")
    
    # 1. Initialize Game State
    state = GameState(num_players=2)
    
    # 2. Initialize Agent (will load KB if exists)
    # Use small time_limit for test
    agent = MCTSAgent(player_id=1, time_limit=1.0)
    print(f"Agent loaded KB with {len(agent.kb.memory)} states.")
    
    # 3. Request a move
    print("Agent thinking...")
    action, meta = agent.get_move(state)
    print(f"Agent chose action: {action}")
    print(f"Agent explored {meta['simulation_count']} simulations.")
    
    # 4. Save KB
    agent.kb.save()
    
    # 5. Check if file exists and has size
    kb_path = "data/mcts_knowledge.json"
    if os.path.exists(kb_path):
        size = os.path.getsize(kb_path)
        print(f"SUCCESS: KB file created at {kb_path} (size: {size} bytes)")
    else:
        print("ERROR: KB file not created!")

if __name__ == "__main__":
    test_persistent_learning()
