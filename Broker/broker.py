import logging
import os
import socketserver
import sys

from registry import Registry

# CONSTANTS

localAddress = '0.0.0.0'
localPort = 20000

# LOGGING

file_handler = logging.FileHandler(f'{os.getpid()}.log')
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(format='%(asctime)s:%(process)d:%(name)s:%(levelname)s:%(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S%z',
                    level=logging.DEBUG,
                    handlers=handlers)
logger = logging.getLogger('Broker')


# INIZIALIZING VARIABLES

registry = Registry(logger)


class BrokerRequestHandler(socketserver.DatagramRequestHandler):

    def handle(self):
        msg = str(self.request[0].strip(), "utf-8")
        addr_string = f'{self.client_address[0]}|{self.client_address[1]}'

        if msg == "query":
            result = registry.get_string()  # address and port
            logger.log(level=logging.INFO, msg="Answered to query")
        else:
            result = registry.add_server(msg, addr_string)

        self.wfile.write(bytes(result, "utf-8"))


try:
    with socketserver.UDPServer((localAddress, localPort), BrokerRequestHandler) as server:
        server.serve_forever()
except KeyboardInterrupt:
    server.shutdown()
    registry.stop_timer()
    print("Terminated")
    logger.log(level=logging.INFO, msg="Broker terminated")
