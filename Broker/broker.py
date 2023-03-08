"""
Scripts that launches the Broker when executed
"""
import logging
import os
import socketserver
import sys

from registry import Registry

# LOGGING

filePath = f'logs/{os.getpid()}.log'

# create logs folder and file
if not os.path.exists('./logs'):
    os.makedirs('./logs')

open(filePath, 'a').close()

file_handler = logging.FileHandler(filePath)
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(format='%(asctime)s:%(process)d:%(name)s:%(levelname)s:%(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S%z',
                    level=logging.DEBUG,
                    handlers=handlers)
logger = logging.getLogger('Broker')

# INIZIALIZING VARIABLES

# CONSTANTS

localAddress = '0.0.0.0'

if len(sys.argv) != 2:
    logger.log(level=logging.ERROR, msg='Invalid arguments. Usage: [broker <localPort>]')
    exit(-1)

try:
    localPort = int(sys.argv[1])
except ValueError:
    logger.log(level=logging.ERROR, msg='Invalid port argument')
    exit(-1)


registry = Registry(logger)


class BrokerRequestHandler(socketserver.DatagramRequestHandler):
    """
    Class that extends a DatagramRequestHandler. It contains one method responsible for
        answering single requests.
    """

    def handle(self):
        """
        method that handles a single request. Uses the attributes self.request and self.client_address.
        """

        # Read the request content and the address it came from
        msg = str(self.request[0].strip(), "utf-8")
        addr_string = f'{self.client_address[0]}|{self.client_address[1]}'

        # if it is a query it can be answered directly
        if msg == "query":
            result = registry.get_string()  # address and port
            logger.log(level=logging.INFO, msg="Answered to query")
        # otherwise the msg content and the address are passed to the registry
        else:
            result = registry.add_server(msg, addr_string)

        # the result (list of servers, or state of registration) is returned to the client
        self.wfile.write(bytes(result, "utf-8"))


# Creates and UDPServer bound to (localAddress, localPort) that answers using the class defined above
try:
    with socketserver.UDPServer((localAddress, localPort), BrokerRequestHandler) as server:
        server.serve_forever()
except KeyboardInterrupt:
    # Teardown when terminated by user
    server.shutdown()
    registry.stop_timer()
    print("Terminated")
    logger.log(level=logging.INFO, msg="Broker terminated")
