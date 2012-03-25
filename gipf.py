#!/usr/bin/env python

import math
import numpy
import string

class Board(object):
    """
    A Board describes the layout of the physical board as well as the
    player pieces.

    Board locations are given by a "letter" and number as described in the
    GIPF rules.  Both, however, are just numbers in function calls.
    """

    WHITE = 1
    BLACK = 2

    def __init__(self):
        self.black_pieces = 15
        self.white_pieces = 15
        self.pieces = [   [0,0,0,0,0],
                         [0,2,0,0,1,0],
                        [0,0,0,0,0,0,0],
                       [0,0,0,0,0,0,0,0],
                      [0,1,0,0,0,0,0,2,0],
                       [0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0],
                         [0,2,0,0,1,0],
                          [0,0,0,0,0]]
        self.rows = [
            [4, 0, 2],
            [3, 0, 2],
            [2, 0, 2],
            [1, 0, 2],
            [0, 0, 2],
            [0, 1, 2],
            [0, 2, 2],
            [0, 3, 2],
            [0, 4, 2],
            [0, 0, 3],
            [0, 1, 3],
            [0, 2, 3],
            [0, 3, 3],
            [0, 4, 3],
            [1, 5, 3],
            [2, 6, 3],
            [3, 7, 3],
            [4, 8, 3],
            [0, 0, 1],
            [1, 0, 1],
            [2, 0, 1],
            [3, 0, 1],
            [4, 0, 1],
            [5, 0, 1],
            [6, 0, 1],
            [7, 0, 1],
            [8, 0, 1]]

    def _InBoard(self, letter, number):
        """Returns true if the given (letter, number) pair is in the board."""
        if letter < 1 or letter > 7:
            return False
        if number < 1 or number > 7-abs(letter-4):
            return False
        return True

    def _SlidePieces(self, letter, number, direction):
        """Slide the pieces one spot in direction starting at (letter, number)"""
        i = letter
        j = number
        last_color = self.pieces[i][j]
        self.pieces[i][j] = 0
        next_i, next_j = self.NextSpot(i, j, direction)
        while self._InBoard(next_i, next_j):
            cur_color = self.pieces[next_i][next_j]
            self.pieces[next_i][next_j] = last_color
            if cur_color == 0:
                break
            last_color = cur_color
            next_i, next_j = self.NextSpot(next_i, next_j, direction)

    def _ResolveRowCapture(self, row, profile, color):
        """Handle capturing a row.
        
        Remove captured pieces from the board and return them
        to the capturing player.

        Args:
            row: tuple (number, letter, direction) that identifies
                one of the rows on the board.
            profile: an array of True/False that describes whether or not
                a piece on the board has been captured.
            color: the color of the capturer
        """
        k = 0
        i, j = row[0], row[1]
        next_i, next_j = self.NextSpot(i, j, row[2])            
        while self._InBoard(next_i, next_j):
            if profile[k]:
                if self.pieces[next_i][next_j] == self.WHITE:
                    if color == self.WHITE:
                        self.white_pieces += 1
                elif self.pieces[next_i][next_j] == self.BLACK:
                    if color == self.BLACK:
                        self.black_pieces += 1
                self.pieces[next_i][next_j] = 0
            k += 1
            next_i, next_j = self.NextSpot(next_i, next_j, row[2])

    def CanMove(self, letter, number, direction):
        """Can we move from (letter, number) in direction."""
        i = letter
        j = number
        next_i, next_j = self.NextSpot(i, j, direction)
        while self._InBoard(next_i, next_j):
            cur_color = self.pieces[next_i][next_j]
            if cur_color == 0:
                return True
            next_i, next_j = self.NextSpot(next_i, next_j, direction)
        return False

    def Move(self, letter, number, direction, color):
        if self.CanMove(letter, number, direction):
            self.pieces[letter][number] = color
            self._SlidePieces(letter, number, direction)
            if color == self.WHITE:
                self.white_pieces -= 1
            else:
                self.black_pieces -= 1
            return True
        else:
            return False

    def Resolve(self, color):
        def GetRowColors(row):
            colors = []
            i, j = row[0], row[1]
            next_i, next_j = self.NextSpot(i, j, row[2])            
            while self._InBoard(next_i, next_j):
                colors.append(self.pieces[next_i][next_j])
                next_i, next_j = self.NextSpot(next_i, next_j, row[2])
            return colors
        # Gather all rows with 4-sets and the profile of the capture
        captures = []
        white_string = ''.join(map(str, [self.WHITE]*4))
        black_string = ''.join(map(str, [self.BLACK]*4))
        for row in self.rows:
            colors = GetRowColors(row)
            colors_string = ''.join(map(str, colors))
            if white_string in colors_string:
                capture_color = self.WHITE
                begin, end = colors_string.split(white_string)
            elif black_string in colors_string:
                capture_color = self.BLACK
                begin, end = colors_string.split(black_string)
            else:
                continue
            color_chars = str(self.WHITE) + str(self.BLACK)
            begin = string.rstrip(begin, color_chars)
            end = string.lstrip(end, color_chars)
            capture_length = len(colors) - len(begin) - len(end)
            capture_profile = [0]*len(begin) + [1]*capture_length + [0]*len(end)
            captures.append([row, capture_profile, capture_color])
        # 1 match is easy to resolve.
        if len(captures) == 1:
            self._ResolveRowCapture(*captures[0])
        
    def PossibleDirections(self, letter, number):
        """
        Directions go from 1 through 6:
                           
                          1
                      6   |   2
                        >-o-<
                      5   |   3
                          4
        """
        dir_map = {
            (0, 0): [2],
            (1, 0): [1, 2],
            (2, 0): [1, 2],
            (3, 0): [1, 2],
            (4, 0): [1],
            (5, 0): [6, 1],
            (6, 0): [6, 1],
            (7, 0): [6, 1],
            (8, 0): [6],
            (8, 1): [5, 6],
            (8, 2): [5, 6],
            (8, 3): [5, 6],
            (8, 4): [5],
            (7, 5): [4, 5],
            (6, 6): [4, 5],
            (5, 7): [4, 5],
            (4, 8): [4],
            (3, 7): [3, 4],
            (2, 6): [3, 4],
            (1, 5): [3, 4],
            (0, 4): [3],
            (0, 3): [2, 3],
            (0, 2): [2, 3],
            (0, 1): [2, 3]
            }
        return dir_map[(letter, number)]

    def NextColor(self, color):
        if color == self.WHITE:
            return self.BLACK
        else:
            return self.WHITE

    def NextSpot(self, letter, number, direction):
        if direction == 1:
            return letter, number+1
        elif direction == 2:
            if letter < 4:
                return letter+1, number+1
            else:
                return letter+1, number
        elif direction == 3:
            if letter < 4:
                return letter+1, number
            else:
                return letter+1, number-1
        elif direction == 4:
            return letter, number-1
        elif direction == 5:
            if letter < 5:
                return letter-1, number-1
            else:
                return letter-1, number
        elif direction == 6:
            if letter < 5:
                return letter-1, number
            else:
                return letter-1, number+1

    def CheckForWinner(self):
        if self.white_pieces <= 0:
            return self.BLACK
        elif self.black_pieces <= 0:
            return self.WHITE
        else:
            return None
