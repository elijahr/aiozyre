# cython: language_level=3


import asyncio
import queue

from cpython.ref cimport Py_INCREF, Py_DECREF
from cpython.pystate cimport PyGILState_STATE, PyGILState_Ensure, PyGILState_Release
from libcpp cimport bool

from typing import Union, Mapping, Iterable, Set, Coroutine

from . cimport zyrec as z

# from .zyrec cimport zyre_join, zlist_destroy, zpoller_expired, \
#     zyre_set_expired_timeout, zyre_recv, zyre_set_verbose, zyre_set_endpoint, zlist_t, zyre_peer_address, \
#     zpoller_destroy, zyre_start, zyre_peer_header_value, zyre_gossip_bind, zpoller_wait, zyre_peer_groups, \
#     zyre_own_groups, zyre_whispers, zmsg_t, zyre_shout, zyre_socket, zyre_leave, zyre_name, zyre_peers_by_group, \
#     zyre_t, zyre_gossip_connect, zyre_set_header, zyre_peers, zpoller_new, zsock_t, zyre_uuid, zyre_stop, \
#     zyre_destroy, zyre_whisper, zyre_new, zyre_set_evasive_timeout, zyre_shouts, zpoller_t, zpoller_add, \
#     zactor_new, zactor_destroy, zactor_send, zsock_signal, zactor_t, zsys_interrupted, zactor_fn, zstr_sendx, \
#     zstr_recvx, zstr_recv, zmsg_recv, zmsg_popstr, zstr_send, zmsg_destroy, zclock_sleep, zmsg_popmsg, zmsg_new, \
#     zmsg_addstr, zmsg_send, zmsg_addmsg, zmsg_size, zsock_wait, zmsg_pop, zframe_t, zframe_data, byte, \
#     zframe_destroy, zmsg_pushmem, zmsg_addmem, zframe_recv

from . cimport util
from .msg import Msg

from .exceptions import NodeStartError, Timeout, Stopped, NodeRecvError, NodeStopError

# _NO_ARGS = tuple()
# _MODE_WHISPER = 1
# _MODE_SHOUT = 2

#
# hmmm make a zactor which selectively acquires the GIL to push items to a asyncio.queue
# the queue is used for recv
#
# a separate queue can be used for sending
#

cdef enum SIGNALS:
    SHOUT, WHISPER, JOIN, LEAVE, PEERS, PEERS_BY_GROUP, OWN_GROUPS, PEER_GROUPS, PEER_ADDRESS, PEER_HEADER_VALUE, \
    STOP

# ERROR_MESSAGES = {
#     ERROR_ZYRE_NEW: "zyre_new() failed",
#     ERROR_ZYRE_START: "zyre_start() failed",
#     ERROR_BAD_MSG: "bad message received"
# }

# cdef size_t BYTE_SIZE = sizeof(byte)


cdef class ThreadSafeFuture:
    cdef object future
    cdef object loop

    _asyncio_future_blocking = True

    def __cinit__(self, **kwargs):
        self.loop = kwargs['loop']
        assert isinstance(self.loop, asyncio.AbstractEventLoop)
        self.future = self.loop.create_future()

    def __init__(self, **kwargs):
        pass

    def result(self):
        """
        Return the result this future represents.

        If the future has been cancelled, raises CancelledError.  If the
        future's result isn't yet available, raises InvalidStateError.  If
        the future is done and has an exception set, this exception is raised.
        """
        return self.future.result()

    def set_result(self, result):
        """
        Set the future result.

        This method can be called from any thread but is not guaranteed to set the result immediately.
        """
        self.loop.call_soon_threadsafe(self.future.set_result, result)

    def cancel(self, *args, **kwargs):
        """
        Cancel the future and schedule callbacks.

        If the future is already done or cancelled, return False.  Otherwise,
        change the future's state to cancelled, schedule the callbacks and
        return True.

        This method can be called from any thread but is not guaranteed to cancel the future immediately.
        """
        self.loop.call_soon_threadsafe(self.future.cancel)

    def cancelled(self):
        """ Return True if the future was cancelled. """
        return self.future.cancelled()

    def done(self):
        """
        Return True if the future is done.

        Done means either that a result / exception are available, or that the
        future was cancelled.
        """
        return self.future.done()

    def exception(self):
        """
        Return the exception that was set on this future.

        The exception (or None if no exception was set) is returned only if
        the future is done.  If the future has been cancelled, raises
        CancelledError.  If the future isn't done yet, raises
        InvalidStateError.
        """
        return self.future.exception()

    def get_loop(self):
        """ Return the event loop the Future is bound to. """
        return self.future.get_loop()

    def add_done_callback(self, callback):
        """
        Add a callback to be run when the future becomes done.

        The callback is called with a single argument - the future object. If
        the future is already done when this is called, the callback is
        scheduled with call_soon.

        This method can be called from any thread but is not guaranteed to add the callback immediately.
        """
        self.loop.call_soon_threadsafe(self.future.add_done_callback, callback)

    def remove_done_callback(self, callback):
        """
        Remove all instances of a callback from the "call when done" list.

        Returns the number of callbacks removed.

        This method can be called from any thread but is not guaranteed to remove the callback immediately.
        """
        self.loop.call_soon_threadsafe(self.future.remove_done_callback, callback)

    def set_exception(self, exception):
        """
        Mark the future done and set an exception.

        If the future is already done when this method is called, raises
        InvalidStateError.

        This method can be called from any thread but is not guaranteed to set the exception immediately.
        """
        self.loop.call_soon_threadsafe(self.future.set_exception, exception)

    def __await__(self):
        return self.future.__await__()

    def __del__(self):
        return self.future.__del__()

    def __iter__(self):
        return self.future.__iter__()


cdef class ShoutFuture(ThreadSafeFuture):
    sig = SHOUT

    cpdef char * group
    cpdef char * blob

    def __cinit__(self, **kwargs):
        group = kwargs['group']
        blob = kwargs['blob']
        assert isinstance(group, str)
        assert isinstance(blob, bytes)
        cdef bytes b_group = group.encode('utf8')
        cdef char * c_group = <char*>b_group
        self.group = <char*>c_group
        self.blob = <char*>blob


cdef class WhisperFuture(ThreadSafeFuture):
    sig = WHISPER

    cpdef char * peer
    cpdef char * blob

    def __cinit__(self, **kwargs):
        peer = kwargs['group']
        blob = kwargs['blob']
        assert isinstance(peer, str)
        assert isinstance(blob, bytes)
        cdef bytes b_peer = peer.encode('utf8')
        cdef char * c_peer = <char*>b_peer
        self.peer = c_peer
        self.blob = <char*>blob


cdef class JoinFuture(ThreadSafeFuture):
    sig = JOIN

    cpdef char * group

    def __cinit__(self, **kwargs):
        group = kwargs['group']
        assert isinstance(group, str)
        cdef bytes b_group = group.encode('utf8')
        cdef char * c_group = <char*>b_group
        self.group = <char*>c_group


cdef class LeaveFuture(ThreadSafeFuture):
    sig = LEAVE

    cpdef char * group

    def __cinit__(self, **kwargs):
        group = kwargs['group']
        assert isinstance(group, str)
        cdef bytes b_group = group.encode('utf8')
        cdef char * c_group = <char*>b_group
        self.group = <char*>c_group


cdef class PeersFuture(ThreadSafeFuture):
    sig = PEERS


cdef class PeersByGroupFuture(ThreadSafeFuture):
    sig = PEERS_BY_GROUP

    cpdef char * group

    def __cinit__(self, **kwargs):
        group = kwargs['group']
        assert isinstance(group, str)
        cdef bytes b_group = group.encode('utf8')
        cdef char * c_group = <char*>b_group
        self.group = <char*>c_group


cdef class OwnGroupsFuture(ThreadSafeFuture):
    sig = OWN_GROUPS


cdef class PeerGroupsFuture(ThreadSafeFuture):
    sig = PEER_GROUPS


cdef class PeerAddressFuture(ThreadSafeFuture):
    sig = PEER_ADDRESS

    cpdef char * peer

    def __cinit__(self, **kwargs):
        peer = kwargs['group']
        assert isinstance(peer, str)
        cdef bytes b_peer = peer.encode('utf8')
        cdef char * c_peer = <char*>b_peer
        self.peer = c_peer


cdef class PeerHeaderValueFuture(ThreadSafeFuture):
    sig = PEER_HEADER_VALUE

    cpdef char * peer
    cpdef char * header

    def __cinit__(self, **kwargs):
        peer = kwargs['group']
        header = kwargs['header']
        assert isinstance(peer, str)
        assert isinstance(peer, header)
        cdef bytes b_peer = peer.encode('utf8')
        cdef char * c_peer = <char*>b_peer
        self.peer = c_peer
        cdef bytes b_header = header.encode('utf8')
        cdef char * c_header = <char*>b_header
        self.header = c_header


cdef class StopFuture(ThreadSafeFuture):
    sig = STOP


cdef class NodeStartFuture(ThreadSafeFuture):
    cdef object node

    def __cinit__(self, **kwargs):
        cdef object node = kwargs['node']
        assert isinstance(node, Node)
        self.node = node


cdef void node_zactor_fn(z.zsock_t * pipe, void * _future) nogil:
    cdef PyGILState_STATE state
    # cdef object future
    # cdef object node
    cdef char * name
    with gil:
        # Why do we use PyGILState_Ensure/PyGILState_Release in the `with gil` blocks?
        # I'm glad you asked! This is because this function runs in a pthread
        # created internally by czmq's zactor class. As such, we don't already have a
        # a reference to the GIL state. Cython barfs with a SyntaxError if code that it deems
        # GIL-requiring is not wrapped in `with gil`, but the generated C code for
        # `with gil` does not suffice for saving and restoring GIL state in this
        # wild thread. It's not very easy on the eyes but it works.
        state = PyGILState_Ensure()
        print('zfn: 1')
        future = <NodeStartFuture>_future
        node = future.node
        Py_INCREF(node)
        n = node.name.encode('utf8')
        name = <char*>n
        print('zfn: 2')
        PyGILState_Release(state)

    cdef z.zyre_t * zyre
    zyre = z.zyre_new(name)
    if zyre is NULL:
        with gil:
            state = PyGILState_Ensure()
            print('zfn: 2')
            future.set_exception(NodeStartError('Could not create zyre instance'))
            # We stole a reference to the future in Node.start(), give it back
            Py_DECREF(future)
            Py_DECREF(node)
            print('zfn: 3')
            PyGILState_Release(state)
        return

    if z.zyre_start(zyre) != 0:
        with gil:
            state = PyGILState_Ensure()
            print('zfn: 4')
            future.set_exception(NodeStartError('Could not start zyre instance'))
            # We stole a reference to the future in Node.start(), give it back
            Py_DECREF(future)
            Py_DECREF(node)
            print('zfn: 5')
            PyGILState_Release(state)
        return

    cdef char * set_header_key
    cdef char * set_header_value
    cdef char * join_group
    cdef char * endpoint
    cdef char * gossip_endpoint
    cdef char * c_uuid
    cdef str uuid
    with gil:
        state = PyGILState_Ensure()
        print('zfn: 6')
        for k, v in node.headers.items():
            b_k = k.encode('utf8')
            b_v = v.encode('utf8')
            set_header_key = <char *>b_k
            set_header_value = <char *>b_v
            z.zyre_set_header(zyre, set_header_key, set_header_value)

        for g in node.groups:
            b_g = g.encode('utf8')
            join_group = <char*>b_g
            z.zyre_join(zyre, join_group)

        if node.endpoint and node.gossip_endpoint:
            b_e = node.endpoint.encode('utf8')
            b_ge = node.gossip_endpoint.encode('utf8')
            endpoint = <char *>b_e
            gossip_endpoint = <char *>b_ge
            z.zyre_set_endpoint(zyre, "%s", endpoint)
            z.zyre_gossip_connect(zyre, "%s", gossip_endpoint)
            z.zyre_gossip_bind(zyre, "%s", gossip_endpoint)

        if node.evasive_timeout_ms is not None:
            z.zyre_set_evasive_timeout(zyre, node.evasive_timeout_ms)

        if node.expired_timeout_ms is not None:
            z.zyre_set_expired_timeout(zyre, node.expired_timeout_ms)

        if node.verbose:
            z.zyre_set_verbose(zyre)

        c_uuid = z.zyre_uuid(zyre)
        uuid = c_uuid.decode('utf8')

        future.set_result(uuid)

        # We stole a reference to the future in Node.start(), give it back
        Py_DECREF(future)

        print('zfn: 7')
        PyGILState_Release(state)

    cdef object inbox
    cdef object outbox
    cdef object loop
    with gil:
        print('zfn: 8')
        state = PyGILState_Ensure()
        inbox = node.inbox
        outbox = node.outbox
        loop = node.loop
        Py_INCREF(inbox)
        Py_INCREF(outbox)
        Py_INCREF(loop)
        PyGILState_Release(state)

    node_zactor_loop(pipe, zyre, inbox, outbox, loop)

    z.zyre_stop(zyre)
    z.zclock_sleep(100)
    z.zyre_destroy(&zyre)
    with gil:
        state = PyGILState_Ensure()
        print('zfn: 99')
        Py_DECREF(node)
        Py_DECREF(inbox)
        Py_DECREF(outbox)
        Py_DECREF(loop)
        PyGILState_Release(state)


cdef void node_zactor_loop(z.zsock_t * pipe, z.zyre_t * zyre, object inbox, object outbox, object loop) nogil:
    cdef z.zpoller_t * zpoller
    cdef void * which

    cdef char * group
    cdef char * peer
    cdef char * blob
    cdef char * address
    cdef char * header
    cdef char * value
    cdef z.zlist_t * zlist

    cdef int terminated = 0
    cdef int sig

    cdef z.zsock_t * sock = z.zyre_socket(zyre)

    zpoller = z.zpoller_new(pipe, sock, NULL)

    while not (terminated or z.zsys_interrupted):
        with gil:
            state = PyGILState_Ensure()
            print('zfnl: 1')
            PyGILState_Release(state)
        which = z.zpoller_wait(zpoller, 200)
        with gil:
            state = PyGILState_Ensure()
            print('zfnl: 2')
            PyGILState_Release(state)
        if which is sock:
            zmsg_in = z.zmsg_recv(which)
            if not zmsg_in:
                with gil:
                    state = PyGILState_Ensure()
                    print('zfnl: 2')
                    PyGILState_Release(state)
                terminated = 1
            with gil:
                state = PyGILState_Ensure()
                print('zfnl: 3')
                msg = util.zmsg_to_msg(&zmsg_in)
                loop.call_soon_threadsafe(outbox.put_nowait, msg)
                PyGILState_Release(state)
        elif which is pipe:
            with gil:
                state = PyGILState_Ensure()
                print('zfnl: 4')
                PyGILState_Release(state)
            z.zsock_wait(which)
            with gil:
                state = PyGILState_Ensure()
                fut = inbox.get()
                sig = fut.sig
                Py_INCREF(fut)
                PyGILState_Release(state)
            if sig == SHOUT:
                with gil:
                    state = PyGILState_Ensure()
                    group = fut.group
                    blob = fut.blob
                    PyGILState_Release(state)
                z.zyre_shouts(zyre, group, "%s", blob)
                with gil:
                    state = PyGILState_Ensure()
                    fut.set_result(None)
                    PyGILState_Release(state)
            elif sig == WHISPER:
                with gil:
                    state = PyGILState_Ensure()
                    peer = fut.peer
                    blob = fut.blob
                    PyGILState_Release(state)
                z.zyre_whispers(zyre, peer, "%s", blob)
                with gil:
                    state = PyGILState_Ensure()
                    fut.set_result(None)
                    PyGILState_Release(state)
            elif sig == JOIN:
                with gil:
                    state = PyGILState_Ensure()
                    group = fut.group
                    PyGILState_Release(state)
                z.zyre_join(zyre, group)
                with gil:
                    state = PyGILState_Ensure()
                    fut.set_result(None)
                    PyGILState_Release(state)
            elif sig == LEAVE:
                with gil:
                    state = PyGILState_Ensure()
                    group = fut.group
                    PyGILState_Release(state)
                z.zyre_leave(zyre, group)
                with gil:
                    state = PyGILState_Ensure()
                    fut.set_result(None)
                    PyGILState_Release(state)
            elif sig == PEERS:
                zlist = z.zyre_peers(zyre)
                with gil:
                    state = PyGILState_Ensure()
                    retset = util.zlist_to_str_set(&zlist)
                    fut.set_result(retset)
                    PyGILState_Release(state)
            elif sig == PEERS_BY_GROUP:
                with gil:
                    state = PyGILState_Ensure()
                    group = fut.group
                    PyGILState_Release(state)
                zlist = z.zyre_peers_by_group(zyre, group)
                with gil:
                    state = PyGILState_Ensure()
                    retset = util.zlist_to_str_set(&zlist)
                    fut.set_result(retset)
                    PyGILState_Release(state)
            elif sig == OWN_GROUPS:
                zlist = z.zyre_own_groups(zyre)
                with gil:
                    state = PyGILState_Ensure()
                    retset = util.zlist_to_str_set(&zlist)
                    fut.set_result(retset)
                    PyGILState_Release(state)
            elif sig == PEER_GROUPS:
                zlist = z.zyre_peer_groups(zyre)
                with gil:
                    state = PyGILState_Ensure()
                    retset = util.zlist_to_str_set(&zlist)
                    fut.set_result(retset)
                    PyGILState_Release(state)
            elif sig == PEER_ADDRESS:
                with gil:
                    state = PyGILState_Ensure()
                    peer = fut.peer
                    PyGILState_Release(state)
                address = z.zyre_peer_address(zyre, peer)
                with gil:
                    state = PyGILState_Ensure()
                    fut.set_result(address)
                    PyGILState_Release(state)
            elif sig == PEER_HEADER_VALUE:
                with gil:
                    state = PyGILState_Ensure()
                    peer = fut.peer
                    header = fut.header
                    PyGILState_Release(state)
                value = z.zyre_peer_header_value(zyre, peer, header)
                with gil:
                    state = PyGILState_Ensure()
                    fut.set_result(value)
                    PyGILState_Release(state)
            elif sig == STOP:
                terminated = 1
                with gil:
                    state = PyGILState_Ensure()
                    fut.set_result(None)
                    PyGILState_Release(state)
            else:
                with gil:
                    state = PyGILState_Ensure()
                    fut.set_exception(ValueError('Unknown signal'))
                    PyGILState_Release(state)
            if z.zpoller_expired(zpoller):
                with gil:
                    state = PyGILState_Ensure()
                    Py_DECREF(fut)
                    PyGILState_Release(state)
            with gil:
                state = PyGILState_Ensure()
                Py_DECREF(fut)
                PyGILState_Release(state)

    with gil:
        state = PyGILState_Ensure()
        print('zfnl: 99')
        PyGILState_Release(state)
    z.zpoller_destroy(&zpoller)


cdef class Node:
    # public
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

        # self.zactor = NULL

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

    # def __dealloc__(self):
    #     if self.zactor is not NULL:
    #         zactor_destroy (&self.zactor)
    #         self.zactor = NULL

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
        if self.running:
            raise NodeStartError('Node already running')
        cdef z.zactor_t * zactor
        cdef void * fut_p
        print('Getting startstoplock')
        async with self.startstoplock:
            print('Got stopstartlock')
            fut = NodeStartFuture(node=self, loop=self.loop)
            fut_p = <void*>fut
            # Steal a reference to the future for the duration of zactor's run;
            # node_zactor_fn calls Py_DECREF on termination.
            Py_INCREF(fut)
            print('calling zactor')
            with nogil:
                zactor = z.zactor_new(node_zactor_fn, fut_p)
            self.zactor = zactor
            print('Hello')
            self.uuid = await asyncio.ensure_future(fut, loop=self.loop)
            print('H2')
            self.started.set()
            print('H3')

    async def stop(self):
        """
        Stop node; this signals to other peers that this node will go away.
        This is polite; however you can also just destroy the node without
        stopping it.
        """
        if not self.running:
            raise NodeStopError('Node not running')
        async with self.startstoplock:
            fut = StopFuture(loop=self.loop)
            self.outbox.put(fut)
            with nogil:
                # notify zactor to check outbox
                z.zsock_signal(self.zactor, 0)
            await asyncio.ensure_future(fut, loop=self.loop)

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
        fut = ShoutFuture(group=group, blob=blob, loop=self.loop)
        self.outbox.put(fut)
        with nogil:
            # notify zactor to check outbox
            z.zsock_signal(self.zactor, 0)
        await asyncio.ensure_future(fut, loop=self.loop)

    async def whisper(self, peer: str, blob: bytes):
        """
        Send message to single peer, specified as a UUID string
        """
        fut = WhisperFuture(peer=peer, blob=blob, loop=self.loop)
        self.outbox.put(fut)
        with nogil:
            # notify zactor to check outbox
            z.zsock_signal(self.zactor, 0)
        await asyncio.ensure_future(fut, loop=self.loop)

    async def join(self, group: str):
        """
        Join a named group; after joining a group you can send messages to
        the group and all Zyre nodes in that group will receive them.
        """
        fut = JoinFuture(group=group, loop=self.loop)
        self.outbox.put(fut)
        with nogil:
            # notify zactor to check outbox
            z.zsock_signal(self.zactor, 0)
        await asyncio.ensure_future(fut, loop=self.loop)

    async def leave(self, group: str):
        """
        Leave a named group
        """
        fut = LeaveFuture(group=group, loop=self.loop)
        self.outbox.put(fut)
        with nogil:
            # notify zactor to check outbox
            z.zsock_signal(self.zactor, 0)
        await asyncio.ensure_future(fut, loop=self.loop)

    async def peers(self) -> Set[str]:
        """
        Return set of current peer ids.
        """
        fut = PeersFuture(loop=self.loop)
        self.outbox.put(fut)
        with nogil:
            # notify zactor to check outbox
            z.zsock_signal(self.zactor, 0)
        return await asyncio.ensure_future(fut, loop=self.loop)

    async def peers_by_group(self, group: str) -> Set[str]:
        """
        Return set of current peers of this group.
        """
        fut = PeersByGroupFuture(group=group, loop=self.loop)
        self.outbox.put(fut)
        with nogil:
            # notify zactor to check outbox
            z.zsock_signal(self.zactor, 0)
        return await asyncio.ensure_future(fut, loop=self.loop)

    async def own_groups(self) -> Set[str]:
        """
        Return set of currently joined groups.
        """
        fut = OwnGroupsFuture(loop=self.loop)
        self.outbox.put(fut)
        with nogil:
            # notify zactor to check outbox
            z.zsock_signal(self.zactor, 0)
        return await asyncio.ensure_future(fut, loop=self.loop)

    async def peer_groups(self) -> Set[str]:
        """
        Return set of groups known through connected peers.
        """
        fut = PeerGroupsFuture(loop=self.loop)
        self.outbox.put(fut)
        with nogil:
            # notify zactor to check outbox
            z.zsock_signal(self.zactor, 0)
        return await asyncio.ensure_future(fut, loop=self.loop)

    async def peer_address(self, peer: str) -> str:
        """
        Return address of peer
        """
        fut = PeerAddressFuture(peer=peer, loop=self.loop)
        self.outbox.put(fut)
        with nogil:
            # notify zactor to check outbox
            z.zsock_signal(self.zactor, 0)
        return await asyncio.ensure_future(fut, loop=self.loop)

    async def peer_header_value(self, peer: str, header: str) -> str:
        """
        Return the value of a header of a connected peer.
        Returns null if peer or key doesn't exits.
        """
        fut = PeerHeaderValueFuture(peer=peer, header=header, loop=self.loop)
        self.outbox.put(fut)
        with nogil:
            # notify zactor to check outbox
            z.zsock_signal(self.zactor, 0)
        return await asyncio.ensure_future(fut, loop=self.loop)
