
import asyncio
from concurrent.futures import Executor
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Union, Mapping, Iterable, Set, Callable

from .zyrec cimport zyre_join, zlist_destroy, zyre_set_interval, zpoller_expired, \
    zyre_set_expired_timeout, zyre_recv, zyre_set_verbose, zyre_set_endpoint, zlist_t, zyre_peer_address, \
    zpoller_destroy, zyre_start, zyre_peer_header_value, zyre_gossip_bind, zpoller_wait, zyre_peer_groups, \
    zyre_own_groups, zyre_whispers, zmsg_t, zyre_shout, zyre_socket, zyre_leave, zyre_name, zyre_peers_by_group, \
    zyre_t, zyre_gossip_connect, zyre_set_header, zyre_peers, zpoller_new, zsock_t, zyre_uuid, zyre_stop, \
    zyre_destroy, zyre_whisper, zyre_new, zyre_set_evasive_timeout, zyre_shouts, zpoller_t, zpoller_add
from .util cimport zmsg_to_msg, msg_to_zmsg, zlist_to_str_set
from .msg import Msg
from .exceptions import NodeStartError, Timeout, Stopped, NodeRecvError


cdef class Node:
    __slots__ = (
        '_c_zyre', '_c_zpoller', '_started', '_name', '_headers', '_groups', '_endpoint', '_gossip_endpoint', '_loop',
        '_executor')

    cdef zyre_t*_c_zyre
    cdef zpoller_t*_c_zpoller
    cdef object _started
    cdef str _name
    cdef object _headers
    cdef object _groups
    cdef str _endpoint
    cdef str _gossip_endpoint
    cdef object _loop
    cdef object _executor

    def __cinit__(
        self,
        name: str,
        *,
        headers: Mapping = None,
        groups: Union[None, Iterable[str]] = None,
        endpoint: str = None,
        gossip_endpoint: str = None,
        loop: Union[None, asyncio.AbstractEventLoop] = None,
        executor: Union[None, Executor] = None
    ):
        """
        Constructor, creates a new Zyre node. Note that until you start the
        node it is silent and invisible to other nodes on the network.
        The node name is provided to other nodes during discovery.
        """
        b_name = name.encode('utf8')
        self._c_zyre = zyre_new(b_name)
        if self._c_zyre is NULL:
            raise MemoryError('Could not create zyre')
        self._name = name
        self._headers = headers
        self._groups = groups
        self._endpoint = endpoint
        self._gossip_endpoint = gossip_endpoint
        self._started = asyncio.Event()
        self._c_zpoller = NULL
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        if executor is None:
            executor = ThreadPoolExecutor(max_workers=1)
        self._executor = executor

    def __init__(
        self,
        name: str,
        *,
        headers: Mapping = None,
        groups: Union[None, Iterable[str]] = None,
        endpoint: str = None,
        gossip_endpoint: str = None,
        loop: Union[None, asyncio.AbstractEventLoop] = None,
        executor: Union[None, Executor] = None
    ):
        pass

    def __dealloc__(self):
        if self._c_zyre is not NULL:
            zpoller_destroy(&self._c_zpoller)
            zyre_destroy(&self._c_zyre)
            self._c_zyre = NULL

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.uuid)

    @property
    def running(self) -> bool:
        return self._started.is_set()

    @property
    def name(self) -> str:
        return zyre_name(self._c_zyre).decode('utf8')

    @property
    def uuid(self) -> str:
        return zyre_uuid(self._c_zyre)

    async def spawn(self, func: Callable, *args):
        """
        Run the given func in a separate thread and return a future for its result.

        This is useful for calling code in a C extension which releases the GIL
        while it performs socket or other blocking actions.
        """
        return self._loop.run_in_executor(self._executor, func, *args)

    async def start(self):
        """
        Start node, after setting header values. When you start a node it
        begins discovery and connection. Returns 0 if OK, -1 if it wasn't
        possible to start the node.
        """
        if self._endpoint and self._gossip_endpoint:
            e = self._endpoint.encode('utf8')
            ge = self._gossip_endpoint.encode('utf8')
            zyre_set_endpoint(self._c_zyre, "%s", <char*> e)
            zyre_gossip_connect(self._c_zyre, "%s", <char*> ge)
            zyre_gossip_bind(self._c_zyre, "%s", <char*> ge)
        if self._headers:
            for name, value in self._headers.items():
                self._set_header(name, value)
        if zyre_start(self._c_zyre) == 0:
            self._started.set()
        else:
            raise NodeStartError
        # The nodes may need a little time to boot
        while not self.name and not zyre_socket(self._c_zyre):
            await asyncio.sleep(0.01)
        if self._groups:
            for group in self._groups:
                self._join(group)
        self._c_zpoller = zpoller_new(NULL)
        zpoller_add(self._c_zpoller, <void *> zyre_socket(self._c_zyre))

    async def stop(self):
        """
        Stop node; this signals to other peers that this node will go away.
        This is polite; however you can also just destroy the node without
        stopping it.
        """
        def stop():
            return self._stop()
        return await self.spawn(stop)

    cdef void _stop(self):
        with nogil:
            zyre_stop(self._c_zyre)
        self._started.clear()

    async def join(self, group: Union[str, bytes]):
        """
        Join a named group; after joining a group you can send messages to
        the group and all Zyre nodes in that group will receive them.
        """
        return await self.spawn(self._join, group)

    def _join(self, group: Union[str, bytes]):
        return self._c_join(group)

    cdef _c_join(self, group: Union[str, bytes]):
        if isinstance(group, str):
            group = group.encode('utf8')
        cdef char *c_group = <char*> group
        with nogil:
            zyre_join(self._c_zyre, c_group)

    async def leave(self, group: Union[str, bytes]):
        """
        Leave a group
        """
        return await self.spawn(self._leave, group)

    def _leave(self, group: Union[str, bytes]):
        return self._c_leave(group)

    cdef void _c_leave(self, group: Union[str, bytes]):
        if isinstance(group, str):
            group = group.encode('utf8')
        cdef char *c_group = <char*> group
        with nogil:
            zyre_leave(self._c_zyre, c_group)

    async def recv(self, timeout_ms: int = -1) -> Msg:
        """
        Receive next message from network; the message may be a control
        message (ENTER, EXIT, JOIN, LEAVE) or data (WHISPER, SHOUT).
        Returns Zmsg object, or NULL if interrupted
        """
        return await self.spawn(self._recv, timeout_ms)

    def _recv(self, timeout_ms: int = -1) -> Msg:
        return self._c_recv(timeout_ms)

    cdef object _c_recv(self, timeout_ms: int = -1):
        if not self.running:
            raise Stopped
        cdef int c_timeout_ms
        cdef zsock_t* sock
        if timeout_ms >= 0:
            c_timeout_ms = <int> timeout_ms
            with nogil:
                sock = <zsock_t*> zpoller_wait(self._c_zpoller, c_timeout_ms)
            if sock is NULL:
                if zpoller_expired(self._c_zpoller):
                    raise Timeout
                else:
                    raise Stopped
        if not self.running:
            raise Stopped
        cdef zmsg_t *zmsg
        with nogil:
            zmsg = zyre_recv(self._c_zyre)

        if zmsg is NULL:
            raise NodeRecvError

        msg = zmsg_to_msg(zmsg)
        return msg

    async def whispers(self, peer: Union[str, bytes], msg: Union[str, bytes]):
        """
        Send message to single peer, specified as a UUID string
        """
        return await self.spawn(self._whispers, peer, msg)

    def _whispers(self, peer: Union[str, bytes], msg: Union[str, bytes]):
        return self._c_whispers(peer, msg)

    cdef void _c_whispers(self, peer: Union[str, bytes], msg: Union[str, bytes]):
        if isinstance(peer, str):
            peer = peer.encode('utf8')
        if isinstance(msg, str):
            msg = msg.encode('utf8')
        cdef char *c_peer = <char *> peer
        cdef char *c_msg = <char *> msg
        with nogil:
            zyre_whispers(self._c_zyre, c_peer, "%s", c_msg)

    async def whisper(self, peer: Union[str, bytes], msg: Msg):
        """
        Send message to single peer, specified as a UUID string
        """
        return await self.spawn(self._whisper, peer, msg)

    def _whisper(self, peer: Union[str, bytes], msg: Union[str, bytes]):
        return self._c_whisper(peer, msg)

    cdef void _c_whisper(self, peer: Union[str, bytes], msg: Msg):
        cdef char *c_peer = <char *> peer
        cdef zmsg_t * c_msg = msg_to_zmsg(msg)
        with nogil:
            zyre_whisper(self._c_zyre, c_peer, &c_msg)

    async def shouts(self, group: Union[str, bytes], msg: Union[str, bytes]):
        """
        Send message to a named group
        """
        await self.spawn(self._shouts, group, msg)

    def _shouts(self, group: Union[str, bytes], msg: Union[str, bytes]):
        self._c_shouts(group, msg)

    cdef void _c_shouts(self, group: Union[str, bytes], msg: Union[str, bytes]):
        if isinstance(group, str):
            group = group.encode('utf8')
        if isinstance(msg, str):
            msg = msg.encode('utf8')
        cdef char *c_group = <char *> group
        cdef char *c_msg = <char *> msg
        with nogil:
            zyre_shouts(self._c_zyre, c_group, "%s", c_msg)

    async def shout(self, group: Union[str, bytes], msg: Msg):
        """
        Send message to a named group
        """
        await self.spawn(self._shout, group, msg)

    def _shout(self, group: Union[str, bytes], msg: Msg):
        self._c_shout(group, msg)

    cdef void _c_shout(self, group: Union[str, bytes], msg: Msg):
        cdef char *c_group = <char *> group
        cdef zmsg_t * c_msg = msg_to_zmsg(msg)
        with nogil:
            zyre_shout(self._c_zyre, c_group, &c_msg)

    async def peers(self) -> Set[str]:
        """
        Return set of current peer ids.
        """
        return await self.spawn(self._peers)

    def _peers(self) -> Set[str]:
        return self._c_peers()

    cdef set _c_peers(self):
        cdef zlist_t *zlist
        with nogil:
            zlist = zyre_peers(self._c_zyre)
        py_set = zlist_to_str_set(zlist)
        zlist_destroy(&zlist)
        return py_set

    async def peers_by_group(self, name: Union[str, bytes]) -> Set[str]:
        """
        Return set of current peers of this group.
        """
        return await self.spawn(self._peers_by_group, name)

    def _peers_by_group(self, name: Union[str, bytes]) -> Set[str]:
        return self._c_peers_by_group(name)

    cdef set _c_peers_by_group(self, name: Union[str, bytes]):
        cdef zlist_t *zlist
        if isinstance(name, str):
            name = name.encode('utf8')
        cdef char *c_name = <char*> name
        with nogil:
            zlist = zyre_peers_by_group(self._c_zyre, c_name)
        py_set = zlist_to_str_set(zlist)
        zlist_destroy(&zlist)
        return py_set

    async def own_groups(self) -> Set[str]:
        """
        Return set of currently joined groups.
        """
        return await self.spawn(self._own_groups)

    def _own_groups(self) -> Set[str]:
        return self._c_own_groups()

    cdef set _c_own_groups(self):
        cdef zlist_t *zlist
        with nogil:
            zlist = zyre_own_groups(self._c_zyre)
        py_set = zlist_to_str_set(zlist)
        zlist_destroy(&zlist)
        return py_set

    async def peer_groups(self) -> Set[str]:
        """
        Return set of groups known through connected peers.
        """
        return await self.spawn(self._peer_groups)

    def _peer_groups(self) -> Set[str]:
        return self._c_peer_groups()

    cdef set _c_peer_groups(self):
        cdef zlist_t *zlist
        with nogil:
            zlist = zyre_peer_groups(self._c_zyre)
        py_set = zlist_to_str_set(zlist)
        zlist_destroy(&zlist)
        return py_set

    async def peer_address(self, peer: Union[str, bytes]) -> str:
        """
        Return the endpoint of a connected peer.
        Returns empty string if peer does not exist.
        """
        return await self.spawn(self._peer_address, peer)

    def _peer_address(self, peer: Union[str, bytes]) -> str:
        return self._c_peer_address(peer)

    cdef str _c_peer_address(self, peer: Union[str, bytes]):
        if isinstance(peer, str):
            peer = peer.encode('utf8')
        cdef char *c_peer = <char *> peer
        cdef char *ret
        with nogil:
            ret = zyre_peer_address(self._c_zyre, c_peer)
        b_ret = b'%s' % (<bytes> ret)
        return b_ret.decode('utf8')

    async def peer_header_value(self, peer: Union[str, bytes], name: Union[str, bytes]) -> str:
        """
        Return the value of a header of a connected peer.
        Returns null if peer or key doesn't exits.
        """
        return await self.spawn(self._peer_header_value, peer, name)

    def _peer_header_value(self, peer: Union[str, bytes], name: Union[str, bytes]) -> str:
        return self._c_peer_header_value(peer, name)

    cdef str _c_peer_header_value(self, peer: Union[str, bytes], name: Union[str, bytes]):
        if isinstance(peer, str):
            peer = peer.encode('utf8')
        if isinstance(name, str):
            name = name.encode('utf8')
        cdef char *c_peer = <char *> peer
        cdef char *c_name = <char *> name
        cdef char *ret
        with nogil:
            ret = zyre_peer_header_value(self._c_zyre, c_peer, c_name)
        b_ret = b'%s' % (<bytes> ret)
        return b_ret.decode('utf8')

    async def set_header(self, name: Union[str, bytes], value: Union[str, bytes]):
        """
        Set node header; these are provided to other nodes during discovery
        and come in each ENTER message.
        """
        await self.spawn(self._set_header, name, value)

    def _set_header(self, name: Union[str, bytes], value: Union[str, bytes]):
        self._c_set_header(name, value)

    cdef void _c_set_header(self, name: Union[str, bytes], value: Union[str, bytes]):
        if isinstance(name, str):
            name = name.encode('utf8')
        if isinstance(value, str):
            value = value.encode('utf8')
        cdef char *c_name = <char*> name
        cdef char *c_value = <char*> value
        with nogil:
            zyre_set_header(self._c_zyre, c_name, "%s", c_value)

    def set_evasive_timeout(self, ms: int):
        zyre_set_evasive_timeout(self._c_zyre, ms)

    def set_expired_timeout(self, ms: int):
        zyre_set_expired_timeout(self._c_zyre, ms)

    def set_interval(self, ms: int):
        zyre_set_interval(self._c_zyre, ms)

    def set_verbose(self):
        zyre_set_verbose(self._c_zyre)
