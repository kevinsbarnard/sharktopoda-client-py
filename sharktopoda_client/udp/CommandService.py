from typing import Awaitable, Callable

from rx.core.typing import Subject

from sharktopoda_client.ClientController import ClientController
from sharktopoda_client.Log import get_logger
from sharktopoda_client.udp.FramecaptureUdpIO import FrameCaptureUdpIO
from sharktopoda_client.model.GenericCommand import GenericCommand
from sharktopoda_client.model.GenericResponse import GenericResponse

class CommandService:
    
    def __init__(self, clientController: ClientController, commandSubject: Subject, responseSubject: Subject):
        self.clientController = clientController
        self.responseSubject = responseSubject
        self.log = get_logger('CommandService')
        self.framecaptureIO = FrameCaptureUdpIO(self, commandSubject)
        commandSubject.subscribe(self.handleCommand)
    
    def handleCommand(self, cmd: GenericCommand):
        c = cmd.command.lower()
        {
            'open': self.doOpen,
            'close': self.doClose,
            'show': self.doShow,
            'request video information': self.doRequestVideoInfo,
            'request all information': self.doRequestAllVideoInfos,
            'play': self.doPlay,
            'pause': self.doPause,
            'request elapsed time': self.doRequestElapsedTime,
            'request status': self.doRequestStatus,
            'seek elapsed time': self.doSeekElapsedTime,
            'frame capture': self.doFrameCapture,
            'frame advance': self.doFrameAdvance
        }.get(c, lambda _: _)(cmd)
    
    def doOpen(self, cmd: GenericCommand):
        r = GenericResponse.from_cmd(cmd)
        if cmd.url and cmd.uuid:
            status = self.clientController.open(cmd.uuid, cmd.url)
            statusMessage = 'ok' if status else 'failed'
            r.status = statusMessage
        else:
            self.log.warn(f'Bad command: {cmd.to_json()}')
        self.responseSubject.on_next(r)
    
    def doClose(self, cmd: GenericCommand):
        r = GenericResponse.from_cmd(cmd)
        if cmd.uuid:
            self.clientController.close(cmd.uuid)
        self.responseSubject.on_next(r)
    
    def doShow(self, cmd: GenericCommand):
        r = GenericResponse.from_cmd(cmd)
        if cmd.uuid:
            self.clientController.show(cmd.uuid)
        self.responseSubject.on_next(r)
    
    def doRequestVideoInfo(self, cmd: GenericCommand):
        r = GenericResponse.from_cmd(cmd)
        opt = self.clientController.requestVideoInfo()
        
        if opt is not None:
            r.uuid = opt.uuid
            r.url = opt.url
        
        self.responseSubject.on_next(r)
    
    def doRequestAllVideoInfos(self, cmd: GenericCommand):
        r = GenericResponse.from_cmd(cmd)
        videos = self.clientController.requestAllVideoInfos()
        r.videos = videos
        self.responseSubject.on_next(r)
    
    def doPlay(self, cmd: GenericCommand):
        self.doAction(cmd, lambda _: 'ok' if self.clientController.play(cmd.uuid, cmd.rate or 1.0) else 'failed')
    
    def doPause(self, cmd: GenericCommand):
        self.doAction(cmd, lambda _: 'ok' if self.clientController.pause(cmd.uuid) else 'failed')
    
    def doRequestElapsedTime(self, cmd: GenericCommand):
        def fn(r: GenericResponse):
            opt = self.clientController.requestElapsedTime(cmd.uuid)
            if opt:
                r.elapsedTime = opt
                return None
            return 'failed'
        self.doAction(cmd, fn)
    
    def doRequestStatus(self, cmd: GenericCommand):
        def fn(r: GenericResponse):
            opt = self.clientController.requestRate(cmd.uuid)
            msg = 'failed'
            if opt:
                rate = opt
                if -0.001 < rate < 0.001:
                    msg = 'paused'
                elif abs(rate - 1.0) < 0.01:
                    msg = 'playing'
                elif rate > 0:
                    msg = 'shuttling forward'
                else:
                    msg = 'shuttling reverse'
            return msg
        self.doAction(cmd, fn)
    
    def doSeekElapsedTime(self, cmd: GenericCommand):
        def fn(r: GenericResponse):
            ok = self.clientController.seekElapsedTime(cmd.uuid, cmd.elapsedTime)
            if not ok:
                return 'failed'
            r.response = None
            return 'ok' if ok else 'failed'
        self.doAction(cmd, fn)
    
    def doFrameAdvance(self, cmd: GenericCommand):
        def fn(r: GenericResponse):
            ok = self.clientController.frameAdvance(cmd.uuid)
            r.response = None
            return 'ok' if ok else 'failed'
        self.doAction(cmd, fn)
    
    def doAction(self, cmd: GenericCommand, fn: Callable):
        r = GenericResponse.from_cmd(cmd)
        r.status = 'failed'
        r.uuid = r.uuid
        if cmd.uuid is not None:
            try:
                status = fn(r)
                r.status = status
            except Exception as e:
                r.status = 'failed'
                self.log.warn(f'Failed to execute {cmd.to_json()} {e}')
        else:
            r.status = 'failed'
        self.responseSubject.on_next(r)
    
    def doFrameCapture(self, cmd: GenericCommand) -> Awaitable[GenericResponse]:
        pass  # TODO: implement
        