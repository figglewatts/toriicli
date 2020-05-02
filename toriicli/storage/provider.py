from abc import ABC, abstractmethod
from io import IOBase
from typing import Generator, ContextManager, Union


class StorageProvider(ABC):
    """Abstract base class of a storage provider."""
    @abstractmethod
    def store(self, data: Union[IOBase, str, bytes], key: str) -> None:
        """Store a piece of data at a given key in blob storage.

        Args:
            data: The data to store.
            key: The path within the container to store it in.
        """
        raise NotImplementedError()

    @abstractmethod
    def retrieve(self, key: str, filename: str) -> None:
        """Retrieve a piece of data from a given key in blob storage.

        Args:
            key: The key within the container to get the data from.
            filename: The file name to write the file to.
        """
        raise NotImplementedError()

    @abstractmethod
    def ls(self) -> Generator[str, None, None]:
        """List blobs within a container.

        Yields:
            str: The names of blobs within the container.
        """
        raise NotImplementedError()