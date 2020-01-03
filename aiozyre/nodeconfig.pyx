# cython: language_level=3

from typing import Mapping, Union, Iterable

cdef class NodeConfig:
    def __cinit__(
        self,
        name: str, * ,
        headers: Mapping = None,
        groups: Union[None, Iterable[str]] = None,
        endpoint: str = None,
        gossip_endpoint: str = None,
        interface: str = None,
        evasive_timeout_ms: int = None,
        expired_timeout_ms: int = None,
        verbose: bool = False
    ):
        self.name = name
        self.headers = headers or {}
        self.groups = groups or set()
        self.endpoint = endpoint
        self.gossip_endpoint = gossip_endpoint
        self.interface = interface
        self.evasive_timeout_ms = evasive_timeout_ms
        self.expired_timeout_ms = expired_timeout_ms
        self.verbose = int(verbose)

    def __init__(
        self,
        name: str, * ,
        headers: Mapping = None,
        groups: Union[None, Iterable[str]] = None,
        endpoint: str = None,
        gossip_endpoint: str = None,
        interface: str = None,
        evasive_timeout_ms: int = None,
        expired_timeout_ms: int = None,
        verbose: bool = False
    ):
        pass
