#!/usr/bin/env python

import math
import messages
import numpy
import socket
import string
import sys
import threading

# import and init pygame
import pygame
pygame.init()

import gipf
import gui

class Events(object):
    """User events in the pygame loop."""
    NETWORKMSG = pygame.USEREVENT


class ServerConnection(object):
    """Wrapper around socket connection to the server."""
    def __init__(self):
        self.HOST, self.PORT = "localhost", 2222
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __del__(self):
        self._socket.send(messages.Shutdown())
        self._socket.close()

    def SetHostAndPort(self, argv):
        if len(argv) > 2:
            host_port = argv[2].split(':')
            self.HOST = host_port[0]
            if len(host_port) > 1:
                self.PORT = host_port[1]

    def Connect(self):
        try:
            self._socket.connect((self.HOST, self.PORT))
        except socket.error:
            print 'Failed to connect to server, bailing.'
            print '  host = ', self.HOST
            print '  port = ', self.PORT
            sys.exit(1)

    def SendReadyForStart(self, player_name):
        msg = messages.JoinGame()
        msg.player_name = player_name
        self._socket.send(msg.Pack())
    
    def Send(self, msg):
        self._socket.send(msg.Pack())
        
    def Receive(self):
        data = self._socket.recv(1024)
        msg = messages.Unpack(data)
        return msg


class ServerListener(threading.Thread):
    """Provides a thread that listens for server messages."""

    def __init__(self, server_conn):
        super(ServerListener, self).__init__()
        self._server_conn = server_conn

    def run(self):
        while True:
            msg = self._server_conn.Receive()
            network_event = pygame.event.Event(Events.NETWORKMSG, msg = msg)
            # I'm under the impression that event.post is thread-safe,
            # though I'm not completely certain.  I know that any sort
            # of event get/poll should only happen in the main thread.
            pygame.event.post(network_event)


class Game(object):
    """A game is the main object for the client app."""

    # states
    WAITING_FOR_GAME = 1
    WAITING_FOR_PLAYER = 2
    WAITING_FOR_SERVER = 3
    PLACING_PIECE = 4
    CHOOSING_DIRECTION = 5
    GAME_OVER = 6

    def __init__(self, conn):
        self._window = pygame.display.set_mode((800,600))
        self._conn = conn

        self._board = gipf.Board()
        self._draw_board = gui.DrawableBoard(self._board, self._window)
        self._mouse_board = gui.MouseableBoard(self._draw_board, self._window)

        self._state = self.WAITING_FOR_GAME
        self.Redraw()

    def Redraw(self):
        surface = pygame.display.get_surface()
        surface.fill((0, 0, 0))

        if self._state == self.WAITING_FOR_GAME:
            gui.DrawText("Waiting for game to start...",
                         48, (200, 250))
        elif self._state == self.GAME_OVER:
            if self._winner == self._color:
                text = "You Won :D"
            else:
                text = "You Lost :("
            gui.DrawText(text, 48, (200, 250))
        else:
            self._draw_board.Draw()

            # Write number of pieces remaining for each player.
            gui.DrawText("White: %d"%self._board.white_pieces,
                         28, (25, 50))
            gui.DrawText("Black: %d"%self._board.black_pieces,
                         28, (self._window.get_size()[0]-100, 50))
            # Write your color and who's turn it is.
            your_color = 'WHITE' if self._color == gipf.Board.WHITE else 'BLACK'
            their_color = 'WHITE' if self._color == gipf.Board.BLACK else 'BLACK'
            state_msg = 'You are ' + your_color + ' and turn is '
            if self._state == self.WAITING_FOR_PLAYER:
                state_msg += their_color
            else:
                state_msg += your_color
            gui.DrawText(state_msg, 28, 
                         (25, self._window.get_size()[1]-25))

        pygame.display.flip()

    def SetupDirectionLines(self, mouse_pos, board_pos, directions):
        root = numpy.array(self._draw_board.BoardToWindow(*board_pos))
        dir1 = numpy.array(self._draw_board.BoardToWindow(
            *self._board.NextSpot(board_pos[0], board_pos[1], directions[0])))
        dir2 = numpy.array(self._draw_board.BoardToWindow(
            *self._board.NextSpot(board_pos[0], board_pos[1], directions[1])))
        pygame.draw.line(self._window, (255, 0, 0), root, dir1, 3)
        pygame.draw.line(self._window, (255, 0, 0), root, dir2, 3)

        div_vector = (dir1-root)+(dir2-root)
        div_left = (dir1-root)-(dir2-root)
        self.dividing = (root, div_left, dir1, dir2)
        self.directions = directions
        pygame.draw.line(self._window, (100, 100, 100),
                         root-div_vector, root+div_vector)

        pygame.display.flip()

    def HighlightDirection(self, mouse_pos):
        root = self.dividing[0]
        div_left = self.dividing[1]
        dir1 = self.dividing[2]
        dir2 = self.dividing[3]
        mouse_vector = numpy.array(mouse_pos)-root        
        if numpy.dot(mouse_vector, div_left) > 0:
            pygame.draw.line(self._window, (0, 255, 0), root, dir1, 3)
            pygame.draw.line(self._window, (255, 0, 0), root, dir2, 3)
            pygame.display.flip()
            return self.directions[0]
        else:
            pygame.draw.line(self._window, (0, 255, 0), root, dir2, 3)
            pygame.draw.line(self._window, (255, 0, 0), root, dir1, 3)
            pygame.display.flip()
            return self.directions[1]

    def HandleMessage(self, msg):
        """ Handle a network message """
        if isinstance(msg, messages.StartGame):
            self._color = msg.color
            if msg.color == gipf.Board.WHITE:
                self._state = self.PLACING_PIECE
            else:
                self._state = self.WAITING_FOR_PLAYER
            self.Redraw()
        elif isinstance(msg, messages.MakeMove):
            if self._board.Move(msg.letter,
                                msg.number, 
                                msg.direction,
                                msg.color):
                self._board.Resolve(msg.color)
                if self._state == self.WAITING_FOR_SERVER:
                    self._state = self.WAITING_FOR_PLAYER
                else:
                    self._state = self.PLACING_PIECE
                self.Redraw()
            else:
                print 'FATAL: server gave bum move'
        elif isinstance(msg, messages.DeclareWinner):
            self._state = self.GAME_OVER
            self._winner = msg.winner
            self.Redraw()

    def TryMove(self, board_pos, direction):
        """ Make a move """
        move_msg = messages.TryMove()
        move_msg.letter = board_pos[0]
        move_msg.number = board_pos[1]
        move_msg.direction = direction
        self._conn.Send(move_msg)
        self._state = self.WAITING_FOR_SERVER

    def Run(self):
        """ Main game loop """
        while True:
            event = pygame.event.wait()
            # Window is closed.
            if event.type == pygame.QUIT:
                self._conn.Send(messages.QuitGame())
                return        
            # Message over the network.
            elif event.type == Events.NETWORKMSG:
                self.HandleMessage(event.msg)
            # Player moves a mouse.
            elif event.type == pygame.MOUSEMOTION:
                if self._state == self.PLACING_PIECE:
                    self._mouse_board.MouseMotion(event.pos)
                    pygame.display.flip()
                elif self._state == self.CHOOSING_DIRECTION:
                    self.HighlightDirection(event.pos)
            # Player clicks the mouse.
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Button clicks other than left click break out of things.
                if event.button != 1:
                    if self._state == self.CHOOSING_DIRECTION:
                        self._state = self.PLACING_PIECE
                        self.Redraw()
                    continue
                # Left clicks are the standard case.
                if self._state == self.PLACING_PIECE:
                    board_pos = self._mouse_board.GetMouseBoardPosition()
                    if board_pos is not None:
                        directions = self._board.PossibleDirections(
                            *board_pos)
                        if len(directions) == 1:
                            if self._board.CanMove(board_pos[0],
                                                   board_pos[1],
                                                   directions[0]):
                                self.TryMove(board_pos, directions[0])
                            else:
                                print 'INVALID MOVE'
                            self.Redraw()
                        else:
                            self.SetupDirectionLines(event.pos,
                                                     board_pos, 
                                                     directions)
                            self._state = self.CHOOSING_DIRECTION
                            self.Redraw()
                elif self._state == self.CHOOSING_DIRECTION:
                    chosen_direction = self.HighlightDirection(
                        event.pos)
                    board_pos = self._mouse_board.GetMouseBoardPosition()
                    if self._board.CanMove(board_pos[0],
                                           board_pos[1],
                                           chosen_direction):
                        self.TryMove(board_pos, chosen_direction)
                    else:
                        print 'INVALID MOVE'            


if __name__=="__main__":
    # Get the player name from command line args.
    if len(sys.argv) < 2:
        print 'usage: gipf_client.py playername [server]'
        sys.exit(1)
    player_name = sys.argv[1]

    # Establish a server connection.
    conn = ServerConnection()
    conn.SetHostAndPort(sys.argv)
    conn.Connect()

    # Create a listener thread to listen to the server.
    # Make this a daemon so that we quit on an exception
    # in the main thread.
    server_listener = ServerListener(conn)
    server_listener.daemon = True
    server_listener.start()

    conn.SendReadyForStart(player_name)

    # Run the game until we finish.
    game = Game(conn)
    game.Run()

    # Close down the server connection.
    # TODO!
