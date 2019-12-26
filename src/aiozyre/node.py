import asyncio
from typing import Union, Iterable, Set, Mapping

from .msg import Msg
from .threader import Threader
from .exceptions import NodeStartError, Timeout, NodeRecvError, Stopped

from . import xzyre


class Node(Threader):
    """
    An open-source framework for proximity-based P2P apps
    """
    __slots__ = (
        '_zyre', '_started', '_poller', '_name', '_headers', '_groups', '_endpoint', '_gossip_endpoint'
    )

    def __init__(
        self,
        name,
        *,
        headers: Mapping = None,
        groups: Union[None, Iterable[str]] = None,
        loop: Union[None, asyncio.AbstractEventLoop] = None,
        endpoint: str = None,
        gossip_endpoint: str = None
    ):
        """
        Constructor, creates a new Zyre node. Note that until you start the
        node it is silent and invisible to other nodes on the network.
        The node name is provided to other nodes during discovery.
        """
        self._name = name
        self._headers = headers
        self._groups = groups
        self._endpoint = endpoint
        self._gossip_endpoint = gossip_endpoint
        self._started = asyncio.Event()
        self._poller = None
        self._zyre = None
        super().__init__(loop)

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.uuid)

    @property
    def running(self) -> bool:
        return self._started.is_set()

    @property
    def name(self) -> str:
        return xzyre.zyre_name(self._zyre)

    @property
    def uuid(self) -> str:
        return xzyre.zyre_uuid(self._zyre)

    @property
    def socket(self):
        return xzyre.zyre_socket(self._zyre)

    async def start(self):
        """
        Start node, after setting header values. When you start a node it
        begins discovery and connection. Returns 0 if OK, -1 if it wasn't
        possible to start the node.
        """
        self._zyre = xzyre.zyre_new(self._name)
        if self._endpoint and self._gossip_endpoint:
            xzyre.zyre_set_endpoint(self._zyre, self._endpoint)
            xzyre.zyre_gossip_connect(self._zyre, self._gossip_endpoint)
            xzyre.zyre_gossip_bind(self._zyre, self._gossip_endpoint)
        if self._headers:
            for name, value in self._headers.items():
                self._set_header(name, value)
        self._start()
        self._poller = xzyre.zpoller_new()
        xzyre.zpoller_add(self._poller, self.socket)
        if self._groups:
            for group in self._groups:
                self._join(group)
        # The nodes need a little time to boot
        while not self.name:
            await asyncio.sleep(0.1)
        return self

    def _start(self):
        if xzyre.zyre_start(self._zyre) == 0:
            self._started.set()
        else:
            raise NodeStartError

    async def destroy(self):
        """
        Stop node; this signals to other peers that this node will go away.
        This is polite; however you can also just destroy the node without
        stopping it.
        """
        await self.spawn(self._destroy)

    def _destroy(self):
        xzyre.zyre_stop(self._zyre)
        del self._zyre
        self._zyre = None
        self._started.clear()

    async def join(self, group: str):
        """
        Join a named group; after joining a group you can send messages to
        the group and all Zyre nodes in that group will receive them.
        """
        return await self.spawn(self._join, args=(group, ))

    def _join(self, group: str):
        xzyre.zyre_join(self._zyre, group)

    async def leave(self, group: str):
        """
        Leave a group
        """
        await self.spawn(self._leave, args=(group, ))

    def _leave(self, group: str):
        xzyre.zyre_leave(self._zyre, group)

    async def recv(self, timeout_ms: int = -1) -> Msg:
        """
        Receive next message from network; the message may be a control
        message (ENTER, EXIT, JOIN, LEAVE) or data (WHISPER, SHOUT).
        Returns Zmsg object, or NULL if interrupted
        """
        return await self.spawn(self._recv, args=(timeout_ms, ))

    def _recv(self, timeout_ms: int = -1) -> Msg:
        if timeout_ms >= 0:
            sock = xzyre.zpoller_wait(self._poller, timeout_ms)
            if sock is None:
                if xzyre.zpoller_expired(self._poller):
                    raise Timeout
                else:
                    raise Stopped
        if not self._zyre or not self.running:
            raise Stopped
        zmsg = xzyre.zyre_recv(self._zyre)
        if zmsg is None:
            raise NodeRecvError
        return Msg.from_zmsg(zmsg)

    async def whisper(self, peer: str, msg: Union[str, Msg]):
        """
        Send message to single peer, specified as a UUID string
        Destroys message after sending
        """
        if isinstance(msg, str):
            return await self.spawn(self._whispers, args=(peer, msg))
        elif isinstance(msg, Msg):
            msg = msg.to_zmsg()
        await self.spawn(self._whisper, args=(peer, msg))

    def _whispers(self, peer: str, msg: str):
        xzyre.zyre_whispers(self._zyre, peer, msg)

    def _whisper(self, peer: str, msg: xzyre.zmsg_t):
        xzyre.zyre_whisper(self._zyre, peer, msg)

    async def shout(self, group: str, msg: str):
        """
        Send message to a named group
        Destroys message after sending
        """
        if isinstance(msg, str):
            return await self.spawn(self._shouts, args=(group, msg))
        elif isinstance(msg, Msg):
            msg = msg.to_zmsg()
        await self.spawn(self._shout, args=(group, msg))

    def _shouts(self, peer: str, msg: str):
        xzyre.zyre_shouts(self._zyre, peer, msg)

    def _shout(self, peer: str, msg: xzyre.zmsg_t):
        xzyre.zyre_shout(self._zyre, peer, msg)

    async def peers(self) -> Set[str]:
        """
        Return zlist of current peer ids.
        """
        return await self.spawn(self._peers)

    def _peers(self) -> Set[str]:
        return xzyre.zyre_peers(self._zyre)

    async def peers_by_group(self, name: str) -> Set[str]:
        """
        Return set of current peers of this group.
        """
        return await self.spawn(self._peers_by_group, args=(name, ))

    def _peers_by_group(self, name: str) -> Set[str]:
        return xzyre.zyre_peers_by_group(self._zyre, name)

    async def own_groups(self) -> Set[str]:
        """
        Return set of currently joined groups.
        """
        return await self.spawn(self._own_groups)

    def _own_groups(self) -> Set[str]:
        return xzyre.zyre_own_groups(self._zyre)

    async def peer_groups(self) -> Set[str]:
        """
        Return set of groups known through connected peers.
        """
        return await self.spawn(self._peer_groups)

    def _peer_groups(self) -> Set[str]:
        return xzyre.zyre_peer_groups(self._zyre)

    async def peer_address(self, peer: str) -> str:
        """
        Return the endpoint of a connected peer.
        Returns empty string if peer does not exist.
        """
        return await self.spawn(self._peer_address, args=(peer, ))

    def _peer_address(self, peer: str):
        return xzyre.zyre_peer_address(self._zyre, peer)

    async def peer_header_value(self, peer: str, name: str) -> str:
        """
        Return the value of a header of a connected peer.
        Returns null if peer or key doesn't exits.
        """
        return await self.spawn(self._peer_header_value, args=(peer, name))

    def _peer_header_value(self, peer: str, name: str) -> str:
        return xzyre.zyre_peer_header_value(self._zyre, peer, name)

    async def set_header(self, name: str, value: str):
        """
        Set node header; these are provided to other nodes during discovery
        and come in each ENTER message.
        """
        await self.spawn(self._set_header, args=(name, value))

    def _set_header(self, name: str, value: str):
        xzyre.zyre_set_header(self._zyre, name, value)

    def set_evasive_timeout(self, ms):
        xzyre.zyre_set_evasive_timeout(self._zyre, ms)

    def set_expired_timeout(self, ms):
        xzyre.zyre_set_expired_timeout(self._zyre, ms)

    def set_interval(self, ms):
        xzyre.zyre_set_interval(self._zyre, ms)
