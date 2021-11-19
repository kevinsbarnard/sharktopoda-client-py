from typing import List
from uuid import UUID

from sharktopoda_client.localization.Localization import Localization
from sharktopoda_client.model.Video import Video


class Message:
    ACTION_ADD = 'add'
    ACTION_REMOVE = 'remove'
    ACTION_CLEAR = 'clear'
    ACTION_SELECT = 'select'
    ACTION_DESELECT = 'deselect'
    
    def __init__(self, action: str, localization: Localization = None, video: Video = None):
        self._action = action
        self._localizations = [localization] if localization is not None else []
    
    @property
    def action(self) -> str:
        return self._action
    
    @property
    def localizations(self) -> List[Localization]:
        return self._localizations
    
    def __str__(self) -> str:
        return 'Message{' + 'action=' + self._action + ', localizations=' + str(self._localizations) + '}'
