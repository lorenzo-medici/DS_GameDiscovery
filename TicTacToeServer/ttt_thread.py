"""
This module contains the game logic for the Tic-Tac-Toe server
"""
import logging
import socket


def game_thread(players, logger):
    """
    This function is called when the new thread is launched. It will run a new game unless
        the players communicate otherwise
    :param players: a list containing two player connections
    :param logger: The logger object to use in these functions
    """
    try:
        while game_loop(players, logger):
            pass
    except OSError:
        pass
    finally:
        players[0].shutdown(socket.SHUT_RDWR)
        players[0].close()
        players[1].shutdown(socket.SHUT_RDWR)
        players[1].close()

    logger.log(level=logging.INFO, msg='Thread terminated')


def game_has_winner(board):
    """
    This function detects whether the current board has a winner
    :param board: 3x3 matrix representing the board
    :return: boolean meaning whether a player has won
    """

    if board[0][0] == board[0][1] == board[0][2] != '-' or \
            board[1][0] == board[1][1] == board[1][2] != '-' or \
            board[2][0] == board[2][1] == board[2][2] != '-' or \
            board[0][0] == board[1][0] == board[2][0] != '-' or \
            board[0][1] == board[1][1] == board[2][1] != '-' or \
            board[0][2] == board[1][2] == board[2][2] != '-' or \
            board[0][0] == board[1][1] == board[2][2] != '-' or \
            board[0][2] == board[1][1] == board[2][0] != '-':
        return True


def game_finished(board):
    """
    Returns if the game has ended, either because a player has won, or because there are no free spaces left
    :param board: 3x3 matrix representing the board
    :return: boolean meaning whether the game has neded
    """

    if game_has_winner(board):
        return True

    for row in board:
        for cell in row:
            if cell == '-':
                return False

    return True


def game_loop(players, logger):
    """
    This function executes a single game of Tic-Tac-Toe.
    Each turn player_1 is shown the current board and asked for their move. The same then happens for
        player_2. This happens until one player wins or the board is full.
    Then, both players are asked if they want to play again. If both want to then True
        is returned
    :param players: a list containing two player connections
    :param logger: The logger object to use in these functions
    :return: A bool representing whether the players want to play again
    """
    board = [
        ['-', '-', '-'],
        ['-', '-', '-'],
        ['-', '-', '-']
    ]

    p1 = players[0]
    p2 = players[1]

    winner = 0
    loser = 0

    while not game_finished(board):

        # Ask player_1 for their move
        try:
            p1_move = ask_for_move(p1, board, 'X')
        except (socket.timeout, socket.error):
            logger.log(level=logging.WARN, msg='Game terminated, player 1 not responding')
            p1.shutdown(socket.SHUT_RDWR)
            p1.close()
            p2.shutdown(socket.SHUT_RDWR)
            p2.close()
            return False

        board[p1_move[0]][p1_move[1]] = 'X'

        if game_has_winner(board):
            winner = 1
            loser = 2
            break
        elif game_finished(board):
            break

        # Ask player_2 for their move
        try:
            p2_move = ask_for_move(p2, board, 'O')
        except (socket.timeout, socket.error):
            logger.log(level=logging.WARN, msg='Game terminated, player 2 not responding')
            p1.shutdown(socket.SHUT_RDWR)
            p1.close()
            p2.shutdown(socket.SHUT_RDWR)
            p2.close()
            return False

        board[p2_move[0]][p2_move[1]] = 'O'

        if game_has_winner(board):
            winner = 2
            loser = 1
            break
        elif game_finished(board):
            break

    try:
        if winner == 0:
            winner_dec = play_again(p1, 'D')
            loser_dec = play_again(p2, 'D')
        else:
            winner_dec = play_again(players[winner - 1], 'W')
            loser_dec = play_again(players[loser - 1], 'L')
    except (socket.timeout, socket.error):
        logger.log(level=logging.WARN, msg='Game terminated, players not responding')
        p1.shutdown(socket.SHUT_RDWR)
        p1.close()
        p2.shutdown(socket.SHUT_RDWR)
        p2.close()
        return False

    return (winner_dec == loser_dec) and (winner_dec == 'yes')


def play_again(player, winner):
    """
    This function asks a player whether they want to play another game.
    :param player: A socket connection
    :param winner: A one charcter string representing the end condition of the game ('W': winner, 'L': loser, 'D', draw)
    :return: A string representing their decision
    """
    while True:
        message = ''
        match winner:
            case 'W':
                message = 'You won! Do you want to play again? [yes, no] '
            case 'L':
                message = 'You lost! Do you want to play again? [yes, no] '
            case 'D':
                message = 'The game was drawn! Do you want to play again? [yes, no] '

        player.sendall(message.encode())

        response = player.recv(1024).decode().strip()

        if response in ['yes', 'no']:
            return response


def ask_for_move(player, board, sign):
    """
    This function shows the current board to a player and asks for their move for
        the current turn
    :param sign: The sign of the current player
    :param player: A socket connection
    :param board: A 3x3 matrix representing the board
    :return: A pair of integers representing the row and column of the valid move
    """

    error = False

    while True:
        if error:
            error_string = 'Invalid move!\n'
        else:
            error_string = ''

        player.sendall(f'{error_string}Your sign: {sign}\nCurrent board:\n'
                       f'{board[0][0]} {board[0][1]} {board[0][2]}\n'
                       f'{board[1][0]} {board[1][1]} {board[1][2]}\n'
                       f'{board[2][0]} {board[2][1]} {board[2][2]}\n'
                       f'Your move: [11, 12, 13, 21, ... , 32, 33] '.encode())

        move = player.recv(1024).decode().strip()

        try:
            row = int(move[0]) - 1
            col = int(move[1]) - 1

            # if cell is already taken
            if board[row][col] == '-':
                return row, col
        except (IndexError, ValueError):
            pass
        finally:
            # either the spot is already taken or the move is invalid (not int, or out of bounds)
            error = True
