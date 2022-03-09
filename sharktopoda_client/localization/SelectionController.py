from typing import List

from sharktopoda_client.localization.Localization import Localization
from sharktopoda_client.localization.Message import Message, MessageAction
from sharktopoda_client.localization.LocalizationController import LocalizationController


class SelectionController:
    
    def __init__(self, controller: LocalizationController):
        self._controller = controller
        
        self._selected_localizations: List[Localization] = []
        
        self._controller.getIncoming().subscribe(self._on_incoming)
    
    def _on_incoming(self, message: Message):
        if message.action == MessageAction.ACTION_SELECT:
            self.select(message.localizations, False)
        elif message.action == MessageAction.ACTION_DESELECT:
            self.deselect(message.localizations, False)
    
    def select(self, localizations: List[Localization], sendNotify: bool):
        intersection = [l for l in self._controller.getLocalizations() if l in localizations]
        
        self._selected_localizations.clear()
        self._selected_localizations.extend(intersection)
        
        if sendNotify:
            self._controller.getOutgoing().on_next(Message(MessageAction.ACTION_SELECT, intersection))

    def deselect(self, localizations: List[Localization], sendNotify: bool):
        intersection = [l for l in self._selected_localizations if l in localizations]
        
        for l in intersection:
            self._selected_localizations.remove(l)
        
        if sendNotify and len(intersection) > 0:
            self._controller.getOutgoing().on_next(Message(MessageAction.ACTION_DESELECT, intersection))

    def clearSelections(self):
        self.select([], True)
    
    @property
    def controller(self):
        return self._controller
    
    def getSelectedLocalizations(self):
        return self._selected_localizations
