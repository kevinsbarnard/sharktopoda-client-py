from typing import List, Set, Union
from uuid import UUID

from sharktopoda_client.IOBus import IOBus
from sharktopoda_client.Log import get_logger
from sharktopoda_client.localization.Localization import Localization
from sharktopoda_client.localization.Message import Message, MessageAction
from sharktopoda_client.localization.Preconditions import Preconditions


class LocalizationController(IOBus):
    
    def __init__(self):
        super().__init__()
        
        self.log = get_logger('LocalizationController')
        
        self._localizations: Set[Localization] = set()
        
        self._incoming.subscribe(self._on_incoming, self._on_error)
        
    @property
    def readOnlyLocalizations(self) -> List[Localization]:
        return sorted(self._localizations, key=lambda l: l.elapsedTime)
    
    def _on_incoming(self, message: Message):
        """
        Handle incoming messages.
        """
        if message.action == MessageAction.ACTION_ADD:
            self._add_or_replace_localizations_internal(message.localizations)
        elif message.action == MessageAction.ACTION_REMOVE:
            self._remove_localizations_internal(message.localizations)
        elif message.action == MessageAction.ACTION_CLEAR:
            self._localizations.clear()
        else:
            self.log.error('Unknown message action: ' + message.action)
    
    def _on_error(self, e):
        self.log.warn('An error occurred on the incoming localization bus', e)
    
    def _add_or_replace_localizations_internal(self, localizations: List[Localization]):
        localizations = set(localizations)
        self._localizations -= localizations
        self._localizations |= localizations
        # for localization in localizations:
        #     self._add_or_replace_localization_internal(localization)
        
    def _add_or_replace_localization_internal(self, a: Localization):
        if a in self._localizations:
            self._localizations.remove(a)
            self.log.debug('Replacing localization (uuid = ' + str(a.localizationUuid) + ')')
        else:
            self.log.debug('Adding localization (uuid = ' + str(a.localizationUuid) + ')')
        self._localizations.add(a)
    
    def addLocalization(self, localization: Localization):
        self.addLocalizations([localization])
    
    def addLocalizations(self, localizations: List[Localization]):
        map(self._validateLocalizationForAdd, localizations)
        if len(localizations) > 0:
            msg = Message(MessageAction.ACTION_ADD, localizations)
            self._incoming.on_next(msg)
            self._outgoing.on_next(msg)
    
    def _validateLocalizationForAdd(self, localization: Localization):
        Preconditions.require(localization.localizationUuid is not None, 'Localization requires a localizationUuid. Null was found.')
        Preconditions.require(localization.concept is not None, 'A Localization requires a concept. Null was found')
        Preconditions.require(localization.elapsedTime is not None, 'A localization requires an elapsedtime. Null was found')
        Preconditions.require(localization.x is not None, 'A localization requires an x value. Null was found')
        Preconditions.require(localization.x >= 0, 'A localization can not have a negative x coordinate. ' + str(localization.x) + ' was found')
        Preconditions.require(localization.y is not None, 'A localization requires a y value. Null was found')
        Preconditions.require(localization.y >= 0, 'A localization can not have a negative y coordinate. ' + str(localization.y) + ' was found')
        Preconditions.require(localization.width is not None, 'A localization requires a width value. Null was found')
        Preconditions.require(localization.width > 0, 'A localization can not have a width less than 1 pixel.' + str(localization.width) + ' was found.')
        Preconditions.require(localization.height is not None, 'A localization requires a height value. Null was found')
        Preconditions.require(localization.height > 0, 'A localization can not have a height less than 1 pixel. ' + str(localization.height) + ' was found.')

    def removeLocalization(self, localization_or_uuid: Union[Localization, str, UUID]):
        if isinstance(localization_or_uuid, Localization):
            localization = localization_or_uuid
            self.removeLocalizations([localization])
        else:
            localization_uuid = localization_or_uuid
            Preconditions.require(localization_uuid is not None, 'removeLocalization(null) is not allowed')
            self.removeLocalizations([Localization(localizationUuid=UUID(localization_uuid))])
    
    def removeLocalizations(self, localizations: List[Localization]):
        map(self._validateLocalizationForRemove, localizations)
        msg = Message(MessageAction.ACTION_REMOVE, localizations)
        self._incoming.on_next(msg)
        self._outgoing.on_next(msg)

    def _validateLocalizationForRemove(self, localization: Localization):
        Preconditions.require(localization.localizationUuid is not None, 'Can not remove a localization without a localizationUuid')

    def _remove_localizations_internal(self, localizations: List[Localization]):
        for localization in localizations:
            try:
                self._remove_localization_internal(localization)
            except Exception as e:
                self.log.warn('Failed to remove a localization that was missing required values.', e)
    
    def _remove_localization_internal(self, a: Localization):
        exists = False
        msg = None
        for i in range(len(self._localizations)):
            b = self._localizations[i]
            if b.localizationUuid == a.localizationUuid:
                self._localizations.pop(i)
                exists = True
                break
        if not exists:
            self.log.debug('A localization with UUID of ' + a.localizationUuid + ' was not found. Unable to remove.')
        if msg is not None:
            self.log.debug('Removing localization (uuid = ' + a.localizationUuid + ')')
    
    def clear(self):
        msg = Message(MessageAction.ACTION_CLEAR)
        self._incoming.on_next(msg)
        self._outgoing.on_next(msg)
    
    def getLocalizations(self) -> List[Localization]:
        return self.readOnlyLocalizations
