
from abc import ABC, abstractmethod
from typing import Iterable, Tuple
from uuid import UUID

from sharktopoda_client.dto import Localization


class LocalizationController(ABC):
    """
    Localization controller base class. Defines the interface for localization controllers.
    """
    
    def __getitem__(self, uuids: Tuple[UUID, UUID]) -> Localization:
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
    def get_localization(self, collection_uuid: UUID, localization_uuid: UUID) -> Localization:
        """
        Get a localization from a collection.

        Args:
            collection_uuid: The UUID of the collection.
            localization_uuid: The UUID of the localization.

        Returns:
            The localization.
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