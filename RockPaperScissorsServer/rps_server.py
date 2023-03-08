"""
Scripts that launches the Rock-Paper-Scissors Server when executed
"""
import logging
import os
import socket
import sys
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

file_handler = logging.FileHandler(f'{os.getpid()}.log')
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(format='%(asctime)s:%(process)d:%(name)s:%(levelname)s:%(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S%z',
                    level=logging.DEBUG,
                    handlers=handlers)
logger = logging.getLogger('RPSServer')


# CONNECTING TO BROKER

# Perpetual timer with set delay
# SOURCE: https://stackoverflow.com/a/48741004
class RepeatTimer(Timer):
    """
    When instantiated (and run) this class repeats the function contained in self.function every
        self.interval seconds.
    """

    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


def register_on_broker():
    """
    This function attempts to register the server on the broker. Once called sends a message containing
        the name of the server to the broker, and awaits a response. The response is logged.
        Possible outcomes are 'okay', 'taken' and 'renewed'
    If the broker is not available, the connection will be attempted MAX_REGISTRATION_TRIES at intervals
        given by the socket timeout set at SECONDS_TIMEOUT seconds.
    """
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


# REPEATTIMER
# A RepeatTime is activated, periodically creating a new thread that executes register_on_broker
# This will make sure this server will not be removed from the registry if the period is smaller
#   that the broker's removal period
# It will also attempt to register if the broker is not reliable and is not responding or
#   periodically shutting down

timer = RepeatTimer(N_MINUTES * 60, register_on_broker)
timer.start()

# HANDLING CLIENT CONNECTIONS

conns = []

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((localAddress, localPort))
    s.listen()
    try:
        # The server sequentially accepts all incoming connections and stores the handles in a queue
        while True:
            conn, addr = s.accept()
            logger.log(level=logging.INFO, msg='Accepted connection from Client')

            conn.settimeout(15)

            conns.append(conn)

            # If there are enough players to start a game, then a new thread is started and
            #   the queue is emptied
            if len(conns) == N_PLAYERS:
                game_instance = Thread(target=rps_thread.game_thread, args=(conns, logger,))
                game_instance.start()

                logger.log(level=logging.INFO, msg='Started new game thread')

                conns = []

    except KeyboardInterrupt:

        # Stopping the timer and waiting for all game threads to finish before terminating
        timer.cancel()

        main_thread = threading.current_thread()
        for t in threading.enumerate():
            if t is main_thread:
                continue
            t.join()

        print("Terminated")
        logger.log(level=logging.INFO, msg="Rock-Paper-Scissors Server terminated")
