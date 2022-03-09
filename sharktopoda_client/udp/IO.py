from sharktopoda_client.ClientController import ClientController
from sharktopoda_client.udp.CommandService import CommandService
from sharktopoda_client.udp.UdpIO import UdpIO


class IO:
    
    def __init__(self, clientController: ClientController, port: int):
        self.clientController = clientController
        self.io = UdpIO(port)
        self.commandService = CommandService(self.clientController, self.io.commandSubject, self.io.responseSubject)
    
    def close(self):
        self.io.close()
