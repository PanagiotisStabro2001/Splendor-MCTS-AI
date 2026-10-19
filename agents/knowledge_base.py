import json
import os
from typing import Dict, Any

class MCTSKnowledgeBase:
    """
    Manages persistent learning for the MCTS AI.
    Loads and saves node evaluations (visits, value) mapped to game states.
    """
    def __init__(self, filepath: str = "data/mcts_knowledge.json"):
        self.filepath = filepath
        self.memory: Dict[str, Dict[str, Dict[str, float]]] = {}
        # Format: { state_hash: { action_hash: {"visits": float, "value": float} } }
        self.dirty = False
        self.load()

    def load(self):
        """Load the knowledge base from disk."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
                print(f"Loaded MCTS knowledge base from {self.filepath} ({len(self.memory)} states).")
            except Exception as e:
                print(f"Error loading MCTS knowledge base: {e}")
                self.memory = {}
        elif os.path.exists(self.filepath.replace(".json", ".zip")):
            zip_path = self.filepath.replace(".json", ".zip")
            try:
                import zipfile
                with zipfile.ZipFile(zip_path, "r") as zf:
                    with zf.open("mcts_knowledge.json") as f:
                        self.memory = json.load(f)
                print(f"Loaded MCTS knowledge base from zip {zip_path} ({len(self.memory)} states).")
            except Exception as e:
                print(f"Error loading MCTS knowledge base from zip: {e}")
                self.memory = {}
        else:
            self.memory = {}
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def save(self):
        """Save the knowledge base to disk if there are changes."""
        if self.dirty:
            try:
                # We could periodically clean up old/low-visit states if memory grows too large,
                # but we'll save everything for now.
                with open(self.filepath, "w", encoding="utf-8") as f:
                    json.dump(self.memory, f)
                print(f"Saved MCTS knowledge base to {self.filepath} ({len(self.memory)} states).")
                self.dirty = False
            except Exception as e:
                print(f"Error saving MCTS knowledge base: {e}")

    def update_node(self, state_hash: str, action_hash: str, visits: float, value: float):
        """Update or insert statistics for a specific state-action pair."""
        if state_hash not in self.memory:
            self.memory[state_hash] = {}
        
        if action_hash not in self.memory[state_hash]:
            self.memory[state_hash][action_hash] = {"visits": visits, "value": value}
        else:
            # We take the maximum visits instead of appending to avoid compounding if the state is revisited in a single run
            # Or we could replace it entirely since MCTS backpropagation naturally accumulates.
            self.memory[state_hash][action_hash]["visits"] = max(visits, self.memory[state_hash][action_hash]["visits"])
            self.memory[state_hash][action_hash]["value"] = value
            
        self.dirty = True

    def get_stats(self, state_hash: str, action_hash: str) -> Dict[str, float]:
        """Retrieve statistics for a specific state-action pair, if available."""
        if state_hash in self.memory and action_hash in self.memory[state_hash]:
            return self.memory[state_hash][action_hash]
        return None
