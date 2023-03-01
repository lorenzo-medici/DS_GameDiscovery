import logging
import os
import socket
import threading
from threading import Timer, Thread

import rps_thread

# CONSTANTS

serverName = 'Rock-Paper-Scissors'

localAddress = '127.0.0.1'
localPort = 20100

brokerAddress = '127.0.0.1'
brokerPort = 20000

N_PLAYERS = 2

MAX_REGISTRATION_TRIES = 3

SECONDS_TIMEOUT = 60

N_MINUTES = 4

# LOGGING

logging.basicConfig(filename=f'{os.getpid()}.log',
                    format='%(asctime)s:%(process)d:%(name)s:%(levelname)s:%(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S%z',
                    level=logging.DEBUG)
logger = logging.getLogger('RPSServer')


# CONNECTING TO BROKER

# Perpetual timer with set delay
# SOURCE: https://stackoverflow.com/a/48741004
class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


def register_on_broker():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(SECONDS_TIMEOUT)

        sock.bind((localAddress, localPort))

        success = False
        for i in range(0, MAX_REGISTRATION_TRIES):
            sock.sendto(bytes(serverName + "\n", "utf-8"), (brokerAddress, brokerPort))

            try:
                received = str(sock.recv(1024), "utf-8")
                match received:
                    case "okay":
                        logger.log(level=logging.INFO, msg='Registered on Broker')
                    case "taken":
                        logger.log(level=logging.WARN, msg='Name already taken on Broker')
                    case "renewed":
                        logger.log(level=logging.INFO, msg='Renewed on Broker')
                success = True
                break
            except socket.timeout:
                logger.log(level=logging.DEBUG, msg=f'Try number {i + 1} failed')
                continue
            except KeyboardInterrupt:
                return

        if not success:
            logger.log(level=logging.WARN, msg='Could not connect to Broker')


# register_on_broker()

timer = RepeatTimer(N_MINUTES * 60, register_on_broker)
timer.start()

# HANDLING CLIENT CONNECTIONS

conns = []

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((localAddress, localPort))
    s.listen()
    try:
        while True:
            conn, addr = s.accept()
            logger.log(level=logging.INFO, msg='Accepted connection from Client')

            conn.settimeout(15)

            conns.append(conn)

            if len(conns) == N_PLAYERS:
                game_instance = Thread(target=rps_thread.game_thread, args=(conns, logger,))
                game_instance.start()

                logger.log(level=logging.INFO, msg='Started new game thread')

                # print(f'\n\n{conns[0]} {conns[1]}\n\n')
                # conns[0].close()
                # conns[1].close()
                # print(f'\n\n{conns[0]} {conns[1]}\n\n')

                conns = []

    except KeyboardInterrupt:

        timer.cancel()

        main_thread = threading.current_thread()
        for t in threading.enumerate():
            if t is main_thread:
                continue
            t.join()

        print("Terminated")
        logger.log(level=logging.INFO, msg="Rock-Paper-Scissors Server terminated")

# noinspection PyUnreachableCode
# class RPSServerHandler(socketserver.StreamRequestHandler):
#
#     def handle(self):
#         global conns
#
#         conns.append(self.request)
#
#         self.request.settimeout(60)
#
#         logger.log(level=logging.INFO, msg='Accepted connection from Client')
#
#         for c in conns:
#             print(f'{c}\n\n')
#
#         if len(conns) == N_PLAYERS:
#             game_instance = Thread(target=rps_thread.game_thread, args=(conns, logger,))
#             game_instance.start()
#
#             logger.log(level=logging.INFO, msg='Started new game thread')
#
#             print(f'\n\n{conns[0]} {conns[1]}\n\n')
#             # conns[0].close()
#             # conns[1].close()
#             print(f'\n\n{conns[0]} {conns[1]}\n\n')
#
#             conns = []
#
#
#
#
# try:
#     with socketserver.TCPServer((localAddress, localPort), RPSServerHandler) as server:
#         server.allow_reuse_address = True
#         server.allow_reuse_port = True
#         server.serve_forever()
# except KeyboardInterrupt:
#
#     server.shutdown()
#
#     timer.cancel()
#
#     main_thread = threading.current_thread()
#     for t in threading.enumerate():
#         if t is main_thread:
#             continue
#         t.join()
#
#     print("Terminated")
#     logger.log(level=logging.INFO, msg="Rock-Paper-Scissors Server terminated")

# def main():
#       while max_retries_not_hit():
#           try_broker_registration()
#       listen()
#       while socket . has_connection():
#           accept()
#           if n_players == needed_players:
#               launch_game_thread()


# def game_thread():
#       while player_action_needed:
#           send_request()
#           get_answer()
#           update_game_state()
#       else:
#           terminate()
