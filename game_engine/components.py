"""
Game components: Cards, Gems, Nobles
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


class GemType(Enum):
    """Gem colors in Splendor."""
    WHITE = "white"
    BLUE = "blue"
    GREEN = "green"
    RED = "red"
    BLACK = "black"
    GOLD = "gold"  # Wildcard


@dataclass
class Card:
    """
    Represents a development card.
    
    Attributes:
        tier: Card tier (1, 2, or 3)
        points: Victory points
        gem_bonus: Gem type this card provides as bonus
        cost: Dictionary of gems required to purchase
    """
    tier: int
    points: int
    gem_bonus: GemType
    cost: Dict[GemType, int]
    
    def can_afford(self, player_gems: Dict[GemType, int], 
                   player_bonuses: Dict[GemType, int]) -> tuple[bool, int]:
        """
        Check if player can afford this card.
        
        Returns:
            (can_afford, gold_needed)
        """
        gold_needed = 0
        
        for gem_type, required in self.cost.items():
            available = player_gems.get(gem_type, 0) + player_bonuses.get(gem_type, 0)
            shortage = required - available
            if shortage > 0:
                gold_needed += shortage
        
        total_gold = player_gems.get(GemType.GOLD, 0)
        return gold_needed <= total_gold, gold_needed
        
    def get_hash(self) -> str:
        """Return a deterministic string representation for this card."""
        cost_str = ",".join(f"{k.value}:{v}" for k, v in sorted(self.cost.items(), key=lambda x: x[0].value))
        return f"C_{self.tier}_{self.points}_{self.gem_bonus.value}_{cost_str}"


@dataclass
class Noble:
    """
    Represents a noble tile.
    
    Attributes:
        requirements: Gem bonuses required to attract this noble
        points: Victory points (always 3)
    """
    requirements: Dict[GemType, int]
    points: int = 3
    
    def can_visit(self, player_bonuses: Dict[GemType, int]) -> bool:
        """Check if player has enough bonuses to attract this noble."""
        for gem_type, required in self.requirements.items():
            if player_bonuses.get(gem_type, 0) < required:
                return False
        return True
        
    def get_hash(self) -> str:
        """Return a deterministic string representation for this noble."""
        req_str = ",".join(f"{k.value}:{v}" for k, v in sorted(self.requirements.items(), key=lambda x: x[0].value))
        return f"N_{self.points}_{req_str}"


class Action:
    """Represents a player action."""
    
    def __init__(self, action_type: str, **kwargs):
        self.type = action_type
        self.data = kwargs
    
    def __repr__(self):
        return f"Action({self.type}, {self.data})"
    
    def __eq__(self, other):
        if not isinstance(other, Action):
            return False
        return self.type == other.type and self.data == other.data
        
    def get_hash(self) -> str:
        """Return a deterministic string representation for this action."""
        data_parts = []
        for k in sorted(self.data.keys()):
            v = self.data[k]
            if isinstance(v, list):
                # E.g., gems list -> join their values
                val_str = "-".join(x.value if isinstance(x, GemType) else str(x) for x in v)
            elif hasattr(v, "get_hash"):
                val_str = v.get_hash()
            elif isinstance(v, GemType):
                val_str = v.value
            else:
                val_str = str(v)
            data_parts.append(f"{k}={val_str}")
            
        data_str = "|".join(data_parts)
        return f"{self.type}[{data_str}]"
    
    def __hash__(self):
        return hash(self.get_hash())


# Action types
TAKE_3_DIFFERENT = "take_3_different"
TAKE_2_SAME = "take_2_same"
RESERVE_CARD = "reserve_card"
BUY_CARD = "buy_card"
