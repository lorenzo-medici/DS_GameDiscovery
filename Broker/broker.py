import logging
import os
import socketserver
from pathlib import Path

from Broker.registry import Registry

# CONSTANTS

localAddress = '0.0.0.0'
localPort = 20000

# LOGGING

logging.basicConfig(filename=f'{os.getpid()}.log',
                    format='%(asctime)s:%(process)d:%(name)s:%(levelname)s:%(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S%z',
                    level=logging.DEBUG)
logger = logging.getLogger(Path(__file__).stem)

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


with socketserver.UDPServer((localAddress, localPort), BrokerRequestHandler) as server:
    server.serve_forever()
