from dataclasses import dataclass
from enum import Enum
from typing import List

from dataclasses_json import dataclass_json

from sharktopoda_client.localization.Localization import Localization
from sharktopoda_client.model.Video import Video


class MessageAction(Enum):
    ACTION_ADD = 'add'
    ACTION_REMOVE = 'remove'
    ACTION_CLEAR = 'clear'
    ACTION_SELECT = 'select'
    ACTION_DESELECT = 'deselect'


@dataclass_json
@dataclass
class Message:
    action: MessageAction
    localizations: List[Localization] = []
    video: Video = None
    
    def __str__(self) -> str:
        return 'Message{' + 'action=' + self.action + ', localizations=' + str(self.localizations) + '}'
