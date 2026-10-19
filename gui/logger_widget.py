"""
Scrollable text log widget for move history.
"""

import pygame
from typing import List


class LoggerWidget:
    """
    Displays a scrollable text log of game moves.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int):
        """
        Initialize the logger widget.
        
        Args:
            x, y: Top-left position
            width, height: Widget dimensions
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.logs: List[str] = []
        self.scroll_offset = 0
        self.line_height = 20
        self.font = pygame.font.Font(None, 18)
        
        # Colors
        self.bg_color = (50, 55, 60)
        self.text_color = (220, 220, 220)
        self.border_color = (100, 120, 140)
    
    def add_log(self, text: str):
        """
        Add a new log entry.
        
        Args:
            text: Log message to add
        """
        self.logs.append(text)
        # Auto-scroll to bottom
        max_visible = (self.height - 50) // self.line_height
        if len(self.logs) > max_visible:
            self.scroll_offset = len(self.logs) - max_visible
    
    def clear(self):
        """Clear all logs."""
        self.logs = []
        self.scroll_offset = 0
    
    def scroll_up(self):
        """Scroll up one line."""
        if self.scroll_offset > 0:
            self.scroll_offset -= 1
    
    def scroll_down(self):
        """Scroll down one line."""
        max_visible = (self.height - 50) // self.line_height
        if self.scroll_offset < len(self.logs) - max_visible:
            self.scroll_offset += 1
    
    def draw(self, surface: pygame.Surface):
        """
        Draw the logger widget.
        
        Args:
            surface: Pygame surface to draw on
        """
        # Background
        pygame.draw.rect(surface, self.bg_color, 
                        (self.x, self.y, self.width, self.height),
                        border_radius=5)
        pygame.draw.rect(surface, self.border_color, 
                        (self.x, self.y, self.width, self.height),
                        2, border_radius=5)
        
        # Title
        title_font = pygame.font.Font(None, 24)
        title = title_font.render("Move Log", True, self.text_color)
        surface.blit(title, (self.x + 10, self.y + 10))
        
        # Log entries
        log_y = self.y + 40
        max_visible = (self.height - 50) // self.line_height
        
        visible_logs = self.logs[self.scroll_offset:self.scroll_offset + max_visible]
        
        for log_text in visible_logs:
            # Wrap long text
            if len(log_text) > 50:
                log_text = log_text[:47] + "..."
            
            text_surface = self.font.render(log_text, True, self.text_color)
            surface.blit(text_surface, (self.x + 10, log_y))
            log_y += self.line_height
        
        # Scroll indicator
        if len(self.logs) > max_visible:
            scroll_info = f"{self.scroll_offset + 1}-{min(self.scroll_offset + max_visible, len(self.logs))} / {len(self.logs)}"
            scroll_text = self.font.render(scroll_info, True, (100, 100, 100))
            surface.blit(scroll_text, (self.x + self.width - 100, self.y + 10))
