"""
Main game window with pygame.
"""

import pygame
import sys
from typing import Optional

from game_engine.state import GameState
from game_engine.components import GemType
from gui.renderer import (
    draw_card, draw_noble, draw_gem_bank, draw_player_area,
    BG_COLOR, TEXT_COLOR
)
from gui.logger_widget import LoggerWidget


class GameWindow:
    """
    Main pygame window for Splendor visualization.
    
    Layout:
    - Left side: Game board (gems, cards, nobles)
    - Right side: Scrollable move log
    - Bottom: Player areas
    - Controls: Start, Next Turn, Auto-Play toggle, Speed slider
    """
    
    def __init__(self, width: int = 1400, height: int = 900):
        """
        Initialize the game window.
        
        Args:
            width, height: Window dimensions
        """
        pygame.init()
        
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Splendor - AI Battle")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game state
        self.game_state: Optional[GameState] = None
        
        # UI components
        self.logger = LoggerWidget(950, 20, 430, 400)
        
        # Control state
        self.auto_play = False
        self.game_speed = 1.0  # Seconds per turn
        self.paused = False
        
        # Fonts
        self.font_large = pygame.font.Font(None, 32)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        
        # Button areas (x, y, width, height)
        self.btn_start = (50, self.height - 60, 120, 40)
        self.btn_next = (190, self.height - 60, 120, 40)
        self.btn_auto = (330, self.height - 60, 120, 40)
        self.slider_area = (500, self.height - 50, 300, 20)
    
    def start_game(self, game_state: GameState):
        """
        Start a new game.
        
        Args:
            game_state: Initial game state
        """
        self.game_state = game_state
        self.logger.clear()
        self.logger.add_log("Game started!")
        self.logger.add_log(f"{game_state.num_players} players")
    
    def log_move(self, player_id: int, action_desc: str):
        """
        Log a move to the widget.
        
        Args:
            player_id: Player who made the move
            action_desc: Description of the action
        """
        self.logger.add_log(f"P{player_id + 1}: {action_desc}")
    
    def draw_board(self):
        """Draw the game board (cards, gems, nobles)."""
        if not self.game_state:
            return
        
        # Nobles
        noble_x = 50
        noble_y = 50
        self.font_medium.render("Nobles:", True, TEXT_COLOR)
        for noble in self.game_state.nobles:
            draw_noble(self.screen, noble, noble_x, noble_y)
            noble_x += 85
        
        # Cards - Tier 3
        tier_y = 150
        tier_label = self.font_medium.render("Tier 3", True, TEXT_COLOR)
        self.screen.blit(tier_label, (50, tier_y))
        card_x = 150
        for card in self.game_state.visible_tier3:
            draw_card(self.screen, card, card_x, tier_y)
            card_x += 95
        
        # Cards - Tier 2
        tier_y = 270
        tier_label = self.font_medium.render("Tier 2", True, TEXT_COLOR)
        self.screen.blit(tier_label, (50, tier_y))
        card_x = 150
        for card in self.game_state.visible_tier2:
            draw_card(self.screen, card, card_x, tier_y)
            card_x += 95
        
        # Cards - Tier 1
        tier_y = 390
        tier_label = self.font_medium.render("Tier 1", True, TEXT_COLOR)
        self.screen.blit(tier_label, (50, tier_y))
        card_x = 150
        for card in self.game_state.visible_tier1:
            draw_card(self.screen, card, card_x, tier_y)
            card_x += 95
        
        # Gem bank (moved to the right of cards)
        draw_gem_bank(self.screen, self.game_state.gem_bank, 540, 150)
    
    def draw_players(self):
        """Draw player areas."""
        if not self.game_state:
            return
        
        player_area_y = 520
        player_area_height = 140
        
        for i in range(self.game_state.num_players):
            is_current = (i == self.game_state.current_player)
            
            draw_player_area(
                self.screen,
                player_id=i,
                gems=dict(self.game_state.player_gems[i]),
                bonuses=dict(self.game_state.player_bonuses[i]),
                points=self.game_state.player_points[i],
                cards=self.game_state.player_cards[i],
                nobles=self.game_state.player_nobles[i],
                x=50,
                y=player_area_y + i * (player_area_height + 10),
                width=880,
                height=player_area_height,
                is_current=is_current
            )
    
    def draw_controls(self):
        """Draw control buttons and speed slider."""
        # Start button
        btn_color = (100, 200, 100) if self.game_state is None else (150, 150, 150)
        pygame.draw.rect(self.screen, btn_color, self.btn_start, border_radius=5)
        pygame.draw.rect(self.screen, TEXT_COLOR, self.btn_start, 2, border_radius=5)
        start_text = self.font_small.render("Start Game", True, TEXT_COLOR)
        self.screen.blit(start_text, (self.btn_start[0] + 15, self.btn_start[1] + 12))
        
        # Next Turn button
        btn_color = (100, 150, 200) if self.game_state and not self.auto_play else (150, 150, 150)
        pygame.draw.rect(self.screen, btn_color, self.btn_next, border_radius=5)
        pygame.draw.rect(self.screen, TEXT_COLOR, self.btn_next, 2, border_radius=5)
        next_text = self.font_small.render("Next Turn", True, TEXT_COLOR)
        self.screen.blit(next_text, (self.btn_next[0] + 20, self.btn_next[1] + 12))
        
        # Auto-play toggle
        btn_color = (200, 100, 100) if self.auto_play else (100, 100, 200)
        pygame.draw.rect(self.screen, btn_color, self.btn_auto, border_radius=5)
        pygame.draw.rect(self.screen, TEXT_COLOR, self.btn_auto, 2, border_radius=5)
        auto_text = self.font_small.render("Auto: ON" if self.auto_play else "Auto: OFF", 
                                          True, TEXT_COLOR)
        self.screen.blit(auto_text, (self.btn_auto[0] + 25, self.btn_auto[1] + 12))
        
        # Speed slider
        slider_x, slider_y, slider_w, slider_h = self.slider_area
        pygame.draw.rect(self.screen, (200, 200, 200), self.slider_area, border_radius=3)
        pygame.draw.rect(self.screen, TEXT_COLOR, self.slider_area, 2, border_radius=3)
        
        # Slider handle
        handle_pos = slider_x + int((self.game_speed / 3.0) * slider_w)
        pygame.draw.circle(self.screen, (100, 100, 200), (handle_pos, slider_y + slider_h // 2), 10)
        
        # Speed label
        speed_label = self.font_small.render(f"Speed: {self.game_speed:.1f}s", True, TEXT_COLOR)
        self.screen.blit(speed_label, (slider_x + slider_w + 20, slider_y))
    
    def draw(self):
        """Draw the entire window."""
        self.screen.fill(BG_COLOR)
        
        if self.game_state:
            self.draw_board()
            self.draw_players()
        else:
            # Welcome message
            welcome = self.font_large.render("Splendor AI Battle", True, TEXT_COLOR)
            welcome_rect = welcome.get_rect(center=(self.width // 2, self.height // 2 - 50))
            self.screen.blit(welcome, welcome_rect)
            
            instruction = self.font_medium.render("Click 'Start Game' to begin", True, TEXT_COLOR)
            inst_rect = instruction.get_rect(center=(self.width // 2, self.height // 2 + 10))
            self.screen.blit(instruction, inst_rect)
        
        self.logger.draw(self.screen)
        self.draw_controls()
        
        pygame.display.flip()
    
    def handle_click(self, pos):
        """
        Handle mouse click events.
        
        Args:
            pos: Mouse position (x, y)
        
        Returns:
            Event type string or None
        """
        x, y = pos
        
        # Check buttons
        if self._point_in_rect(pos, self.btn_start):
            return "start_game"
        elif self._point_in_rect(pos, self.btn_next):
            if self.game_state and not self.auto_play:
                return "next_turn"
        elif self._point_in_rect(pos, self.btn_auto):
            self.auto_play = not self.auto_play
            return "toggle_auto"
        elif self._point_in_rect(pos, self.slider_area):
            # Adjust speed
            slider_x = self.slider_area[0]
            slider_w = self.slider_area[2]
            ratio = (x - slider_x) / slider_w
            self.game_speed = max(0.1, min(3.0, ratio * 3.0))
            return "adjust_speed"
        
        return None
    
    def _point_in_rect(self, point, rect):
        """Check if point is inside rectangle."""
        x, y = point
        rx, ry, rw, rh = rect
        return rx <= x <= rx + rw and ry <= y <= ry + rh
    
    def handle_events(self):
        """
        Handle pygame events.
        
        Returns:
            Event type string or None
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return "quit"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    return self.handle_click(event.pos)
                elif event.button == 4:  # Scroll up
                    self.logger.scroll_up()
                elif event.button == 5:  # Scroll down
                    self.logger.scroll_down()
        
        return None
    
    def update(self):
        """Update window (called each frame)."""
        self.clock.tick(60)  # 60 FPS
    
    def quit(self):
        """Clean up and quit."""
        pygame.quit()
        sys.exit()
