import threading
from collections import defaultdict
from typing import ForwardRef

from .types import PY_MODEL, SA_MODEL

RegistryType = defaultdict[SA_MODEL, dict[str, PY_MODEL | ForwardRef]]


class Sa2PydanticReg(RegistryType):
    def __init__(self):
        super().__init__(dict)
        self.lock = threading.Lock()

    def __setitem__(self, key, value):
        with self.lock:
            return super().__setitem__(key, value)


SA2PYDANTIC_REGISTRY = Sa2PydanticReg()
