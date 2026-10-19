"""
Core game state and rules engine.
"""

from typing import List, Dict, Optional, Tuple
from copy import deepcopy
from collections import defaultdict
import random

from game_engine.components import (
    Card, Noble, Action, GemType,
    TAKE_3_DIFFERENT, TAKE_2_SAME, RESERVE_CARD, BUY_CARD
)


class GameState:
    """
    Manages the complete game state for Splendor.
    
    Tracks:
    - Gem bank
    - Card decks and visible cards
    - Nobles
    - Player tableaux (cards, gems, reserved cards)
    """
    
    def __init__(self, num_players: int = 2):
        self.num_players = num_players
        self.current_player = 0
        self.turn_number = 0
        self.game_over = False
        self.winner = None
        self.end_game_triggered = False
        self.trigger_player = None  # Player who reached 15 first
        
        # Gem bank
        gems_per_color = {2: 4, 3: 5, 4: 7}[num_players]
        self.gem_bank = {
            GemType.WHITE: gems_per_color,
            GemType.BLUE: gems_per_color,
            GemType.GREEN: gems_per_color,
            GemType.RED: gems_per_color,
            GemType.BLACK: gems_per_color,
            GemType.GOLD: 5
        }
        
        # Card decks (hidden)
        self.deck_tier1: List[Card] = []
        self.deck_tier2: List[Card] = []
        self.deck_tier3: List[Card] = []
        
        # Visible cards (4 per tier)
        self.visible_tier1: List[Card] = []
        self.visible_tier2: List[Card] = []
        self.visible_tier3: List[Card] = []
        
        # Nobles (num_players + 1)
        self.nobles: List[Noble] = []
        
        # Player data
        self.player_gems: List[Dict[GemType, int]] = []
        self.player_bonuses: List[Dict[GemType, int]] = []
        self.player_cards: List[List[Card]] = []
        self.player_reserved: List[List[Card]] = []
        self.player_points: List[int] = []
        self.player_nobles: List[List[Noble]] = []
        
        # Initialize game
        self._initialize_decks()
        self._initialize_nobles()
        self._initialize_players()
        self._deal_cards()
    
    def _initialize_decks(self):
        """Create card decks with proper Splendor distribution."""
        # Tier 1: 40 cards (cheap, 0-1 points)
        tier1_configs = [
            # 0 point cards
            (0, GemType.WHITE, {GemType.BLUE: 3}),
            (0, GemType.WHITE, {GemType.GREEN: 3}),
            (0, GemType.WHITE, {GemType.RED: 3}),
            (0, GemType.WHITE, {GemType.BLACK: 3}),
            (0, GemType.WHITE, {GemType.BLUE: 2, GemType.GREEN: 1}),
            (0, GemType.BLUE, {GemType.WHITE: 3}),
            (0, GemType.BLUE, {GemType.GREEN: 3}),
            (0, GemType.BLUE, {GemType.RED: 3}),
            (0, GemType.BLUE, {GemType.BLACK: 3}),
            (0, GemType.BLUE, {GemType.WHITE: 2, GemType.BLACK: 1}),
            (0, GemType.GREEN, {GemType.WHITE: 3}),
            (0, GemType.GREEN, {GemType.BLUE: 3}),
            (0, GemType.GREEN, {GemType.RED: 3}),
            (0, GemType.GREEN, {GemType.BLACK: 3}),
            (0, GemType.GREEN, {GemType.BLUE: 2, GemType.RED: 1}),
            (0, GemType.RED, {GemType.WHITE: 3}),
            (0, GemType.RED, {GemType.BLUE: 3}),
            (0, GemType.RED, {GemType.GREEN: 3}),
            (0, GemType.RED, {GemType.BLACK: 3}),
            (0, GemType.RED, {GemType.GREEN: 2, GemType.BLACK: 1}),
            (0, GemType.BLACK, {GemType.WHITE: 3}),
            (0, GemType.BLACK, {GemType.BLUE: 3}),
            (0, GemType.BLACK, {GemType.GREEN: 3}),
            (0, GemType.BLACK, {GemType.RED: 3}),
            (0, GemType.BLACK, {GemType.RED: 2, GemType.WHITE: 1}),
            # 1 point cards
            (1, GemType.WHITE, {GemType.BLUE: 4}),
            (1, GemType.WHITE, {GemType.BLACK: 4}),
            (1, GemType.BLUE, {GemType.WHITE: 4}),
            (1, GemType.BLUE, {GemType.RED: 4}),
            (1, GemType.GREEN, {GemType.BLUE: 4}),
            (1, GemType.GREEN, {GemType.BLACK: 4}),
            (1, GemType.RED, {GemType.WHITE: 4}),
            (1, GemType.RED, {GemType.GREEN: 4}),
            (1, GemType.BLACK, {GemType.GREEN: 4}),
            (1, GemType.BLACK, {GemType.RED: 4}),
        ]
        
        for points, bonus, cost in tier1_configs:
            self.deck_tier1.append(Card(tier=1, points=points, gem_bonus=bonus, cost=cost))
        
        # Tier 2: 30 cards (medium, 1-3 points)
        tier2_configs = [
            (1, GemType.WHITE, {GemType.BLUE: 3, GemType.GREEN: 2, GemType.RED: 2}),
            (1, GemType.BLUE, {GemType.WHITE: 3, GemType.GREEN: 2, GemType.BLACK: 2}),
            (1, GemType.GREEN, {GemType.WHITE: 3, GemType.BLUE: 2, GemType.RED: 2}),
            (1, GemType.RED, {GemType.BLUE: 3, GemType.GREEN: 2, GemType.BLACK: 2}),
            (1, GemType.BLACK, {GemType.WHITE: 3, GemType.RED: 2, GemType.BLACK: 2}),
            (2, GemType.WHITE, {GemType.BLUE: 5}),
            (2, GemType.WHITE, {GemType.GREEN: 5}),
            (2, GemType.BLUE, {GemType.WHITE: 5}),
            (2, GemType.BLUE, {GemType.BLACK: 5}),
            (2, GemType.GREEN, {GemType.BLUE: 5}),
            (2, GemType.GREEN, {GemType.RED: 5}),
            (2, GemType.RED, {GemType.GREEN: 5}),
            (2, GemType.RED, {GemType.BLACK: 5}),
            (2, GemType.BLACK, {GemType.RED: 5}),
            (2, GemType.BLACK, {GemType.WHITE: 5}),
            (3, GemType.WHITE, {GemType.WHITE: 6}),
            (3, GemType.BLUE, {GemType.BLUE: 6}),
            (3, GemType.GREEN, {GemType.GREEN: 6}),
            (3, GemType.RED, {GemType.RED: 6}),
            (3, GemType.BLACK, {GemType.BLACK: 6}),
        ]
        
        for points, bonus, cost in tier2_configs:
            self.deck_tier2.append(Card(tier=2, points=points, gem_bonus=bonus, cost=cost))
        
        # Tier 3: 20 cards (expensive, 3-5 points)
        tier3_configs = [
            (3, GemType.WHITE, {GemType.WHITE: 3, GemType.BLUE: 3, GemType.GREEN: 5, GemType.RED: 3}),
            (3, GemType.BLUE, {GemType.WHITE: 3, GemType.BLUE: 3, GemType.GREEN: 3, GemType.BLACK: 5}),
            (3, GemType.GREEN, {GemType.BLUE: 5, GemType.GREEN: 3, GemType.RED: 3, GemType.BLACK: 3}),
            (3, GemType.RED, {GemType.WHITE: 5, GemType.GREEN: 3, GemType.RED: 3, GemType.BLACK: 3}),
            (3, GemType.BLACK, {GemType.WHITE: 3, GemType.BLUE: 3, GemType.RED: 5, GemType.BLACK: 3}),
            (4, GemType.WHITE, {GemType.BLACK: 7}),
            (4, GemType.BLUE, {GemType.RED: 7}),
            (4, GemType.GREEN, {GemType.WHITE: 7}),
            (4, GemType.RED, {GemType.BLUE: 7}),
            (4, GemType.BLACK, {GemType.GREEN: 7}),
            (5, GemType.WHITE, {GemType.BLACK: 7, GemType.RED: 3}),
            (5, GemType.BLUE, {GemType.WHITE: 7, GemType.GREEN: 3}),
            (5, GemType.GREEN, {GemType.BLUE: 7, GemType.BLACK: 3}),
            (5, GemType.RED, {GemType.GREEN: 7, GemType.WHITE: 3}),
            (5, GemType.BLACK, {GemType.RED: 7, GemType.BLUE: 3}),
        ]
        
        for points, bonus, cost in tier3_configs:
            self.deck_tier3.append(Card(tier=3, points=points, gem_bonus=bonus, cost=cost))
        
        # Shuffle decks
        random.shuffle(self.deck_tier1)
        random.shuffle(self.deck_tier2)
        random.shuffle(self.deck_tier3)
    
    def _initialize_nobles(self):
        """Create noble tiles."""
        all_nobles = [
            Noble({GemType.WHITE: 3, GemType.BLUE: 3, GemType.GREEN: 3}),
            Noble({GemType.BLUE: 3, GemType.GREEN: 3, GemType.RED: 3}),
            Noble({GemType.GREEN: 3, GemType.RED: 3, GemType.BLACK: 3}),
            Noble({GemType.RED: 3, GemType.BLACK: 3, GemType.WHITE: 3}),
            Noble({GemType.BLACK: 3, GemType.WHITE: 3, GemType.BLUE: 3}),
            Noble({GemType.WHITE: 4, GemType.BLUE: 4}),
            Noble({GemType.BLUE: 4, GemType.GREEN: 4}),
            Noble({GemType.GREEN: 4, GemType.RED: 4}),
            Noble({GemType.RED: 4, GemType.BLACK: 4}),
            Noble({GemType.BLACK: 4, GemType.WHITE: 4}),
        ]
        random.shuffle(all_nobles)
        self.nobles = all_nobles[:self.num_players + 1]
    
    def _initialize_players(self):
        """Initialize player data structures."""
        for _ in range(self.num_players):
            self.player_gems.append(defaultdict(int))
            self.player_bonuses.append(defaultdict(int))
            self.player_cards.append([])
            self.player_reserved.append([])
            self.player_points.append(0)
            self.player_nobles.append([])
    
    def _deal_cards(self):
        """Deal initial visible cards."""
        for _ in range(4):
            if self.deck_tier1:
                self.visible_tier1.append(self.deck_tier1.pop())
            if self.deck_tier2:
                self.visible_tier2.append(self.deck_tier2.pop())
            if self.deck_tier3:
                self.visible_tier3.append(self.deck_tier3.pop())
    
    def get_legal_actions(self, player_id: int) -> List[Action]:
        """
        Generate all legal actions for the specified player.
        
        Returns:
            List of valid Action objects
        """
        actions = []
        
        # Get player data
        player_gems = self.player_gems[player_id]
        player_bonuses = self.player_bonuses[player_id]
        player_reserved = self.player_reserved[player_id]
        
        total_gems = sum(player_gems.values())
        
        # 1. Take 3 different colored gems
        available_colors = [gem for gem in [GemType.WHITE, GemType.BLUE, GemType.GREEN, 
                                            GemType.RED, GemType.BLACK] 
                           if self.gem_bank[gem] > 0]
        
        if len(available_colors) >= 3 and total_gems <= 7:
            from itertools import combinations
            for combo in combinations(available_colors, 3):
                actions.append(Action(TAKE_3_DIFFERENT, gems=list(combo)))
        
        # 2. Take 2 gems of same color (if 4+ available)
        for gem_type in available_colors:
            if self.gem_bank[gem_type] >= 4 and total_gems <= 8:
                actions.append(Action(TAKE_2_SAME, gem=gem_type))
        
        # 3. Reserve a card (if < 3 reserved) - Always allow if cards available
        if len(player_reserved) < 3:
            all_visible_cards = self.visible_tier1 + self.visible_tier2 + self.visible_tier3
            if all_visible_cards:
                for card in all_visible_cards:
                    actions.append(Action(RESERVE_CARD, card=card))
        
        # 4. Buy a visible card
        for card in self.visible_tier1 + self.visible_tier2 + self.visible_tier3:
            can_afford, gold_needed = card.can_afford(dict(player_gems), dict(player_bonuses))
            if can_afford:
                actions.append(Action(BUY_CARD, card=card))
        
        # 5. Buy a reserved card
        for card in player_reserved:
            can_afford, gold_needed = card.can_afford(dict(player_gems), dict(player_bonuses))
            if can_afford:
                actions.append(Action(BUY_CARD, card=card, from_reserved=True))
        
        # 6. Fallback: If no actions available at all, allow taking fewer gems
        if not actions:
            # Try taking 2 different gems
            if len(available_colors) >= 2 and total_gems <= 8:
                from itertools import combinations
                for combo in combinations(available_colors, 2):
                    actions.append(Action(TAKE_3_DIFFERENT, gems=list(combo)))
            
            # Try taking 1 gem
            if len(available_colors) >= 1 and total_gems <= 9:
                for gem in available_colors:
                    actions.append(Action(TAKE_3_DIFFERENT, gems=[gem]))
        
        return actions
    
    def apply_action(self, action: Action) -> None:
        """
        Apply an action and update game state.
        
        Args:
            action: The action to execute
        """
        player_id = self.current_player
        
        if action.type == TAKE_3_DIFFERENT:
            for gem in action.data['gems']:
                self.gem_bank[gem] -= 1
                self.player_gems[player_id][gem] += 1
        
        elif action.type == TAKE_2_SAME:
            gem = action.data['gem']
            self.gem_bank[gem] -= 2
            self.player_gems[player_id][gem] += 2
        
        elif action.type == RESERVE_CARD:
            card = action.data['card']
            # Remove from visible
            if card in self.visible_tier1:
                self.visible_tier1.remove(card)
                if self.deck_tier1:
                    self.visible_tier1.append(self.deck_tier1.pop())
            elif card in self.visible_tier2:
                self.visible_tier2.remove(card)
                if self.deck_tier2:
                    self.visible_tier2.append(self.deck_tier2.pop())
            elif card in self.visible_tier3:
                self.visible_tier3.remove(card)
                if self.deck_tier3:
                    self.visible_tier3.append(self.deck_tier3.pop())
            
            # Add to reserved
            self.player_reserved[player_id].append(card)
            
            # Give gold if available
            if self.gem_bank[GemType.GOLD] > 0:
                self.gem_bank[GemType.GOLD] -= 1
                self.player_gems[player_id][GemType.GOLD] += 1
        
        elif action.type == BUY_CARD:
            card = action.data['card']
            from_reserved = action.data.get('from_reserved', False)
            
            # Calculate and pay cost
            can_afford, gold_needed = card.can_afford(
                dict(self.player_gems[player_id]),
                dict(self.player_bonuses[player_id])
            )
            
            if can_afford:
                # Pay gems
                for gem_type, required in card.cost.items():
                    bonus = self.player_bonuses[player_id].get(gem_type, 0)
                    gems_to_pay = max(0, required - bonus)
                    actual_payment = min(gems_to_pay, self.player_gems[player_id].get(gem_type, 0))
                    
                    if actual_payment > 0:
                        self.player_gems[player_id][gem_type] -= actual_payment
                        self.gem_bank[gem_type] += actual_payment
                
                # Pay gold for remainder
                if gold_needed > 0 and self.player_gems[player_id].get(GemType.GOLD, 0) >= gold_needed:
                    self.player_gems[player_id][GemType.GOLD] -= gold_needed
                    self.gem_bank[GemType.GOLD] += gold_needed
                
                # Remove card from board/reserved
                if from_reserved:
                    self.player_reserved[player_id].remove(card)
                else:
                    if card in self.visible_tier1:
                        self.visible_tier1.remove(card)
                        if self.deck_tier1:
                            self.visible_tier1.append(self.deck_tier1.pop())
                    elif card in self.visible_tier2:
                        self.visible_tier2.remove(card)
                        if self.deck_tier2:
                            self.visible_tier2.append(self.deck_tier2.pop())
                    elif card in self.visible_tier3:
                        self.visible_tier3.remove(card)
                        if self.deck_tier3:
                            self.visible_tier3.append(self.deck_tier3.pop())
                
                # Add to player
                self.player_cards[player_id].append(card)
                self.player_bonuses[player_id][card.gem_bonus] += 1
                self.player_points[player_id] += card.points
        
        # Check for nobles
        self._check_nobles(player_id)
        
        # Enforce gem limit (10 total)
        self._enforce_gem_limit(player_id)
        
        # Next player
        self.current_player = (self.current_player + 1) % self.num_players
        if self.current_player == 0:
            self.turn_number += 1
        
        # Check win condition
        self.check_winner()
    
    def _check_nobles(self, player_id: int):
        """Check if player attracts any nobles."""
        player_bonuses = self.player_bonuses[player_id]
        
        for noble in self.nobles[:]:  # Copy list to allow removal
            if noble.can_visit(player_bonuses):
                self.nobles.remove(noble)
                self.player_nobles[player_id].append(noble)
                self.player_points[player_id] += noble.points
                break  # Only one noble per turn
    
    def _enforce_gem_limit(self, player_id: int):
        """Ensure player has at most 10 gems."""
        total_gems = sum(self.player_gems[player_id].values())
        
        # Discard excess gems (simplified - just remove extras randomly)
        while total_gems > 10:
            # Remove from largest stack
            for gem_type in [GemType.WHITE, GemType.BLUE, GemType.GREEN, 
                           GemType.RED, GemType.BLACK, GemType.GOLD]:
                if self.player_gems[player_id].get(gem_type, 0) > 0:
                    self.player_gems[player_id][gem_type] -= 1
                    self.gem_bank[gem_type] += 1
                    total_gems -= 1
                    break
    
    def check_winner(self) -> Optional[int]:
        """
        Check if game is over and determine winner.
        Official 2-player rule: When a player reaches 15 points, finish the round
        so both players have had equal turns.
        
        Returns:
            Player ID of winner, or None if game continues
        """
        # Check if someone reached 15 points
        for i, pts in enumerate(self.player_points):
            if pts >= 15 and not self.end_game_triggered:
                self.end_game_triggered = True
                self.trigger_player = i
        
        # If end game was triggered, check if round is complete
        # Round is complete when we're back to player 0's turn
        if self.end_game_triggered and self.current_player == 0:
            # Determine winner
            max_points = max(self.player_points)
            winners = [i for i, pts in enumerate(self.player_points) if pts == max_points]
            
            # Tiebreaker: fewest cards (official rule)
            if len(winners) > 1:
                card_counts = [(i, len(self.player_cards[i])) for i in winners]
                winner = min(card_counts, key=lambda x: x[1])[0]
            else:
                winner = winners[0]
            
            self.game_over = True
            self.winner = winner
            return winner
        
        return None
    
    def get_state_copy(self):
        """Return a deep copy of the game state for simulations."""
        return deepcopy(self)
    
    def get_player_score(self, player_id: int) -> int:
        """Get total score for a player."""
        return self.player_points[player_id]

    def get_hash(self) -> str:
        """
        Return a deterministic string representation of the game state.
        This is used for persistent learning to uniquely identify a board position.
        """
        parts = []
        
        # 1. Gem bank
        bank_str = ",".join(f"{g.value}:{c}" for g, c in sorted(self.gem_bank.items(), key=lambda x: x[0].value))
        parts.append(f"BANK[{bank_str}]")
        
        # 2. Visible cards
        v1 = ",".join(sorted(c.get_hash() for c in self.visible_tier1))
        v2 = ",".join(sorted(c.get_hash() for c in self.visible_tier2))
        v3 = ",".join(sorted(c.get_hash() for c in self.visible_tier3))
        parts.append(f"V1[{v1}]V2[{v2}]V3[{v3}]")
        
        # 3. Nobles
        nobles_str = ",".join(sorted(n.get_hash() for n in self.nobles))
        parts.append(f"NOBLES[{nobles_str}]")
        
        # 4. Player data (order matters as players are distinguished by ID, 
        # but to make states symmetric, we'd need canonical representations. 
        # For simplicity, we just use the literal state from current player's perspective)
        # Shift players so current player is always first (index 0)
        shifted_indices = [(self.current_player + i) % self.num_players for i in range(self.num_players)]
        
        for i, p_idx in enumerate(shifted_indices):
            gems_str = ",".join(f"{g.value}:{c}" for g, c in sorted(self.player_gems[p_idx].items(), key=lambda x: x[0].value))
            bonuses_str = ",".join(f"{g.value}:{c}" for g, c in sorted(self.player_bonuses[p_idx].items(), key=lambda x: x[0].value))
            res_str = ",".join(sorted(c.get_hash() for c in self.player_reserved[p_idx]))
            
            parts.append(f"P{i}[G({gems_str})B({bonuses_str})R({res_str})Pts({self.player_points[p_idx]})]")
            
        return "|".join(parts)
