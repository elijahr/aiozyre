# cython: language_level=3

import asyncio
import queue

from typing import Union, Mapping, Iterable, Set, Coroutine

from .exceptions import NodeStartError, NodeStopError
from .msg import Msg

from cpython.ref cimport Py_INCREF
from libcpp cimport bool

from . cimport actor
from . cimport futures
from . cimport zyre as z
from . cimport signals


cdef class Node:
    cpdef public str name
    cpdef public str uuid
    cpdef public object headers
    cpdef public object groups
    cpdef public str endpoint
    cpdef public str gossip_endpoint
    cpdef public int evasive_timeout_ms
    cpdef public int expired_timeout_ms
    cpdef public int verbose
    cpdef public object inbox
    cpdef public object outbox
    cpdef public object started
    cpdef public object stopped
    cpdef public object loop

    # private
    cpdef object startstoplock
    cpdef z.zactor_t * zactor

    def __cinit__(
        self,
        name: str, * ,
        headers: Mapping = None,
        groups: Union[None, Iterable[str]] = None,
        endpoint: str = None,
        gossip_endpoint: str = None,
        evasive_timeout_ms: int = None,
        expired_timeout_ms: int = None,
        verbose: bool = False,
        loop: asyncio.AbstractEventLoop = None,
    ):
        """
        Constructor, creates a new Zyre node. Note that until you start the
        node it is silent and invisible to other nodes on the network.
        The node name is provided to other nodes during discovery.
        """
        self.name = name
        self.uuid = None
        self.headers = headers or {}
        self.groups = groups or set()
        self.endpoint = endpoint
        self.gossip_endpoint = gossip_endpoint
        self.evasive_timeout_ms = evasive_timeout_ms
        self.expired_timeout_ms = expired_timeout_ms
        self.verbose = verbose
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.startstoplock = asyncio.Lock()
        self.started = asyncio.Event()
        self.stopped = asyncio.Event()

        # Use a non-thread-safe queue for receiving messages from the zactor thread.
        # We achieve thread safety by using loop.call_soon_threadsafe to place
        # items in the queue from the zactor thread.
        self.inbox = asyncio.Queue()

        # Use a thread-safe queue for sending messages to the zactor thread
        self.outbox = queue.Queue()

        self.zactor = NULL

    def __init__(
        self,
        name: str, * ,
        headers: Mapping = None,
        groups: Union[None, Iterable[str]] = None,
        endpoint: str = None,
        gossip_endpoint: str = None,
        evasive_timeout_ms: int = None,
        expired_timeout_ms: int = None,
        verbose: bool = False
    ):
        pass

    def __dealloc__(self):
        if self.zactor is not NULL:
            z.zactor_destroy(&self.zactor)
            self.zactor = NULL

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.uuid)

    @property
    def running(self) -> bool:
        return self.started.is_set()

    async def start(self):
        """
        Start node, after setting header values. When you start a node it
        begins discovery and connection. Returns 0 if OK, -1 if it wasn't
        possible to start the node.
        """
        cdef z.zactor_t * zactor
        cdef void * fut_p
        async with self.startstoplock:
            if self.running:
                raise NodeStartError('Node already running')
            fut = futures.StartFuture(node=self, loop=self.loop)
            fut_p = <void*>fut
            # Steal a reference to the future for the duration of zactor's run;
            # node_zactor_fn calls Py_DECREF on termination.
            Py_INCREF(fut)
            with nogil:
                zactor = z.zactor_new(actor.node_zactor_fn, fut_p)
            self.zactor = zactor
            await asyncio.ensure_future(fut, loop=self.loop)
            self.started.set()

    async def stop(self):
        """
        Stop node; this signals to other peers that this node will go away.
        This is polite; however you can also just destroy the node without
        stopping it.
        """
        async with self.startstoplock:
            if not self.running:
                raise NodeStopError('Node not running')
            fut = futures.StopFuture(loop=self.loop)
            self.outbox.put_nowait(fut)
            with nogil:
                # notify zactor to check outbox
                z.zstr_send(self.zactor, signals.INCOMING)
            await asyncio.ensure_future(fut, loop=self.loop)
            self.started.clear()

    async def recv(self) -> Coroutine[Msg]:
        """
        Receive next message from network; the message may be a control
        message (ENTER, EXIT, JOIN, LEAVE) or data (WHISPER, SHOUT).
        Returns Msg object, or NULL if interrupted
        """
        msg = await self.inbox.get()
        if isinstance(msg, Exception):
            raise msg
        return msg

    async def shout(self, group: str, blob: bytes):
        """
        Send message to a group
        """
        fut = futures.ShoutFuture(group=group, blob=blob, loop=self.loop)
        self.outbox.put_nowait(fut)
        with nogil:
            # notify zactor to check outbox
            z.zstr_send(self.zactor, signals.INCOMING)
        await asyncio.ensure_future(fut, loop=self.loop)

    async def whisper(self, peer: str, blob: bytes):
        """
        Send message to single peer, specified as a UUID string
        """
        fut = futures.WhisperFuture(peer=peer, blob=blob, loop=self.loop)
        self.outbox.put_nowait(fut)
        with nogil:
            # notify zactor to check outbox
            z.zstr_send(self.zactor, signals.INCOMING)
        await asyncio.ensure_future(fut, loop=self.loop)

    async def join(self, group: str):
        """
        Join a named group; after joining a group you can send messages to
        the group and all Zyre nodes in that group will receive them.
        """
        fut = futures.JoinFuture(group=group, loop=self.loop)
        self.outbox.put_nowait(fut)
        with nogil:
            # notify zactor to check outbox
            z.zstr_send(self.zactor, signals.INCOMING)
        await asyncio.ensure_future(fut, loop=self.loop)

    async def leave(self, group: str):
        """
        Leave a named group
        """
        fut = futures.LeaveFuture(group=group, loop=self.loop)
        self.outbox.put_nowait(fut)
        with nogil:
            # notify zactor to check outbox
            z.zstr_send(self.zactor, signals.INCOMING)
        await asyncio.ensure_future(fut, loop=self.loop)

    async def peers(self) -> Set[str]:
        """
        Return set of current peer ids.
        """
        fut = futures.PeersFuture(loop=self.loop)
        self.outbox.put_nowait(fut)
        with nogil:
            # notify zactor to check outbox
            z.zstr_send(self.zactor, signals.INCOMING)
        return await asyncio.ensure_future(fut, loop=self.loop)

    async def peers_by_group(self, group: str) -> Set[str]:
        """
        Return set of current peers of this group.
        """
        fut = futures.PeersByGroupFuture(group=group, loop=self.loop)
        self.outbox.put_nowait(fut)
        with nogil:
            # notify zactor to check outbox
            z.zstr_send(self.zactor, signals.INCOMING)
        return await asyncio.ensure_future(fut, loop=self.loop)

    async def own_groups(self) -> Set[str]:
        """
        Return set of currently joined groups.
        """
        fut = futures.OwnGroupsFuture(loop=self.loop)
        self.outbox.put_nowait(fut)
        with nogil:
            # notify zactor to check outbox
            z.zstr_send(self.zactor, signals.INCOMING)
        return await asyncio.ensure_future(fut, loop=self.loop)

    async def peer_groups(self) -> Set[str]:
        """
        Return set of groups known through connected peers.
        """
        fut = futures.PeerGroupsFuture(loop=self.loop)
        self.outbox.put_nowait(fut)
        with nogil:
            # notify zactor to check outbox
            z.zstr_send(self.zactor, signals.INCOMING)
        return await asyncio.ensure_future(fut, loop=self.loop)

    async def peer_address(self, peer: str) -> str:
        """
        Return address of peer
        """
        fut = futures.PeerAddressFuture(peer=peer, loop=self.loop)
        self.outbox.put_nowait(fut)
        with nogil:
            # notify zactor to check outbox
            z.zstr_send(self.zactor, signals.INCOMING)
        return await asyncio.ensure_future(fut, loop=self.loop)

    async def peer_header_value(self, peer: str, header: str) -> str:
        """
        Return the value of a header of a connected peer.
        Returns null if peer or key doesn't exits.
        """
        fut = futures.PeerHeaderValueFuture(peer=peer, header=header, loop=self.loop)
        self.outbox.put_nowait(fut)
        with nogil:
            # notify zactor to check outbox
            z.zstr_send(self.zactor, signals.INCOMING)
        return await asyncio.ensure_future(fut, loop=self.loop)
