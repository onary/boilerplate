import random
import string
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
import tornado.template
import traceback
from itertools import cycle
from apps.core.handlers import BaseHandler
from tornado_utils.routes import route

games = []


class Game(object):
    def __init__(self):
        self.players = []
        self.state = self.add_player
        self.winner = None

    def add_player(self, player):
        self.players.append(player)
        if len(self.players) == 2:
            self.start_game()

    def start_game(self):
        self.grid = [[None, None, None],
                     [None, None, None],
                     [None, None, None]]
        # This creates a generator which cycles over the elements in a list
        self.turn_order = cycle(self.players)
        self.next_player = self.turn_order.next()
        self.winner = None
        self.broadcast({'new_game': True})

    def make_move(self, player, x, y):
        if player != self.next_player:
            player.socket.write_message({'error': 'Out of turn!'})
            return
        if self.grid[y][x] is not None:
            player.socket.write_message({'error': 'Space occupied'})
            return
        self.grid[y][x] = player.symbol
        self.broadcast({'id': '%s%s' % (x, y), 'img': player.symbol})
        self.check_winner()
        self.next_player = self.turn_order.next()

    def broadcast(self, message):
        try:
            for player in self.players:
                if player.socket:
                    player.socket.write_message(message)
        except:
            traceback.print_exc()

    def check_winner(self):
        def all_same(symbol, set):
            set = map(lambda _: _ == symbol, set)
            return all(set)

        def dead_heat():
            for x in xrange(0, 3):
                for y in xrange(0, 3):
                    if self.grid[x][y] is None:
                        return False
            return True

        for player in self.players:
            for y in xrange(0, 3):
                if all_same(player.symbol, self.grid[y]):
                    self.winner = player.symbol
            for x in xrange(0, 3):
                if all_same(player.symbol, [self.grid[0][x],
                                            self.grid[1][x],
                                            self.grid[2][x]]):
                    self.winner = player.symbol
            if all_same(player.symbol, [self.grid[0][0],
                                        self.grid[1][1],
                                        self.grid[2][2]]):
                    self.winner = player.symbol
            if all_same(player.symbol, [self.grid[0][2],
                                        self.grid[1][1],
                                        self.grid[2][0]]):
                    self.winner = player.symbol
        if self.winner:
            self.broadcast({'winner': self.winner})
            self.start_game()

        if dead_heat():
            self.broadcast({'dead_heat': True})
            self.start_game()


class Player(object):
    def __init__(self, symbol, game, socket=None):
        self.symbol = symbol
        self.socket = socket
        self.game = game
        self.game.add_player(self)

        self.id = ''.join(random.choice(string.ascii_uppercase +
                          string.digits) for _ in range(10))

    def make_move(self, x, y):
        self.game.make_move(self, x, y)


@route('/start-game', name='start_game')
class PlayerHandler(BaseHandler):
    def get(self):
        self.render('tictactoe/game.html')


@route(r'/ws', name='ws')
class PlayerWebSocket(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        self.player = None
        self.game = None
        super(PlayerWebSocket, self).__init__(*args, **kwargs)

    def open(self):
        for game in games:
            if len(game.players) == 1:
                self.player = Player('O', game, self)
                self.game = game

        if self.player is None:
            self.game = Game()
            self.player = Player('X', self.game, self)
            games.append(self.game)

        print self.player.symbol, self.player.id

        self.write_message({'symbol': self.player.symbol})

    def on_message(self, message):
        try:
            x, y = map(int, message.split(','))
            self.player.make_move(x, y)
        except Exception, e:
            print e

        print self.player.id

    def on_close(self):
        try:
            games.remove(self.game)
        except Exception, e:
            print e

        print "WebSocket closed"
