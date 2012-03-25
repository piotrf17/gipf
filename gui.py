"""
GUI classes for the GIPF game.
"""

import gipf
import math
import pygame

def DrawText(string, size, pos, color = (255, 255, 255)):
    """Draw the text in string at the pos tuple (x, y)."""
    surface = pygame.display.get_surface()
    font = pygame.font.Font(None, size)
    text = font.render(string, 1, color)
    textpos = text.get_rect()
    textpos.topleft = pos
    surface.blit(text, textpos)


class DrawableBoard(object):
    """A drawable representation of the GIPF board."""

    def __init__(self, board, window):
        self.board = board
        self.window = window
        self.scale = 0.8

    def Draw(self):        
        self._DrawBoard()
        self._DrawPieces()

    def BoardToWindow(self, letter, number):
        window_x, window_y = self.window.get_size()
        cx = 0.5*window_x
        cy = 0.5*window_y
        h = self.scale*window_y
        
        dx = h*math.sqrt(3.0)/16.0
        x = (letter-4)*dx
        dy = h/16.0
        y = -(number-4)*h/8.0 - abs(letter-4)*dy;
        return (int(x+cx), int(y+cy))

    def TriggerRadius(self):
        window_x, window_y = self.window.get_size()
        h = self.scale*window_y
        return int(h/50.0)
    
    def PieceRadius(self):
        window_x, window_y = self.window.get_size()
        h = self.scale*window_y
        return int(h/25.0)

    def _DrawBoard(self):
        window_x, window_y = self.window.get_size()
        cx = 0.5*window_x
        cy = 0.5*window_y
        h = self.scale*window_y

        def Rotate(p, angle):
            s = math.sin(angle)
            c = math.cos(angle)
            return [c*p[0]-s*p[1], s*p[0]+c*p[1]]

        def DrawLineSet(angle):
            trigger_radius = self.TriggerRadius()
            for i in range(1, 8):
                dx = h*math.sqrt(3.0)/16.0
                x = (i-4)*dx
                dy = h/16.0
                y = h/2.0 - abs(i-4)*dy
            
                p1 = Rotate([x, -y], angle)
                p2 = Rotate([x, +y], angle)
                p1[0] = int(p1[0]+cx)
                p2[0] = int(p2[0]+cx)
                p1[1] = int(p1[1]+cy)
                p2[1] = int(p2[1]+cy)

                pygame.draw.line(self.window, (255, 255, 255), p1, p2)
                pygame.draw.circle(self.window, (255, 255, 255), p1, trigger_radius)
                pygame.draw.circle(self.window, (255, 255, 255), p2, trigger_radius)

        DrawLineSet(0.0)
        DrawLineSet(math.pi/3.0)
        DrawLineSet(-math.pi/3.0)

    def _DrawPieces(self):
        for letter in range(9):
            for number in range(9-abs(letter-4)):
                color = self.board.pieces[letter][number]
                if color:
                    self._DrawPiece(color, letter, number)

    def _DrawPiece(self, color, letter, number):
        window_x, window_y = self.window.get_size()
        h = self.scale*window_y
        piece_radius = self.PieceRadius()
        
        p = self.BoardToWindow(letter, number)
        
        if color == gipf.Board.BLACK:
            pygame.draw.circle(self.window, (255, 255, 255), p, piece_radius, 1)
            pygame.draw.circle(self.window, (0, 0, 0), p, piece_radius-1)
        elif color == gipf.Board.WHITE:
            pygame.draw.circle(self.window, (0, 0, 0), p, piece_radius, 1)
            pygame.draw.circle(self.window, (255, 255, 255), p, piece_radius-1)


class MouseableBoard(object):
    """Mediates mouse interactions with a drawable board."""

    def __init__(self, draw_board, window):
        self.draw_board = draw_board
        self.window = window

        # Triggers for where mouse can move over and create a
        # highlight.  trigger = (board_pos, window_pos)
        self.triggers = []
        for i in range(9):
            self.triggers.append(((i,0), draw_board.BoardToWindow(i, 0)))
            self.triggers.append(((i,8-abs(i-4)),
                                  draw_board.BoardToWindow(i, 8-abs(i-4))))
        for i in range(1,4):
            self.triggers.append(((0,i), draw_board.BoardToWindow(0, i)))
            self.triggers.append(((8,i), draw_board.BoardToWindow(8, i)))

        self.last_highlight = None

    def MouseMotion(self, pos):
        trigger_radius = self.draw_board.TriggerRadius()
        current_highlight = None
        for trigger in self.triggers:
            dist2 = (pos[0]-trigger[1][0])*(pos[0]-trigger[1][0])+(pos[1]-trigger[1][1])*(pos[1]-trigger[1][1])
            if dist2 < trigger_radius*trigger_radius:
                current_highlight = trigger
                break

        if self.last_highlight:
            pygame.draw.circle(self.window, (255, 255, 255), self.last_highlight[1], trigger_radius)  
            self.last_highlight = None
        if current_highlight:
            pygame.draw.circle(self.window, (0, 255, 0), current_highlight[1], trigger_radius)          
            self.last_highlight = current_highlight

    def GetMouseBoardPosition(self):
        if self.last_highlight:
            return self.last_highlight[0]
        else:
            return None
