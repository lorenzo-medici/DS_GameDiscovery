"""
This module contains the game logic for the Rock-Paper-Scissors server
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


def game_loop(players, logger):
    """
    This function executes a single game of Rock-Paper-Scissors, the first player to three points wins.
    Each turn player_1 is shown the current score and asked for their move. The same then happens for
        player_2. Then, the moves are compared and the score is adjusted.
    When one player wins, both players are asked if they want to play again. If both want to then True
        is returned
    :param players: a list containing two player connections
    :param logger: The logger object to use in these functions
    :return: A bool representing whether the players want to play again
    """
    objective = 3

    p1 = players[0]
    p2 = players[1]

    p1_wins = 0
    p2_wins = 0

    while p1_wins < 3 and p2_wins < 3:

        # Ask player_1 for their move
        try:
            p1_move = ask_for_move(p1, [p1_wins, p2_wins])
        except (socket.timeout, socket.error):
            logger.log(level=logging.WARN, msg='Game terminated, player 1 not responding')
            p1.shutdown(socket.SHUT_RDWR)
            p1.close()
            p2.shutdown(socket.SHUT_RDWR)
            p2.close()
            return False

        # Ask player_2 for their move
        try:
            p2_move = ask_for_move(p2, [p2_wins, p1_wins])
        except (socket.timeout, socket.error):
            logger.log(level=logging.WARN, msg='Game terminated, player 2 not responding')
            p1.shutdown(socket.SHUT_RDWR)
            p1.close()
            p2.shutdown(socket.SHUT_RDWR)
            p2.close()
            return False

        # Compare moves and assign point
        if p1_move == p2_move:
            continue
        elif (p1_move, p2_move) in [('rock', 'scissors'), ('scissors', 'paper'), ('paper', 'rock')]:
            p1_wins += 1
            continue
        else:
            p2_wins += 1
            continue

    if p1_wins == 3:
        winner = p1
        loser = p2
    else:
        winner = p2
        loser = p1

    # Ask both players if they want to play again
    try:
        winner_dec = play_again(winner, True)
        loser_dec = play_again(loser, False)
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
    :param winner: A bool representing if the player has won or not
    :return: A string representing their decision
    """
    while True:
        if winner:
            message = 'You won! Do you want to play again? [yes, no] '
        else:
            message = 'You lost! Do you want to play again? [yes, no] '
        player.sendall(message.encode())

        response = player.recv(1024).decode().strip()

        if response in ['yes', 'no']:
            return response


def ask_for_move(player, wins):
    """
    This function shows the current score to a player and asks for their move for
        the current turn
    :param player: A socket connection
    :param wins: A list of two items containing the wins of the player in the first
        element, and the wins of their opponent in the second element
    :return: A string representing their (valid) move
    """

    error = False

    while True:
        if error:
            error_string = 'Invalid move!\n'
        else:
            error_string = ''

        player.sendall(f'{error_string}Your score: {wins[0]}\nOpponent\'s score: {wins[1]}\n'
                       f'Input your next move [rock, paper, scissors]: '.encode())

        move = player.recv(1024).decode().strip()

        if move in ['rock', 'paper', 'scissors']:
            return move

        error = True
