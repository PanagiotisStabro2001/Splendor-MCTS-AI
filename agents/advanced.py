"""
Advanced AI agent using Monte Carlo Tree Search (MCTS).
"""

import math
import random
import time
from typing import List, Optional
from game_engine.state import GameState
from game_engine.components import Action, GemType, TAKE_3_DIFFERENT
from agents.knowledge_base import MCTSKnowledgeBase


class MCTSNode:
    """Node in the MCTS tree."""
    
    def __init__(self, state: GameState, parent: Optional['MCTSNode'] = None, 
                 action: Optional[Action] = None, kb: Optional[MCTSKnowledgeBase] = None):
        self.state = state
        self.parent = parent
        self.action = action  # Action that led to this state
        self.kb = kb
        
        self.children: List['MCTSNode'] = []
        self.visits = 0
        self.value = 0.0
        
        # Load persistent knowledge if available
        if self.kb and self.parent and self.action:
            parent_hash = self.parent.state.get_hash()
            action_hash = self.action.get_hash()
            stats = self.kb.get_stats(parent_hash, action_hash)
            if stats:
                self.visits = stats["visits"]
                self.value = stats["value"]
                
        legal_actions = state.get_legal_actions(state.current_player)
        self.untried_actions: List[Action] = self._prune_actions(state, legal_actions)
        
    def _prune_actions(self, state: GameState, actions: List[Action]) -> List[Action]:
        """Prune obviously bad actions to reduce branching factor and deepen MCTS search."""
        player_id = state.current_player
        total_gems = sum(state.player_gems[player_id].values())
        player_bonuses = sum(state.player_bonuses[player_id].values())
        
        buy_actions = [a for a in actions if a.type == "buy_card"]
        
        pruned = []
        for action in actions:
            if action.type == "buy_card":
                pruned.append(action)
                
            elif action.type == "reserve_card":
                # Prune reserving if we are at 10 gems (random discard is bad)
                if total_gems >= 10:
                    continue
                # Prune reserving Tier 3 cards very early in the game
                card = action.data.get('card')
                if card and card.tier == 3 and player_bonuses < 3:
                    continue
                pruned.append(action)
                
            elif action.type in ["take_3_different", "take_2_same"]:
                # If we have 8+ gems and can buy a card, don't take 2 of the same gem (often clogs hand)
                if total_gems >= 8 and buy_actions and action.type == "take_2_same":
                    continue
                pruned.append(action)
                
        return pruned if pruned else actions
    
    def is_fully_expanded(self) -> bool:
        """Check if all actions have been tried."""
        return len(self.untried_actions) == 0
    
    def is_terminal(self) -> bool:
        """Check if this is a terminal game state."""
        return self.state.game_over
    
    def best_child(self, root_player_id: int, exploration_weight: float = 1.41) -> 'MCTSNode':
        """
        Select best child using perspective-aware UCB1 formula.
        Adaptive exploration based on visit count.
        
        Args:
            root_player_id: The root player's ID (to determine perspective)
            exploration_weight: Exploration parameter (√2 is theoretically optimal)
        
        Returns:
            Best child node
        """
        if not self.children:
            return None
        
        # Aggressive exploitation: strongly reduce exploration as we learn more
        adaptive_weight = exploration_weight
        if self.visits > 200:
            adaptive_weight *= 0.5  # Heavy exploitation when very well-explored
        elif self.visits > 100:
            adaptive_weight *= 0.6  # Strong exploitation
        elif self.visits > 50:
            adaptive_weight *= 0.75  # Moderate exploitation
        
        def ucb1(node: MCTSNode) -> float:
            if node.visits == 0:
                return float('inf')
            
            # Simplified robust UCB1: always from root player's perspective
            # Value already represents root player's win probability
            exploitation = node.value / node.visits
            
            exploration = adaptive_weight * math.sqrt(
                math.log(self.visits) / node.visits
            )
            return exploitation + exploration
        
        return max(self.children, key=ucb1)
    
    def expand(self) -> 'MCTSNode':
        """
        Expand tree by trying an untried action.
        Uses domain knowledge to prioritize promising actions.
        
        Returns:
            New child node
        """
        # Prioritize actions: buy high-value cards first
        if self.untried_actions:
            # Sort actions by heuristic value (descending)
            def action_priority(action: Action) -> float:
                """Heuristic to prioritize actions during expansion."""
                if action.type == "buy_card":
                    card = action.data.get('card')
                    if card:
                        # Strongly prioritize high-value cards
                        return card.points * 20 + card.tier * 5
                elif action.type == "reserve_card":
                    return 7  # Medium-high priority
                elif action.type == "take_3_different":
                    return 4  # Lower priority
                elif action.type == "take_2_same":
                    return 3  # Lowest priority
                return 1  # Default
            
            self.untried_actions.sort(key=action_priority, reverse=True)
            action = self.untried_actions.pop(0)  # Take best
        else:
            return self  # Should not happen
        
        # Apply action to get new state
        new_state = self.state.get_state_copy()
        new_state.apply_action(action)
        
        # Create child node
        child = MCTSNode(new_state, parent=self, action=action, kb=self.kb)
        self.children.append(child)
        
        return child
    
    def update(self, result: float):
        """
        Update node statistics.
        
        Args:
            result: Simulation result (0 to 1)
        """
        self.visits += 1
        self.value += result
    
    def backpropagate(self, result: float):
        """
        Backpropagate result up the tree.
        
        Args:
            result: Simulation result
        """
        self.update(result)
        if self.parent:
            self.parent.backpropagate(result)


class MCTSAgent:
    """
    Monte Carlo Tree Search agent for Splendor.
    
    Uses MCTS to simulate games and find the best move.
    Optimized to run in 2-3 seconds per turn.
    """
    
    def __init__(self, player_id: int, time_limit: float = 6.0):
        """
        Initialize MCTS agent.
        
        Args:
            player_id: This agent's player ID
            time_limit: Max time per move in seconds (6.0s for maximum strength)
        """
        self.player_id = player_id
        self.name = "MCTS"
        self.time_limit = time_limit
        self.simulations_per_move = 0  # Track for analytics
        self.kb = MCTSKnowledgeBase()
    
    def select_move(self, game_state: GameState) -> Action:
        """
        Select best move using MCTS (legacy method for compatibility).
        
        Args:
            game_state: Current game state
        
        Returns:
            Best action found
        """
        action, _ = self.get_move(game_state)
        return action
    
    def get_move(self, game_state: GameState, max_simulations: int = None):
        """
        Select best move using MCTS and return metadata.
        
        Args:
            game_state: Current game state
            max_simulations: Override time limit with fixed simulation count (for critic mode)
        
        Returns:
            Tuple of (best_action, metadata_dict)
        """
        legal_actions = game_state.get_legal_actions(self.player_id)
        
        if not legal_actions:
            # This should never happen with fallback moves
            print(f"WARNING: Player {self.player_id} has no legal moves!")
            # Emergency fallback - try to get ANY action
            return Action(TAKE_3_DIFFERENT, gems=[GemType.WHITE]), {}
        
        if len(legal_actions) == 1:
            return legal_actions[0], {
                'win_probability': 0.5,
                'search_depth': 0,
                'simulation_count': 0,
                'visit_distribution': []
            }
        
        # Run MCTS
        root = MCTSNode(game_state.get_state_copy(), kb=self.kb)
        
        start_time = time.time()
        simulations = 0
        max_depth = 0
        
        # Time-based or simulation-based limit
        if max_simulations is not None:
            # Fixed simulation count (for critic mode)
            while simulations < max_simulations:
                node = self._select(root, self.player_id)
                depth = self._get_node_depth(node)
                max_depth = max(max_depth, depth)
                result = self._simulate(node.state)
                node.backpropagate(result)
                simulations += 1
        else:
            # Time-based limit (normal mode)
            while time.time() - start_time < self.time_limit:
                node = self._select(root, self.player_id)
                depth = self._get_node_depth(node)
                max_depth = max(max_depth, depth)
                result = self._simulate(node.state)
                node.backpropagate(result)
                simulations += 1
        
        self.simulations_per_move = simulations
        
        # Return best action with metadata
        if not root.children:
            # Fallback if MCTS failed
            return legal_actions[0], {
                'win_probability': 0.5,
                'search_depth': 0,
                'simulation_count': simulations,
                'visit_distribution': []
            }
        
        best_child = max(root.children, key=lambda c: c.visits)
        
        # Calculate win probability from best child
        win_probability = best_child.value / best_child.visits if best_child.visits > 0 else 0.5
        
        # Get top 3 moves by visit count
        sorted_children = sorted(root.children, key=lambda c: c.visits, reverse=True)[:3]
        visit_distribution = [
            {'visits': child.visits, 'value': child.value / child.visits if child.visits > 0 else 0}
            for child in sorted_children
        ]
        
        metadata = {
            'win_probability': win_probability,
            'search_depth': max_depth,
            'simulation_count': simulations,
            'visit_distribution': visit_distribution
        }
        
        # Update Knowledge Base at the end of the search
        self._save_tree_to_kb(root)
        
        return best_child.action, metadata
        
    def _save_tree_to_kb(self, node: MCTSNode):
        """Recursively save visited nodes into the Knowledge Base."""
        if node.visits < 5:  # Only save reasonably explored nodes to save space
            return
            
        if node.parent and node.action:
            parent_hash = node.parent.state.get_hash()
            action_hash = node.action.get_hash()
            self.kb.update_node(parent_hash, action_hash, node.visits, node.value)
            
        for child in node.children:
            self._save_tree_to_kb(child)
    
    def _get_node_depth(self, node: MCTSNode) -> int:
        """
        Calculate depth of a node in the tree.
        
        Args:
            node: Node to measure
        
        Returns:
            Depth from root
        """
        depth = 0
        current = node
        while current.parent is not None:
            depth += 1
            current = current.parent
        return depth
    
    def _select(self, node: MCTSNode, root_player_id: int) -> MCTSNode:
        """
        Selection phase: traverse tree using UCB1.
        
        Args:
            node: Current node
            root_player_id: The root player's ID for perspective-aware selection
        
        Returns:
            Leaf node to expand
        """
        while not node.is_terminal():
            if not node.is_fully_expanded():
                return node.expand()
            else:
                best = node.best_child(root_player_id)
                if best is None:
                    return node
                node = best
        return node
    
    def _simulate(self, state: GameState) -> float:
        """
        Simulation phase: Intelligent playout using Splendor domain knowledge.
        
        Args:
            state: State to simulate from
        
        Returns:
            Result value (1.0 for win, 0.0 for loss, scaled partial score)
        """
        sim_state = state.get_state_copy()
        
        max_turns = 30  # Shorter simulations = more total simulations
        turns = 0
        
        while not sim_state.game_over and turns < max_turns:
            current_player = sim_state.current_player
            legal_actions = sim_state.get_legal_actions(current_player)
            
            if not legal_actions:
                break
            
            # Smart action selection using domain knowledge
            action = self._select_smart_action(sim_state, legal_actions, current_player)
            sim_state.apply_action(action)
            turns += 1
        
        # Enhanced evaluation
        return self._evaluate_position(sim_state)
    
    def _select_smart_action(self, state: GameState, actions: List[Action], player_id: int) -> Action:
        """Ultra-aggressive simulation policy - plays near-optimally."""
        # Categorize actions
        buy_actions = [a for a in actions if a.type == "buy_card"]
        reserve_actions = [a for a in actions if a.type == "reserve_card"]
        gem_actions = [a for a in actions if a.type in ["take_3_different", "take_2_same"]]
        
        current_points = state.player_points[player_id]
        
        # Strategy: Ultra-aggressive card buying
        if buy_actions:
            # Score each buy action with ultra-aggressive weights
            scored_buys = []
            for action in buy_actions:
                card = action.data.get('card')
                if card:
                    # Ultra-aggressive scoring
                    score = card.points * 10  # Points are CRITICAL
                    score += card.tier * 3  # High tiers are valuable
                    score += 3  # Base value for engine
                    
                    # MASSIVE bonus for winning moves
                    if current_points + card.points >= 15:
                        score += 100  # ALWAYS take winning moves
                    elif current_points + card.points >= 13:
                        score += 20  # Very high priority near win
                    elif current_points + card.points >= 10:
                        score += 10  # High priority getting close
                    
                    # Bonus for high-point cards even early
                    if card.points >= 4:
                        score += 15
                    elif card.points >= 3:
                        score += 8
                    
                    scored_buys.append((score, action))
            
            if scored_buys:
                # 95% pick absolute best, 5% explore (ultra-aggressive)
                if random.random() < 0.95:
                    return max(scored_buys, key=lambda x: x[0])[1]
                else:
                    # Even in exploration, only consider top 2 moves
                    top_moves = sorted(scored_buys, key=lambda x: x[0], reverse=True)[:2]
                    return random.choice([a for _, a in top_moves])
        
        # If can't buy, rarely reserve (only if gems are maxed)
        if reserve_actions and random.random() < 0.15:
            return random.choice(reserve_actions)
        
        # Otherwise collect gems strategically
        if gem_actions:
            # Strongly prefer taking 3 different gems (better flexibility)
            take_3_actions = [a for a in gem_actions if a.type == "take_3_different"]
            if take_3_actions:
                return random.choice(take_3_actions)
            return random.choice(gem_actions)
        
        # Fallback
        return random.choice(actions)
    
    def _evaluate_position(self, state: GameState) -> float:
        """Ultra-win-focused evaluation - dramatically improved."""
        if state.winner == self.player_id:
            return 1.0
        elif state.winner is not None:
            return 0.0
        
        # Get player points
        my_points = state.player_points[self.player_id]
        opponent_points = max((p for i, p in enumerate(state.player_points) 
                              if i != self.player_id), default=0)
        
        # Factor 1: Point advantage with MASSIVE win-proximity scaling
        point_diff = my_points - opponent_points
        
        # Exponential bonus for being close to winning
        if my_points >= 14:
            proximity_bonus = 0.35  # Nearly winning
        elif my_points >= 12:
            proximity_bonus = 0.25  # Very close
        elif my_points >= 10:
            proximity_bonus = 0.15  # Close
        elif my_points >= 8:
            proximity_bonus = 0.08  # Getting there
        else:
            proximity_bonus = 0
        
        # Exponential penalty for opponent being close
        if opponent_points >= 14:
            proximity_penalty = 0.35
        elif opponent_points >= 12:
            proximity_penalty = 0.25
        elif opponent_points >= 10:
            proximity_penalty = 0.15
        elif opponent_points >= 8:
            proximity_penalty = 0.08
        else:
            proximity_penalty = 0
        
        # Point difference with aggressive scaling
        point_score = 0.5 + (point_diff / 20.0) + proximity_bonus - proximity_penalty
        
        # Factor 2: Engine strength (bonuses)
        my_bonuses = sum(state.player_gems[self.player_id].values())
        opponent_bonuses = max((sum(state.player_gems[i].values()) 
                               for i in range(state.num_players) if i != self.player_id), default=0)
        bonus_diff = my_bonuses - opponent_bonuses
        bonus_score = bonus_diff / 12.0  # More sensitive
        
        # Factor 3: Nobles (3 points each!)
        my_nobles = len(state.player_nobles[self.player_id])
        opponent_nobles = max((len(state.player_nobles[i]) 
                              for i in range(state.num_players) if i != self.player_id), default=0)
        noble_score = (my_nobles - opponent_nobles) * 0.12  # Nobles are HUGE
        
        # Factor 4: Card count (engine size)
        my_card_count = len(state.player_cards[self.player_id])
        opponent_card_count = max((len(state.player_cards[i]) 
                                  for i in range(state.num_players) if i != self.player_id), default=0)
        card_count_score = (my_card_count - opponent_card_count) * 0.025
        
        # Combine with heavily point-focused weights
        # Points: 80%, Engine: 12%, Nobles: 10%, Cards: 3%
        total_score = (point_score * 0.80 + 
                      bonus_score * 0.12 + 
                      noble_score * 0.10 + 
                      card_count_score * 0.03)
        
        # Aggressive clamping - favor extreme scores
        result = max(0.0, min(1.0, total_score))
        
        # Push toward extremes when clearly winning/losing
        if result > 0.7:
            result = 0.65 + (result - 0.7) * 1.17  # Amplify winning positions
        elif result < 0.3:
            result = 0.35 - (0.3 - result) * 1.17  # Amplify losing positions
        
        return max(0.0, min(1.0, result))
    
    def evaluate_state_as_critic(self, game_state: GameState, target_player: int, simulations: int = 50):
        """
        Evaluate a game state from the perspective of target_player.
        Used as 'The MCTS Critic' to evaluate moves made by other agents.
        
        Args:
            game_state: Game state to evaluate
            target_player: Player ID to evaluate for
            simulations: Number of simulations to run (default 50)
        
        Returns:
            Dictionary with win_probability and projected_score
        """
        # Temporarily switch to evaluate from target player's perspective
        original_player = self.player_id
        self.player_id = target_player
        
        try:
            # Run brief MCTS search
            _, metadata = self.get_move(game_state, max_simulations=simulations)
            
            # Get projected score based on current state
            projected_score = game_state.player_points[target_player]
            
            return {
                'win_probability': metadata.get('win_probability', 0.5),
                'projected_score': projected_score,
                'simulation_count': metadata.get('simulation_count', 0)
            }
        finally:
            # Restore original player
            self.player_id = original_player
    
    def export_tree_structure(self, root_node: MCTSNode, max_depth: int = 3, top_k: int = 3, turn_number: int = None):
        """
        Export tree structure for visualization with pruning.
        Marks the chosen path (best child at each level) in red.
        
        Args:
            root_node: Root node of the MCTS tree
            max_depth: Maximum depth to export (default 3)
            top_k: Number of top children to keep per node (default 3)
            turn_number: The turn number when this tree was captured (optional)
        
        Returns:
            Dictionary with 'nodes' and 'edges' lists for visualization
        """
        nodes = []
        edges = []
        node_id_counter = [0]  # Use list for mutability in nested function
        chosen_path_node_ids = []  # Track nodes on the chosen path
        
        def traverse(node: MCTSNode, depth: int = 0, parent_id: int = None, is_chosen_path: bool = False):
            """Recursively traverse and export tree."""
            if depth > max_depth:
                return
            
            # Assign unique ID to this node
            current_id = node_id_counter[0]
            node_id_counter[0] += 1
            
            # Mark if this node is on the chosen path
            if is_chosen_path:
                chosen_path_node_ids.append(current_id)
            
            # Calculate win rate
            win_rate = node.value / node.visits if node.visits > 0 else 0.0
            
            # All nodes are green for clean visualization
            color = '#2ecc71'  # Green
            
            # Highlight chosen path nodes with special border
            if is_chosen_path:
                # Add golden/orange border to chosen nodes
                node_border_color = '#FF6B35'
                node_border_width = 5
            else:
                node_border_color = color
                node_border_width = 2
            
            # Get action description if available
            action_desc = "Root Position"
            if node.action is not None:
                action_desc = self.get_move_description(node.action)
            
            # Create label
            label = f"Win: {win_rate*100:.1f}%\\n(N={node.visits})"
            if is_chosen_path:
                label += "\\n⭐ CHOSEN"
            
            # Scale size based on visits (10-40 range)
            size = min(40, max(10, 10 + (node.visits / 10)))
            if is_chosen_path:
                size += 5  # Make chosen nodes slightly bigger
            
            # Build tooltip with all information
            tooltip_parts = []
            if turn_number is not None:
                turn_display = turn_number + depth if depth > 0 else turn_number
                tooltip_parts.append(f"<b>Turn: {turn_display}</b>")
            tooltip_parts.append(f"<b>Action: {action_desc}</b>")
            tooltip_parts.append(f"Visits: {node.visits}")
            tooltip_parts.append(f"Win Rate: {win_rate*100:.1f}%")
            if is_chosen_path:
                tooltip_parts.append("<b>⭐ CHOSEN PATH</b>")
            tooltip = "<br>".join(tooltip_parts)
            
            # Add node
            nodes.append({
                'id': current_id,
                'label': label,
                'color': {'background': color, 'border': node_border_color},
                'borderWidth': node_border_width,
                'size': size,
                'visits': node.visits,
                'win_rate': win_rate,
                'title': tooltip
            })
            
            # Add edge from parent
            if parent_id is not None:
                edge_data = {
                    'from': parent_id,
                    'to': current_id,
                    'width': 3 if is_chosen_path else 2,  # Thinner red path
                    'color': '#FF0000' if is_chosen_path else '#848484',  # Red for chosen path
                    'arrows': 'to'
                }
                if is_chosen_path:
                    edge_data['dashes'] = False
                    edge_data['smooth'] = {'type': 'curvedCW', 'roundness': 0.2}
                edges.append(edge_data)
            
            # Prune: only keep top_k children by visit count
            if node.children and depth < max_depth:
                sorted_children = sorted(node.children, key=lambda c: c.visits, reverse=True)
                top_children = sorted_children[:top_k]
                
                # The best child (most visits) is the chosen path
                best_child = sorted_children[0] if sorted_children else None
                
                # Recurse on top children
                for child in top_children:
                    # Mark if this child is the best (chosen) one
                    child_is_chosen = (child == best_child) and is_chosen_path
                    traverse(child, depth + 1, current_id, child_is_chosen)
        
        # Start traversal from root - root is on chosen path
        traverse(root_node, is_chosen_path=True)
        
        return {
            'nodes': nodes,
            'edges': edges,
            'chosen_path': chosen_path_node_ids
        }
    
    def get_move_description(self, action: Action) -> str:
        """
        Get human-readable description of an action.
        
        Args:
            action: The action taken
        
        Returns:
            Description string
        """
        if action.type == "buy_card":
            card = action.data['card']
            return f"Bought {card.gem_bonus.value} card ({card.points} pts)"
        elif action.type == "take_3_different":
            gems = [g.value for g in action.data['gems']]
            return f"Took 3 gems: {', '.join(gems)}"
        elif action.type == "take_2_same":
            gem = action.data['gem'].value
            return f"Took 2 {gem} gems"
        else:
            return f"Reserved card"
