class ConnectCommand:
    def __init__(self, port: int = None, host: str = None):
        self.command = 'connect'
        self.port = port
        self.host = host
    
    def getPort(self) -> int:
        return self.port
    
    def setPort(self, port: int):
        self.port = port
    
    def getHost(self) -> str:
        return self.host

    def setHost(self, host: str):
        self.host = host