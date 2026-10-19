"""
Basic AI agent with simple heuristics.
"""

import random
from typing import List
from game_engine.state import GameState
from game_engine.components import Action, GemType
from game_engine.components import BUY_CARD, TAKE_3_DIFFERENT, TAKE_2_SAME, RESERVE_CARD


class BasicAgent:
    """
    Simple heuristic-based AI for Splendor.
    
    Strategy:
    1. Buy cards with victory points if affordable
    2. Buy cheapest card if no VP cards available
    3. Take gems needed for cheapest card
    4. Take 3 different gems if no clear target
    """
    
    def __init__(self, player_id: int):
        """
        Initialize the basic agent.
        
        Args:
            player_id: This agent's player ID
        """
        self.player_id = player_id
        self.name = "Basic Heuristic"
    
    def select_move(self, game_state: GameState) -> Action:
        """
        Select the best move using simple heuristics.
        
        Args:
            game_state: Current game state
        
        Returns:
            Selected action
        """
        legal_actions = game_state.get_legal_actions(self.player_id)
        
        if not legal_actions:
            # Emergency fallback
            print(f"WARNING: Player {self.player_id} has no legal moves!")
            return Action(TAKE_3_DIFFERENT, gems=[GemType.WHITE])
        
        # Separate actions by type
        buy_actions = [a for a in legal_actions if a.type == BUY_CARD]
        gem_actions = [a for a in legal_actions 
                      if a.type in [TAKE_3_DIFFERENT, TAKE_2_SAME]]
        
        # Priority 1: Buy cards with victory points
        vp_buys = [a for a in buy_actions if a.data['card'].points > 0]
        if vp_buys:
            # Buy card with most points
            best = max(vp_buys, key=lambda a: a.data['card'].points)
            return best
        
        # Priority 2: Buy any affordable card (build engine)
        if buy_actions:
            # Buy cheapest card to build gem bonuses
            cheapest = min(buy_actions, 
                          key=lambda a: sum(a.data['card'].cost.values()))
            return cheapest
        
        # Priority 3: Strategic Reservation (Hyperparameter: 0.2 probability)
        reserve_actions = [a for a in legal_actions if a.type == RESERVE_CARD]
        if reserve_actions and random.random() < 0.2:
            return random.choice(reserve_actions)
            
        # Priority 4: Take gems strategically
        if gem_actions:
            # Prefer taking 3 different (more efficient)
            take_3 = [a for a in gem_actions if a.type == TAKE_3_DIFFERENT]
            if take_3:
                return random.choice(take_3)
            else:
                return random.choice(gem_actions)
        
        # Fallback: Random legal action
        return random.choice(legal_actions)
    
    def get_move_description(self, action: Action) -> str:
        """
        Get human-readable description of an action.
        
        Args:
            action: The action taken
        
        Returns:
            Description string
        """
        if action.type == BUY_CARD:
            card = action.data['card']
            return f"Bought {card.gem_bonus.value} card ({card.points} pts)"
        elif action.type == TAKE_3_DIFFERENT:
            gems = [g.value for g in action.data['gems']]
            return f"Took 3 gems: {', '.join(gems)}"
        elif action.type == TAKE_2_SAME:
            gem = action.data['gem'].value
            return f"Took 2 {gem} gems"
        else:
            return f"Reserved card"
