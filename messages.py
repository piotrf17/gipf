import struct

def Unpack(data):
    cmd = data[0:2]
    if cmd == 'JG':
        msg = JoinGame()
    elif cmd == 'TM':
        msg = TryMove()
    elif cmd == 'QG':
        msg = QuitGame()
    elif cmd == 'SD':
        msg = Shutdown()
    elif cmd == 'SG':
        msg = StartGame()
    elif cmd == 'MM':
        msg = MakeMove()
    elif cmd == 'DW':
        msg = DeclareWinner()
    else:
        raise ValueError
    msg.Unpack(data[2:])
    return msg

# Client -> Server messages

class JoinGame(object):
    def __init__(self):
        self.player_name = ''

    def Pack(self):
        cmd = 'JG'
        data = self.player_name
        return cmd + data

    def Unpack(self, data):
        self.player_name = data


class TryMove(object):
    def __init__(self):
        self.letter = 0
        self.number = 0
        self.direction = 0

    def Pack(self):
        cmd = 'TM'
        data = struct.pack('bbb', 
                           self.letter, 
                           self.number, 
                           self.direction)
        return cmd + data
    
    def Unpack(self, data):
        (self.letter, 
         self.number, 
         self.direction) = struct.unpack('bbb', data)


class QuitGame(object):
    def Pack(self):
        cmd = 'QG'
        return cmd

    def Unpack(self, data):
        pass


class Shutdown(object):
    def Pack(self):
        cmd = 'SD'
        return cmd
        
    def Unpack(self, data):
        pass

# Server -> Client messages

class StartGame(object):
    def __init__(self):
        self.color = 0
        
    def Pack(self):
        cmd = 'SG'
        data = struct.pack('b', self.color)
        return cmd + data

    def Unpack(self, data):
        (self.color,) = struct.unpack('b', data)

class MakeMove(object):
    def __init__(self):
        self.letter = 0
        self.number = 0
        self.direction = 0
        self.color = 0

    def Pack(self):
        cmd = 'MM'
        data = struct.pack('bbbb', 
                           self.letter, 
                           self.number, 
                           self.direction,
                           self.color)
        return cmd + data
    
    def Unpack(self, data):
        (self.letter, 
         self.number, 
         self.direction,
         self.color) = struct.unpack('bbbb', data)

class DeclareWinner(object):
    def __init__(self):
        self.winner = 0

    def Pack(self):
        cmd = 'DW'
        data = struct.pack('b', self.winner)
        return cmd + data

    def Unpack(self, data):
        (self.winner,) = struct.unpack('b', data)
