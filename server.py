import asyncio
import websockets
import json

class Game:
    def __init__(self):
        self.board = [['' for _ in range(5)] for _ in range(5)]
        self.players = {'A': [], 'B': []}
        self.current_turn = 'A'
        self.is_game_over = False

    def place_character(self, player, positions):
        if len(positions) != 5:
            return False
        row = 0 if player == 'A' else 4
        for i, char in enumerate(positions):
            if self.board[row][i] != '':
                return False
            self.board[row][i] = f"{player}-{char}"
            self.players[player].append((char, row, i))
        return True

    def move_character(self, player, char, direction):
        if self.is_game_over:
            return False

        for i, (c, row, col) in enumerate(self.players[player]):
            if c == char:
                new_row, new_col = row, col
                if char.startswith('P'):
                    if direction == 'L':
                        new_col -= 1
                    elif direction == 'R':
                        new_col += 1
                    elif direction == 'F':
                        new_row -= 1
                    elif direction == 'B':
                        new_row += 1
                elif char.startswith('H1'):
                    if direction == 'L':
                        new_col -= 2
                    elif direction == 'R':
                        new_col += 2
                    elif direction == 'F':
                        new_row -= 2
                    elif direction == 'B':
                        new_row += 2
                elif char.startswith('H2'):
                    if direction == 'FL':
                        new_row -= 2
                        new_col -= 2
                    elif direction == 'FR':
                        new_row -= 2
                        new_col += 2
                    elif direction == 'BL':
                        new_row += 2
                        new_col -= 2
                    elif direction == 'BR':
                        new_row += 2
                        new_col += 2
                
                if self.is_valid_move(new_row, new_col):
                    if self.board[new_row][new_col] != '':
                        opponent_player = 'B' if player == 'A' else 'A'
                        if self.board[new_row][new_col].startswith(opponent_player):
                            self.remove_character(opponent_player, new_row, new_col)

                    self.board[row][col] = ''
                    self.board[new_row][new_col] = f"{player}-{char}"
                    self.players[player][i] = (char, new_row, new_col)
                    self.switch_turn()
                    return True
                else:
                    return False
        return False

    def remove_character(self, player, row, col):
        char = self.board[row][col]
        self.board[row][col] = ''
        self.players[player] = [(c, r, c) for (c, r, c) in self.players[player] if not (r == row and c == col)]
        if not self.players[player]:
            self.is_game_over = True

    def is_valid_move(self, row, col):
        return 0 <= row < 5 and 0 <= col < 5 and self.board[row][col] == ''

    def switch_turn(self):
        self.current_turn = 'B' if self.current_turn == 'A' else 'A'

    def get_state(self):
        return {
            'board': self.board,
            'players': self.players,
            'current_turn': self.current_turn,
            'is_game_over': self.is_game_over
        }

async def handle_connection(websocket, path):
    game = Game()
    while True:
        try:
            message = await websocket.recv()
            data = json.loads(message)

            if data['type'] == 'initialize':
                player = data['player']
                positions = data['positions']
                success = game.place_character(player, positions)
                if not success:
                    await websocket.send(json.dumps({'type': 'error', 'message': 'Invalid placement'}))

            elif data['type'] == 'move':
                player = data['player']
                char = data['char']
                direction = data['direction']
                success = game.move_character(player, char, direction)
                if not success:
                    await websocket.send(json.dumps({'type': 'error', 'message': 'Invalid move'}))
            
            await websocket.send(json.dumps({'type': 'state', 'state': game.get_state()}))

        except websockets.ConnectionClosedError:
            print("Client disconnected unexpectedly.")
            break
        except websockets.ConnectionClosedOK:
            print("Client disconnected gracefully.")
            break

start_server = websockets.serve(handle_connection, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
