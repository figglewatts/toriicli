from io import IOBase
import os
from os import path
import shutil
from typing import Generator, Union

from . import provider


class LocalStorageProvider(provider.StorageProvider):
    """Storage provider for local file storage.

    Attributes:
        container (str): The folder we're using to store files in.
    """
    def __init__(self, container: str):
        self.container = container

    def store(self, data: Union[IOBase, str, bytes], key: str) -> None:
        self._ensure_container()
        file_path = path.join(self.container, key)
        os.makedirs(path.dirname(file_path), exist_ok=True)
        if issubclass(type(data), IOBase):
            with open(file_path, "wb") as file_handle:
                shutil.copyfileobj(data, file_handle)
        elif type(data) == str:
            with open(file_path, "w") as file_handle:
                file_handle.write(data)
        elif type(data) == bytes:
            with open(file_path, "wb") as file_handle:
                file_handle.write(data)
        else:
            raise TypeError(f"invalid data type '{type(data)}'")

    def retrieve(self, key: str, filename: str) -> None:
        self._ensure_container()
        os.makedirs(path.dirname(filename), exist_ok=True)
        with open(path.join(self.container, key), "rb") as file_handle, \
                open(filename, "wb") as out_file_handle:
            shutil.copyfileobj(file_handle, out_file_handle)

    def ls(self) -> Generator[str, None, None]:
        self._ensure_container()
        for dirpath, _, filenames in os.walk(self.container):
            for filename in filenames:
                full_path = path.join(dirpath, filename)
                yield path.relpath(full_path, self.container)

    def _ensure_container(self) -> None:
        os.makedirs(self.container, exist_ok=True)