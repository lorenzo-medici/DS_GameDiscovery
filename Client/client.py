"""
Scripts that launches the Client when executed
"""
import logging
import os
import socket
import sys

import validators
from validators import ValidationFailure

# CONSTANTS

if len(sys.argv) != 3:
    print('Invalid arguments. Usage: [client <brokerAddress> <brokerPort>]')
    exit(-1)

brokerAddress = sys.argv[1]

try:
    brokerPort = int(sys.argv[2])
except ValueError:
    print('Invalid port argument')
    exit(-1)


# GLOBAL VARIABLES

manual_address = False
query_broker = False
valid_address = False

user_retries = True
connected_to_server = False

server_address = None

# LOGGING

# create logs folder
if not os.path.exists('./logs'):
    os.makedirs('./logs')

logging.basicConfig(filename=f'logs/{os.getpid()}.log',
                    format='%(asctime)s:%(process)d:%(name)s:%(levelname)s:%(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S%z',
                    level=logging.DEBUG)
logger = logging.getLogger('Client')


# EXIT CODES
# -1    user inputs EOF of terminates process manually (EOFError, KeyboardInterrupt)
# -2    user chooses not to retry connection to the server
# -3    game ends because the server stops responding

def _query_broker():
    """
    This function queries the Broker and returns the result.
    :return: A list of pairs containing the name of the server in the first element,
        and the pair of address string and integer port in the second element; and a bool.
        If the broker is not available an empty list is returned and the bool is False.
        If the broker is available with no registered servers an empty list is returned
            and the bool is True.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(2)
        sock.sendto(bytes("query" + "\n", "utf-8"), (brokerAddress, brokerPort))

        try:
            received = str(sock.recv(1024), "utf-8")
        except (socket.timeout, socket.error):
            # Broker not available
            return [], False
        except KeyboardInterrupt:
            logger.log(level=logging.INFO, msg='User terminated the process')
            exit(-1)

    # If response is empty there aren't servers registered
    if len(received) == 0:
        return [], True

    # Parsing the response
    s_strings = received.split('$')
    s_tuples = [serv.split('|') for serv in s_strings]

    # return [(<str:name>, (<str:addr>, <int:port>)], True
    return [(serv[0], (serv[1], int(serv[2]))) for serv in s_tuples], True


def _valid_addr(address_tuple):
    """
    Checks if the given tuple is valid in terms of address and port. The first element of the tuple
        has to be either a valid ipv4 address or a valid hostname, the second has to be a string
        representing an integer in the range [1024, 49151] for user defined ports.
    :param address_tuple: A tuple containing two strings, an address and a port
    :return: If the tuple is not valid, False and an empty tuple are returned.
        If the tuple is valid, True is returned as well as a tuple containing the address and the
            port converted to integer
    """
    if len(address_tuple) != 2:
        return False, ()

    # Check if the port is integer and in valid range
    try:
        port = int(address_tuple[1])

        if port < 1024 or port > 49151:
            return False, ()
    except ValueError:
        return False, ()

    try:
        if validators.domain(address_tuple[0]):
            return True, (address_tuple[0], port)
        if validators.ip_address.ipv4(address_tuple[0]):
            return True, (address_tuple[0], port)
    except ValidationFailure:
        return False, ()


def _get_input_address():
    """
    Asks the user for a valid pair of address and port. Uses _valid_addr for validation.
    :return: A tuple containing the address (stirng) and port (int)
    """
    while True:
        try:
            input_addr = input("Input the desired server's address and port separated by a space: ")
        except (EOFError, KeyboardInterrupt):
            logger.log(level=logging.INFO, msg='User terminated the process')
            exit(-1)

        addr = input_addr.split(' ', maxsplit=1)

        is_valid = _valid_addr(addr)
        if is_valid[0]:
            return is_valid[1]
        else:
            print('Invalid address and/or port inserted')


# SCRIPT START

# OBTAINING A SERVER ADDRESS
# The user is prompted to either query the broker or input a server address
# If the query is successful, the user is asked to choose one of the available servers
# If the query is unsuccessful (Broker doesn't respons or no servers are registered), the
#   user is asked to enter a server address anyway
# After the loop, server_address should contain a tuple of address (string) and port (int)
while not valid_address:

    query_broker = False
    manual_address = False

    try:
        choice = input("Choose:\n [1] Query the broker\n [2] Manually input an address\nYour choice: ")
    except (EOFError, KeyboardInterrupt):
        logger.log(level=logging.INFO, msg='User terminated the process')
        exit(-1)

    if choice == '1':
        query_broker = True
    elif choice == '2':
        manual_address = True
    else:
        print('Invalid input not in [1, 2]')
        continue

    if query_broker:
        servers, valid_response = _query_broker()

        if not valid_response:
            print("Broker not available, please try again or manually input a server address.")
            logger.log(level=logging.WARN, msg='Broker not available')
            continue

        if len(servers) == 0:
            print("No servers registered, please try again or manually input a server address.")
            logger.log(level=logging.INFO, msg='No servers on Broker')
            continue

        while not valid_address:
            print("Servers currently available:")
            for i, s in enumerate(servers):
                print(f" [{i + 1}]:\t{s[0]}")

            try:
                n = input("Choose the server you want to connect to: ")
                index = int(n)
            except (EOFError, KeyboardInterrupt):
                logger.log(level=logging.INFO, msg='User terminated the process')
                exit(-1)
            except ValueError:
                print("Please type a number from the list")
                continue

            if 1 <= index <= len(servers):
                print(f"Chosen {servers[index - 1][0]}. Will attempt connection...")
                server_address = servers[index - 1][1]
                valid_address = True
            else:
                print("Please type a number from the list")
                continue

    if manual_address:
        server_address = _get_input_address()
        print("Will attempt connection to chosen server...")
        valid_address = True

# GAME LOOP
# At this point the server_address variable contains the pair (addr, port)
logger.log(level=logging.INFO, msg=f'Chosen server at address {server_address[0]}:{server_address[1]}')

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(None)

    # Attempts connection to the server until a connection is established or the user
    #   decides to stop attempting
    while not connected_to_server:
        try:
            s.connect(server_address)
            connected_to_server = True
            print("Connected to server!")
            logger.log(level=logging.INFO, msg='Connected to server')
        except (socket.timeout, socket.error):
            choice = input("Cannot connect to the server. Do you want to try again? [y/n]: ")
            logger.log(level=logging.WARN, msg='Cannot connect to chosen Server')
            if choice != 'y':
                print("Terminating...")
                logger.log(level=logging.INFO, msg='User terminated the process')
                exit(-2)
        except KeyboardInterrupt:
            print("Terminating...")
            logger.log(level=logging.INFO, msg='User terminated the process')
            exit(-1)

    # A connection to the server is established
    # Each message coming from the server is displayed to the user, the user's response
    #   is read from stdin and sent to the server
    # This stops when the user terminates the process or the connection is closed
    while True:
        try:
            prompt = s.recv(1024).decode('utf-8')

            # Server has closed the connection
            if prompt == '':
                raise socket.timeout

            move = input(prompt)
            s.sendall(move.encode('utf-8'))
        except (socket.timeout, socket.error):
            print("Server stopped responding, terminating...")
            logger.log(level=logging.INFO, msg='Connectino with the Server was closed')
            exit(-3)
        except (EOFError, KeyboardInterrupt):
            print("Terminating...")
            logger.log(level=logging.INFO, msg='User terminated the process')
            exit(-1)
