
from abc import ABC, abstractmethod
from typing import Iterable, Optional, Tuple
from uuid import UUID

from sharktopoda_client.dto import Localization


class LocalizationController(ABC):
    """
    Localization controller base class. Defines the interface for localization controllers.
    """
    
    def __getitem__(self, uuids: Tuple[UUID, UUID]) -> Optional[Localization]:
        return self.get_localization(uuids[0], uuids[1])
    
    @abstractmethod
    def clear_collection(self, uuid: UUID):
        """
        Clear a collection.

        Args:
            uuid: The UUID of the collection.
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_localization(self, collection_uuid: UUID, localization_uuid: UUID) -> Optional[Localization]:
        """
        Get a localization from a collection.

        Args:
            collection_uuid: The UUID of the collection.
            localization_uuid: The UUID of the localization.

        Returns:
            The localization, or None if it does not exist.
        """
        raise NotImplementedError
    
    @abstractmethod
    def add_update_localizations(self, collection_uuid: UUID, localizations: Iterable[Localization]):
        """
        Add or update localizations in a collection.

        Args:
            collection_uuid: The UUID of the collection.
            localizations: The localizations to add or update.
        """
        raise NotImplementedError
    
    @abstractmethod
    def remove_localizations(self, collection_uuid: UUID, localization_uuids: Iterable[UUID]):
        """
        Remove localizations from a collection by UUID.

        Args:
            collection_uuid: The UUID of the collection.
            localization_uuids: The UUIDs of the localizations to remove.
        """
        raise NotImplementedError

    @abstractmethod
    def select_localizations(self, collection_uuid: UUID, localization_uuids: Iterable[UUID]):
        """
        Select localizations in a collection by UUID.

        Args:
            collection_uuid: The UUID of the collection.
            localization_uuids: The UUIDs of the localizations to select.
        """
        raise NotImplementedError


class NoOpLocalizationController(LocalizationController):
    """
    No-op localization controller. Does nothing. Useful for applications that don't care about localizations and just want to control the video.
    """
    
    def clear_collection(self, uuid: UUID):
        pass
    
    def get_localization(self, collection_uuid: UUID, localization_uuid: UUID) -> Optional[Localization]:
        return None
    
    def add_update_localizations(self, collection_uuid: UUID, localizations: Iterable[Localization]):
        pass
    
    def remove_localizations(self, collection_uuid: UUID, localization_uuids: Iterable[UUID]):
        pass
    
    def select_localizations(self, collection_uuid: UUID, localization_uuids: Iterable[UUID]):
        pass
