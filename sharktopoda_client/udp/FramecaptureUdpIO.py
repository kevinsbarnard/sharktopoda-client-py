from rx.core.typing import Observable

# from sharktopoda_client.model.GenericCommand import GenericCommand
# from sharktopoda_client.udp.CommandService import CommandService


class FrameCaptureUdpIO:
    def __init__(self, commandService: 'CommandService', commandObserver: Observable['GenericCommand']) -> None:
        self.commandObserver = commandObserver
        self.commandService = commandService
        # TODO: implement