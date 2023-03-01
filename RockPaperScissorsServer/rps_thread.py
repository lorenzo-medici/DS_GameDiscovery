import logging
import socket


def game_thread(players, logger):
    try:
        while game_loop(players, logger):
            pass
    except OSError:
        pass

    logger.log(level=logging.INFO, msg='Thread terminated')


def game_loop(players, logger):
    objective = 3

    p1 = players[0]
    p2 = players[1]

    p1_wins = 0
    p2_wins = 0

    while p1_wins < 3 and p2_wins < 3:
        try:
            p1_move = ask_for_move(p1, [p1_wins, p2_wins])
        except (socket.timeout, socket.error):
            logger.log(level=logging.WARN, msg='Game terminated, player 1 not responding')
            p1.shutdown(socket.SHUT_RDWR)
            p1.close()
            p2.shutdown(socket.SHUT_RDWR)
            p2.close()
            return False

        try:
            p2_move = ask_for_move(p2, [p2_wins, p1_wins])
        except (socket.timeout, socket.error):
            logger.log(level=logging.WARN, msg='Game terminated, player 2 not responding')
            p1.shutdown(socket.SHUT_RDWR)
            p1.close()
            p2.shutdown(socket.SHUT_RDWR)
            p2.close()
            return False

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

    return (winner_dec == loser_dec) and winner_dec


def play_again(player, winner):
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
    while True:
        player.sendall(f'Your score: {wins[0]}\nOpponent\'s score: {wins[1]}\n'
                       f'Input your next move [rock, paper, scissors]: '.encode())

        move = player.recv(1024).decode().strip()

        if move in ['rock', 'paper', 'scissors']:
            return move
