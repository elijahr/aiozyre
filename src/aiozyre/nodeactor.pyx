# cython: language_level=3

import asyncio
import logging
import queue
import sys
import threading


from . import messages
from .exceptions import StartFailed, StopFailed, Stopped


# Importing cython.parallel ensures CPython's thread state is initialized properly
# See https://bugs.python.org/issue20891 and https://github.com/python/cpython/pull/5425
# and https://github.com/opensocdebug/osd-sw/issues/37
cimport cython.parallel

from cpython.ref cimport Py_INCREF, Py_DECREF
from libc.stdlib cimport free
from libc.string cimport strcmp

from . import futures
from . import nodeconfig
from . cimport signals
from . cimport util
from . cimport zyre as z


logger = logging.getLogger('aiozyre')


cdef class NodeActor:
    def __cinit__(
        self,
        *,
        config: nodeconfig.NodeConfig,
        loop: asyncio.AbstractEventLoop
    ):
        self.config = config
        self.loop = loop
        self.zactor_pipe = NULL
        self.zactor = NULL
        self.zpoller = NULL
        self.zyre = NULL
        self.zthreadid = -1
        self.lthreadid = threading.get_ident()
        self.started = None
        self.stopped = None

        # Use a non-thread-safe awaitable queue for sending messages from the zactor thread.
        # We achieve thread safety by using loop.call_soon_threadsafe to place
        # items in the queue from the zactor thread.
        self.outbox = asyncio.Queue()

        # Use a thread-safe queue, non-awaitable queue for sending messages to the zactor thread.
        # The zactor thread can't async/await since it is a cdef function, and since it is a separate thread
        # it is fine for it to block while waiting for a message.
        self.inbox = queue.Queue()

    def __init__(
        self,
        *,
        config: nodeconfig.NodeConfig,
        loop: asyncio.AbstractEventLoop
    ):
        pass

    def __dealloc__(self):
        if self.zpoller is not NULL:
            logger.warning('NodeActor.zpoller could not be deallocated')
        if self.zyre is not NULL:
            logger.warning('NodeActor.zyre could not be deallocated')
        if self.zactor_pipe is not NULL:
            logger.warning('NodeActor.zactor_pipe could not be deallocated')
        if self.zactor is not NULL:
            logger.warning('NodeActor.zactor could not be deallocated')

    def assert_lthread(self):
        assert threading.get_ident() == self.lthreadid, \
            '%s must be called from the loop thread' % sys._getframe(1).f_code.co_name

    def assert_zthread(self):
        assert threading.get_ident() == self.zthreadid, \
            '%s must be called from the zactor thread' % sys._getframe(1).f_code.co_name

    def start(self):
        """
        Start the node actor thread.

        This method is *not* thread safe and should only be called from the event loop thread.
        """
        self.assert_lthread()
        if self.started is not None:
            raise StopFailed('NodeActor already running')
        # Steal a reference to the future for the duration of zactor's run;
        # actor_run calls Py_DECREF on termination.
        Py_INCREF(self)

        self.started = futures.ThreadSafeFuture(loop=self.loop)
        self.stopped = futures.ThreadSafeFuture(loop=self.loop)

        with nogil:
            zactor = z.zactor_new(node_act, <void*>self)

        if zactor is NULL:
            Py_DECREF(self)
            raise MemoryError("Could not create zactor instance")

        self.zactor = zactor

    def stop(self):
        """
        Stop the node actor thread.

        This method is *not* thread safe and should only be called from the event loop thread.
        """
        self.assert_lthread()
        if self.started is None:
            raise StopFailed('NodeActor not running')
        with nogil:
            z.zactor_destroy(&self.zactor)
            self.zactor = NULL

        # We stole a reference to the future in NodeActor.start(), give it back
        Py_DECREF(self)

    def stop_sync(self):
        yield from self.stop().__await__()

    def give(self, fut: futures.ThreadSafeFuture):
        """
        Give a future for processing by the zactor thread.
        The future's result will be the corresponding zyre_* function's return value.

        This method is thread safe.
        """
        self.inbox.put(fut)
        self.loop.call_soon_threadsafe(self.signal_incoming)

    def take(self, timeout: int = None) -> messages.Msg:
        """
        Receive a future for processing by the zactor thread.

        This method is thread safe.
        """
        return self.inbox.get(timeout=timeout)

    def emit(self, msg: messages.Msg):
        """
        Emit an incoming zyre message.

        This method is thread safe.
        """
        self.loop.call_soon_threadsafe(self.outbox.put_nowait, msg)

    def signal_incoming(self):
        """
        Notify the zactor thread to check its inbox.

        This method is *not* thread safe and should only be called from the event loop thread.
        """
        self.assert_lthread()
        with nogil:
            # notify zactor's poller to check inbox
            z.zstr_send(self.zactor, signals.INCOMING)

    def configure(object self):
        """
        Configure and start the zyre node for this zactor.

        This method is *not* thread safe and should only be called from the zactor thread.
        """

        self.assert_zthread()
        name = self.config.name.encode('utf8')
        self.zyre = z.zyre_new(name)
        if self.zyre is NULL:
            raise MemoryError('Could not create zyre instance')

        if self.config.verbose:
            z.zyre_set_verbose(self.zyre)

        for k, v in self.config.headers.items():
            k = k.encode('utf8')
            v = v.encode('utf8')
            key = <char*>k
            value = <char*>v
            z.zyre_set_header(self.zyre, key, "%s", value)

        if self.config.interface:
            interface = self.config.interface.encode('utf8')
            interface = <char*>interface
            z.zyre_set_interface(self.zyre, interface)

        if self.config.endpoint:
            endpoint = self.config.endpoint.encode('utf8')
            endpoint = <char*>endpoint
            z.zyre_set_endpoint(self.zyre, "%s", endpoint)

        if self.config.gossip_endpoint:
            gossip_endpoint = self.config.gossip_endpoint.encode('utf8')
            gossip_endpoint = <char*>gossip_endpoint
            z.zyre_gossip_connect(self.zyre, "%s", gossip_endpoint)
            z.zyre_gossip_bind(self.zyre, "%s", gossip_endpoint)

        if self.config.evasive_timeout_ms is not None:
            z.zyre_set_evasive_timeout(self.zyre, self.config.evasive_timeout_ms)

        if self.config.expired_timeout_ms is not None:
            z.zyre_set_expired_timeout(self.zyre, self.config.expired_timeout_ms)

        if z.zyre_start(self.zyre) != 0:
            z.zyre_destroy(&self.zyre)
            raise StartFailed('Could not start zyre instance')

        self.zpoller = z.zpoller_new(self.zactor_pipe, NULL)
        if self.zpoller is NULL:
            z.zyre_destroy(&self.zyre)
            raise MemoryError('Could not create zpoller instance')

        z.zpoller_add(self.zpoller, z.zyre_socket(self.zyre))

        for g in self.config.groups:
            group = g.encode('utf8')
            group = <char*>group
            z.zyre_join(self.zyre, group)

        return 0

    def listen(self):
        """
        Listen for socket and inbox events and process them. Runs on the zactor thread until stopped.

        This method is *not* thread safe and should only be called from the zactor thread.
        """
        self.assert_zthread()
        cdef:
            int terminated = 0
            void * which
            char * cmd
            z.zmsg_t * zmsg
        with nogil:
            while not (terminated or z.zsys_interrupted):
                which = z.zpoller_wait(self.zpoller, -1)
                if which is z.zyre_socket(self.zyre):
                    zmsg = z.zmsg_recv(which)
                    if zmsg is NULL:
                        terminated = 1
                    else:
                        with gil:
                            msg = util.zmsg_to_msg(zmsg)
                            self.emit(msg)
                elif which is self.zactor_pipe:
                    cmd = z.zstr_recv(which)
                    if strcmp(cmd, signals.TERMINATE) == 0:
                        terminated = 1
                    elif strcmp(cmd, signals.INCOMING) == 0:
                        with gil:
                            self.process_inbox()
                    else:
                        with gil:
                            logger.error('node_actor_loop: received unknown cmd %s' % (<bytes>cmd).decode('utf8'))
                    free(cmd)
                if z.zpoller_terminated(self.zpoller):
                    terminated = 1

    def process_inbox(self):
        """
        Dequeue an item (future) from the inbox, process it, and set its result.

        This method is *not* thread safe and should only be called from the zactor thread.
        """
        self.assert_zthread()
        cdef:
            char * group
            char * peer
            char * blob
            char * address
            char * header
            char * value
            z.zlist_t * zlist
            int sig

        try:
            fut = self.take(timeout=5)
        except TimeoutError:
            logger.warning('Received signal but no message in inbox')
            return

        Py_INCREF(fut)
        try:
            sig = fut.signal
            if sig == signals.SHOUT:
                group = fut.group
                blob = fut.blob
                with nogil:
                    z.zyre_shouts(self.zyre, group, "%s", blob)
                fut.set_result(None)
            elif sig == signals.WHISPER:
                peer = fut.peer
                blob = fut.blob
                with nogil:
                    z.zyre_whispers(self.zyre, peer, "%s", blob)
                fut.set_result(None)
            elif sig == signals.JOIN:
                group = fut.group
                with nogil:
                    z.zyre_join(self.zyre, group)
                fut.set_result(None)
            elif sig == signals.LEAVE:
                group = fut.group
                with nogil:
                    z.zyre_leave(self.zyre, group)
                fut.set_result(None)
            elif sig == signals.PEERS:
                with nogil:
                    zlist = z.zyre_peers(self.zyre)
                if zlist is not NULL:
                    retset = util.zlist_to_str_set(zlist)
                    fut.set_result(retset)
                else:
                    fut.set_result(set())
            elif sig == signals.PEERS_BY_GROUP:
                group = fut.group
                with nogil:
                    zlist = z.zyre_peers_by_group(self.zyre, group)
                if zlist is not NULL:
                    retset = util.zlist_to_str_set(zlist)
                    fut.set_result(retset)
                else:
                    fut.set_result(set())
            elif sig == signals.OWN_GROUPS:
                with nogil:
                    zlist = z.zyre_own_groups(self.zyre)
                if zlist is not NULL:
                    retset = util.zlist_to_str_set(zlist)
                    fut.set_result(retset)
                else:
                    fut.set_result(set())
            elif sig == signals.PEER_GROUPS:
                with nogil:
                    zlist = z.zyre_peer_groups(self.zyre)
                if zlist is not NULL:
                    retset = util.zlist_to_str_set(zlist)
                    fut.set_result(retset)
                else:
                    fut.set_result(set())
            elif sig == signals.PEER_HEADER_VALUE:
                peer = fut.peer
                header = fut.header
                with nogil:
                    value = z.zyre_peer_header_value(self.zyre, peer, header)
                if value is not NULL:
                    fut.set_result((<bytes>value).decode('utf8'))
                    free(value)
                else:
                    fut.set_result(None)
            else:
                fut.set_exception(ValueError('Unknown signal'))
        except Exception as exc:
            fut.set_exception(exc)
            raise
        finally:
            Py_DECREF(fut)

    def act(self):
        """
        Long running function that handles inputs and outputs from zyre <-> Node.

        This is the entrypoint for the zactor thread.
        """
        try:
            self.assert_zthread()
            # Start and configure the zyre node
            self.configure()
            # Attach the zyre node's UUID to the actor
            self.uuid = (<bytes>z.zyre_uuid(self.zyre)).decode('utf8')
            self.uuid = (<bytes>z.zyre_uuid(self.zyre)).decode('utf8')
            # Notify zmq that the zactor is ready to start receiving
            z.zsock_signal(self.zactor_pipe, 0)
            # Notify NodeActor.start() that the zactor is ready to start receiving
            self.started.set_result(True)
        except Exception as exc:
            self.started.set_exception(exc)
            # We stole a reference to the future in NodeActor.start(), give it back
            Py_DECREF(self)
            return

        exc = None
        try:
            self.listen()
            # Notify any receivers we've stopped
            self.emit(Stopped())
        except Exception as e:
            logger.exception(e)
            exc = e
        finally:
            with nogil:
                if self.zpoller is not NULL:
                    z.zpoller_destroy(&self.zpoller)
                    self.zpoller = NULL
                    self.zactor_pipe = NULL
                if self.zyre is not NULL:
                    z.zyre_stop(self.zyre)
                    z.zclock_sleep(500)
                    z.zyre_destroy(&self.zyre)
                    self.zyre = NULL

            if exc:
                self.stopped.set_exception(exc)
            else:
                # Notify NodeActor.stop() we've stopped
                self.stopped.set_result(True)


cdef void node_act(z.zsock_t * pipe, void * _self) nogil:
    """
    Long running function that handles inputs and outputs from zyre <-> Node.

    This is the entrypoint for the zactor thread.
    """
    with gil:
        self = <NodeActor>_self
        self.zthreadid = threading.get_ident()
        self.zactor_pipe = pipe
        self.act()

