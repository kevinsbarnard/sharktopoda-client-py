from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

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
    localizations: List[Localization] = field(default_factory=list)
    
    def __str__(self) -> str:
        return 'Message{' + 'action=' + self.action.value + ', localizations=' + str(self.localizations) + '}'
