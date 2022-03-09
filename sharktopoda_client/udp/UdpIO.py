import logging
from socket import AF_INET, SOCK_DGRAM, socket
from threading import Thread

from rx.subject import Subject
from rx.scheduler import EventLoopScheduler
from sharktopoda_client.Log import get_logger
from sharktopoda_client.model.GenericCommand import GenericCommand

from sharktopoda_client.model.GenericResponse import GenericResponse


class UdpIO:
    
    def __init__(self, port: int):
        self.port = port
        self.log = get_logger('UdpIO')
        
        self.commandSubject = Subject()
        
        self.scheduler = EventLoopScheduler()
        
        self.server: socket = None
        self.responseSubject = Subject()
        self.responseSubject.subscribe(self.doResponse, scheduler=self.scheduler)
        
        self.ok = True
        
        def receive():
            while self.ok:
                try:
                    packet, (addr, port) = self.getServer().recvfrom(4096)
                    msg = packet.decode('utf-8')
                    r: GenericCommand = GenericCommand.from_json(msg)
                    r.packetAddress = addr
                    r.packetPort = port
                    self.commandSubject.on_next(r)
                except Exception as e:
                    self.log.info(f'Error while reading UDP datagram {e}')
                    break
            if self.server:
                self.server.close()
                self.server = None
                self.log.info('Shutting down UDP server')
            
        self.receiverThread = Thread(target=receive, daemon=True)
        self.receiverThread.start()
    
    def close(self):
        if self.ok:
            self.ok = False
            self.commandSubject.on_completed()
            self.responseSubject.on_completed()
    
    def doResponse(self, response: GenericResponse):
        if response.isResponseExpected():
            try:
                s = self.getServer()
                b = response.to_json().encode('utf-8')
                self.log.debug(f'Sending >>> {b.decode("utf-8")}')
                self.log.debug(response.packetAddress)
                self.log.debug(response.packetPort)
                s.sendto(b, (response.packetAddress, response.packetPort))
            except Exception as e:
                self.log.error(f'UDP response failed {e}')
    
    def getServer(self) -> socket:
        if not self.server:
            self.server = socket(AF_INET, SOCK_DGRAM)
            self.server.bind(('', self.port))
        return self.server