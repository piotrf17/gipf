#!/usr/bin/env python
#
# TODO:
#   factor out client connection from server

import gipf
import messages
import random
import socket
import threading

class GameState(object):
    """State of GIPF game and players joining, shared among threads"""

    # States
    WAITING_FOR_PLAYERS = 1
    PLAYING = 2

    def __init__(self):
        self._state = self.WAITING_FOR_PLAYERS
        self._player_list = []
        self._player_list_lock = threading.Lock()
        self._game_start_event = threading.Event()
        self._colors = {}
        self.board = gipf.Board()
        self.board_lock = threading.Lock()

    def _StartGame(self):
        # Assign colors to players
        if random.random() > 0.5:
            self._colors[self._player_list[0][0]] = 1
            self._colors[self._player_list[1][0]] = 2
        else:
            self._colors[self._player_list[0][0]] = 2
            self._colors[self._player_list[1][0]] = 1            
        self._game_start_event.set()

    def AddPlayer(self, player_name, handler):
        with self._player_list_lock:
            if len(self._player_list) > 1:
                return False
            self._player_list.append((player_name, handler))
            if len(self._player_list) == 2:
                self._StartGame()
        return True

    def WaitForGameStart(self, player_name):
        self._game_start_event.wait()
        color = self._colors[player_name]
        print 'START: Player', player_name, 'is color', color
        return color

    # TODO(piotrf): move this function to networking class
    def Broadcast(self, msg):
        for player in self._player_list:
            player[1].Send(msg)

class GIPFHandler(threading.Thread):

    def __init__(self, socket, game_state):
        super(GIPFHandler, self).__init__()
        self._socket = socket
        self._game_state = game_state
        self._msg_handlers = {messages.JoinGame: self._JoinGame,
                              messages.TryMove: self._TryMove,
                              messages.QuitGame: self._QuitGame,
                              messages.Shutdown: self._Shutdown}
        self._done = False

    def __del__(self):
        # TODO(piotrf): send a quitting message here
        self._socket.close()

    def _JoinGame(self, msg):
        self._player_name = msg.player_name
        print self._player_name, 'joined!'
        if not self._game_state.AddPlayer(self._player_name, self):
            self._socket.send('GF')
            self._done = True
            return
        self._color = self._game_state.WaitForGameStart(self._player_name)
        start_msg = messages.StartGame()
        start_msg.color = self._color
        self._socket.send(start_msg.Pack())

    def _TryMove(self, msg):
        with self._game_state.board_lock:
            if self._game_state.board.Move(msg.letter,
                                           msg.number,
                                           msg.direction,
                                           self._color):
                self._game_state.board.Resolve(self._color)
                winner = self._game_state.board.CheckForWinner()
                if winner:
                    win_msg = messages.DeclareWinner()
                    win_msg.winner = winner
                    self._game_state.Broadcast(win_msg)
                    self._done = True
                else:
                    move_msg = messages.MakeMove()
                    move_msg.letter = msg.letter
                    move_msg.number = msg.number
                    move_msg.direction = msg.direction
                    move_msg.color = self._color
                    self._game_state.Broadcast(move_msg)
            else:
                print self._player_name, 'made an invalid move'

    def _QuitGame(self, msg):
        print self._player_name, 'quit'
        self._done = True

    def _Shutdown(self, msg):
        print self._player_name, 'quit abruptly!'
        self._done = True

    def Send(self, msg):
        self._socket.send(msg.Pack())

    def run(self):
        while not self._done:
            data = self._socket.recv(1024).strip()
            try:
                msg = messages.Unpack(data)
                self._msg_handlers[msg.__class__](msg)
            except ValueError, KeyError:
                print 'ERROR - invalid message:', data
                self._done = True

class GIPFServer(object):

    def __init__(self):
        self.HOST = 'localhost'
        self.PORT = 2222
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._game_state = GameState()

    def __del__(self):
        self._socket.close()

    def Serve(self):
        self._socket.bind((self.HOST, self.PORT))
        self._socket.listen(1)
        while True:
            conn, addr = self._socket.accept()
            handler = GIPFHandler(conn, self._game_state)
            handler.daemon = True
            handler.start()

if __name__=="__main__":
    server = GIPFServer()
    server.Serve()
