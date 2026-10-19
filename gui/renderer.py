"""
Pygame rendering functions for game components.
"""

import pygame
from typing import Dict, List, Tuple
from game_engine.components import Card, Noble, GemType


# Colors
COLORS = {
    GemType.WHITE: (240, 240, 240),
    GemType.BLUE: (70, 130, 180),
    GemType.GREEN: (60, 179, 113),
    GemType.RED: (220, 60, 60),
    GemType.BLACK: (40, 40, 40),
    GemType.GOLD: (184, 134, 11),  # Dark goldenrod - less bright
}

TIER_COLORS = {
    1: (100, 200, 100),
    2: (100, 150, 200),
    3: (200, 100, 150),
}

BG_COLOR = (40, 45, 52)
TEXT_COLOR = (230, 230, 230)
HIGHLIGHT_COLOR = (204, 85, 0)  # Dark orange


def draw_gem(surface: pygame.Surface, gem_type: GemType, x: int, y: int, 
             radius: int = 15, count: int = None):
    """
    Draw a gem token.
    
    Args:
        surface: Pygame surface to draw on
        gem_type: Type of gem
        x, y: Center position
        radius: Gem radius
        count: Optional count to display
    """
    color = COLORS[gem_type]
    pygame.draw.circle(surface, color, (x, y), radius)
    pygame.draw.circle(surface, TEXT_COLOR, (x, y), radius, 2)
    
    if count is not None and count > 0:
        font = pygame.font.Font(None, 20)
        text = font.render(str(count), True, TEXT_COLOR)
        text_rect = text.get_rect(center=(x, y))
        surface.blit(text, text_rect)


def draw_card(surface: pygame.Surface, card: Card, x: int, y: int, 
              width: int = 80, height: int = 100, highlight: bool = False):
    """
    Draw a development card.
    
    Args:
        surface: Pygame surface to draw on
        card: Card to draw
        x, y: Top-left position
        width, height: Card dimensions
        highlight: Whether to highlight the card
    """
    # Background
    tier_color = TIER_COLORS.get(card.tier, (150, 150, 150))
    pygame.draw.rect(surface, tier_color, (x, y, width, height), border_radius=5)
    
    if highlight:
        pygame.draw.rect(surface, HIGHLIGHT_COLOR, (x, y, width, height), 3, border_radius=5)
    else:
        pygame.draw.rect(surface, TEXT_COLOR, (x, y, width, height), 2, border_radius=5)
    
    # Bonus gem
    bonus_color = COLORS[card.gem_bonus]
    pygame.draw.circle(surface, bonus_color, (x + width - 15, y + 15), 10)
    pygame.draw.circle(surface, TEXT_COLOR, (x + width - 15, y + 15), 10, 1)
    
    # Points
    if card.points > 0:
        font = pygame.font.Font(None, 24)
        points_text = font.render(str(card.points), True, TEXT_COLOR)
        surface.blit(points_text, (x + 5, y + 5))
    
    # Cost
    font_small = pygame.font.Font(None, 16)
    cost_y = y + 35
    for gem_type, amount in card.cost.items():
        gem_color = COLORS[gem_type]
        pygame.draw.circle(surface, gem_color, (x + 15, cost_y), 8)
        cost_text = font_small.render(str(amount), True, TEXT_COLOR)
        surface.blit(cost_text, (x + 25, cost_y - 7))
        cost_y += 18


def draw_noble(surface: pygame.Surface, noble: Noble, x: int, y: int, 
               width: int = 70, height: int = 70):
    """
    Draw a noble tile.
    
    Args:
        surface: Pygame surface to draw on
        noble: Noble to draw
        x, y: Top-left position
        width, height: Noble dimensions
    """
    # Background
    pygame.draw.rect(surface, (200, 180, 140), (x, y, width, height), border_radius=5)
    pygame.draw.rect(surface, TEXT_COLOR, (x, y, width, height), 2, border_radius=5)
    
    # Points
    font = pygame.font.Font(None, 24)
    points_text = font.render("3", True, TEXT_COLOR)
    surface.blit(points_text, (x + 5, y + 5))
    
    # Requirements
    font_small = pygame.font.Font(None, 14)
    req_y = y + 30
    for gem_type, amount in noble.requirements.items():
        gem_color = COLORS[gem_type]
        pygame.draw.circle(surface, gem_color, (x + 15, req_y), 6)
        req_text = font_small.render(str(amount), True, TEXT_COLOR)
        surface.blit(req_text, (x + 25, req_y - 6))
        req_y += 15


def draw_gem_bank(surface: pygame.Surface, gem_bank: Dict[GemType, int], 
                  x: int, y: int):
    """
    Draw the gem bank.
    
    Args:
        surface: Pygame surface to draw on
        gem_bank: Dictionary of gem counts
        x, y: Top-left position
    """
    font = pygame.font.Font(None, 20)
    title = font.render("Gem Bank", True, TEXT_COLOR)
    surface.blit(title, (x, y))
    
    gem_y = y + 30
    for gem_type in [GemType.WHITE, GemType.BLUE, GemType.GREEN, 
                     GemType.RED, GemType.BLACK, GemType.GOLD]:
        count = gem_bank.get(gem_type, 0)
        draw_gem(surface, gem_type, x + 20, gem_y, 15, count)
        gem_y += 40


def draw_player_area(surface: pygame.Surface, player_id: int, 
                     gems: Dict[GemType, int], bonuses: Dict[GemType, int],
                     points: int, cards: List[Card], nobles: List[Noble],
                     x: int, y: int, width: int, height: int,
                     is_current: bool = False):
    """
    Draw player's tableau.
    
    Args:
        surface: Pygame surface to draw on
        player_id: Player number
        gems: Player's gem tokens
        bonuses: Player's gem bonuses
        points: Player's points
        cards: Player's cards
        nobles: Player's nobles
        x, y: Top-left position
        width, height: Area dimensions
        is_current: Whether this is the current player
    """
    # Background
    bg_color = HIGHLIGHT_COLOR if is_current else (60, 65, 70)
    pygame.draw.rect(surface, bg_color, (x, y, width, height), border_radius=10)
    pygame.draw.rect(surface, TEXT_COLOR, (x, y, width, height), 2, border_radius=10)
    
    # Header
    font = pygame.font.Font(None, 24)
    header = f"Player {player_id + 1} - {points} pts"
    if is_current:
        header += " (Current)"
    header_text = font.render(header, True, TEXT_COLOR)
    surface.blit(header_text, (x + 10, y + 10))
    
    # Gems
    gem_x = x + 10
    gem_y = y + 40
    font_small = pygame.font.Font(None, 18)
    for gem_type in [GemType.WHITE, GemType.BLUE, GemType.GREEN, 
                     GemType.RED, GemType.BLACK, GemType.GOLD]:
        count = gems.get(gem_type, 0)
        if count > 0:
            draw_gem(surface, gem_type, gem_x + 15, gem_y, 12)
            count_text = font_small.render(f"×{count}", True, TEXT_COLOR)
            surface.blit(count_text, (gem_x + 30, gem_y - 8))
            gem_x += 60
    
    # Bonuses
    bonus_x = x + 10
    bonus_y = y + 70
    bonus_label = font_small.render("Bonuses:", True, TEXT_COLOR)
    surface.blit(bonus_label, (bonus_x, bonus_y - 8))
    bonus_x += 70
    
    for gem_type in [GemType.WHITE, GemType.BLUE, GemType.GREEN, 
                     GemType.RED, GemType.BLACK]:
        count = bonuses.get(gem_type, 0)
        if count > 0:
            draw_gem(surface, gem_type, bonus_x + 10, bonus_y, 10)
            count_text = font_small.render(f"×{count}", True, TEXT_COLOR)
            surface.blit(count_text, (bonus_x + 25, bonus_y - 8))
            bonus_x += 50
    
    # Cards (show count)
    cards_label = font_small.render(f"Cards: {len(cards)}", True, TEXT_COLOR)
    surface.blit(cards_label, (x + 10, y + 100))
    
    # Nobles
    if nobles:
        nobles_label = font_small.render(f"Nobles: {len(nobles)}", True, TEXT_COLOR)
        surface.blit(nobles_label, (x + 100, y + 100))
