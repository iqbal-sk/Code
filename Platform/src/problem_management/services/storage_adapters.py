import os

from abc import ABC, abstractmethod
from Platform.src.config.config import config
class StorageAdapter(ABC):
    @abstractmethod
    def save(self, file_bytes: bytes, dest: str) -> str: ...

    @abstractmethod
    def read(self, location: str) -> bytes: ...

    @abstractmethod
    def delete(self, location: str) -> None: ...


class LocalAdapter(StorageAdapter):
    def __init__(self, base_dir=config.LOCAL_TEST_ASSETS):
        self.base = os.path.expanduser(base_dir)
        os.makedirs(self.base, exist_ok=True)

    def save(self, file_bytes, dest):
        path = os.path.join(self.base, dest)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(file_bytes)
        return path

    def read(self, location):
        with open(location, 'rb') as f:
            return f.read()

    def delete(self, location):
        os.remove(location)