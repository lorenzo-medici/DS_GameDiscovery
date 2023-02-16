import socketserver

from Broker.registry import Registry

# TODO: Add logging

# CONSTANTS

localAddress = '0.0.0.0'
localPort = 20000

# INIZIALIZING VARIABLES

registry = Registry()


class BrokerRequestHandler(socketserver.DatagramRequestHandler):

    def handle(self):
        msg = str(self.request[0].strip(), "utf-8")
        addr_string = f'{self.client_address[0]}|{self.client_address[1]}'

        if msg == "query":
            result = registry.get_string()  # address and port
        else:
            result = registry.add_server(msg, addr_string)

        self.wfile.write(bytes(result, "utf-8"))


with socketserver.UDPServer((localAddress, localPort), BrokerRequestHandler) as server:
    server.serve_forever()
