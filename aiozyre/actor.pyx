# cython: language_level=3

from cpython.ref cimport Py_INCREF, Py_DECREF
from cpython.pystate cimport PyGILState_STATE, PyGILState_Ensure, PyGILState_Release
from libc.string cimport strcmp
from libc.stdlib cimport free

from . cimport zyre as z
from . cimport util
from . cimport futures
from . cimport signals

from .exceptions import StartFailed, Stopped

cdef void node_zactor_fn(z.zsock_t * pipe, void * _future) nogil:
    cdef PyGILState_STATE state
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
        future = <futures.StartFuture>_future
        node = future.node
        Py_INCREF(node)
        n = node.name.encode('utf8')
        name = <char*>n
        PyGILState_Release(state)

    cdef z.zyre_t * zyre
    zyre = z.zyre_new(name)
    if zyre is NULL:
        with gil:
            state = PyGILState_Ensure()
            future.set_exception(MemoryError('Could not create zyre instance'))
            # We stole a reference to the future in Node.start(), give it back
            Py_DECREF(future)
            Py_DECREF(node)
            PyGILState_Release(state)
        return

    if z.zyre_start(zyre) != 0:
        with gil:
            state = PyGILState_Ensure()
            future.set_exception(StartFailed('Could not start zyre instance'))
            # We stole a reference to the future in Node.start(), give it back
            Py_DECREF(future)
            Py_DECREF(node)
            PyGILState_Release(state)
        return

    cdef char * set_header_key
    cdef char * set_header_value
    cdef char * join_group
    cdef char * endpoint
    cdef char * gossip_endpoint
    with gil:
        state = PyGILState_Ensure()
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

        node.uuid = (<bytes>z.zyre_uuid(zyre)).decode('utf8')
        future.set_result(None)

        # We stole a reference to the future in Node.start(), give it back
        Py_DECREF(future)

        PyGILState_Release(state)

    cdef object inbox
    cdef object outbox
    cdef object loop
    with gil:
        state = PyGILState_Ensure()
        inbox = node.outbox
        outbox = node.inbox
        loop = node.loop
        Py_INCREF(inbox)
        Py_INCREF(outbox)
        Py_INCREF(loop)
        PyGILState_Release(state)

    cdef z.zpoller_t * zpoller = z.zpoller_new(pipe, NULL)
    if zpoller is NULL:
        with gil:
            state = PyGILState_Ensure()
            future.set_exception(MemoryError('Could not create zpoller'))
            # We stole a reference to the future in Node.start(), give it back
            Py_DECREF(future)
            Py_DECREF(node)
            PyGILState_Release(state)
        return

    node_zactor_loop(zpoller, pipe, zyre, inbox, outbox, loop)

    z.zyre_stop(zyre)
    z.zclock_sleep(100)
    z.zyre_destroy(&zyre)
    with gil:
        state = PyGILState_Ensure()
        loop.call_soon_threadsafe(outbox.put_nowait, Stopped())
        Py_DECREF(node)
        Py_DECREF(inbox)
        Py_DECREF(outbox)
        Py_DECREF(loop)
        PyGILState_Release(state)


cdef void node_zactor_loop(z.zpoller_t * zpoller, z.zsock_t * pipe, z.zyre_t * zyre, object inbox, object outbox, object loop) nogil:
    cdef PyGILState_STATE state
    cdef void * which
    cdef char * cmd
    cdef char * group
    cdef char * peer
    cdef char * blob
    cdef char * address
    cdef char * header
    cdef char * value
    cdef z.zlist_t * zlist
    cdef z.zmsg_t * zmsg

    cdef int terminated = 0
    cdef int sig

    cdef z.zsock_t * sock = z.zyre_socket(zyre)

    z.zpoller_add(zpoller, sock)

    # notify zmq that the zactor is ready
    z.zsock_signal(pipe, 0)

    while not (terminated or z.zsys_interrupted):
        which = z.zpoller_wait(zpoller, -1)
        if which is sock:
            zmsg_in = z.zmsg_recv(which)
            if zmsg_in is NULL:
                terminated = 1
            else:
                with gil:
                    state = PyGILState_Ensure()
                    msg = util.zmsg_to_msg(&zmsg_in)
                    loop.call_soon_threadsafe(outbox.put_nowait, msg)
                    PyGILState_Release(state)
        elif which is pipe:
            cmd = z.zstr_recv(which)
            if strcmp(cmd, signals.TERM) == 0:
                terminated = 1
            else:
                with gil:
                    state = PyGILState_Ensure()
                    fut = inbox.get()
                    Py_INCREF(fut)
                    sig = fut.signal
                    PyGILState_Release(state)
                if sig == signals.SHOUT:
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
                elif sig == signals.WHISPER:
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
                elif sig == signals.JOIN:
                    with gil:
                        state = PyGILState_Ensure()
                        group = fut.group
                        PyGILState_Release(state)
                    z.zyre_join(zyre, group)
                    with gil:
                        state = PyGILState_Ensure()
                        fut.set_result(None)
                        PyGILState_Release(state)
                elif sig == signals.LEAVE:
                    with gil:
                        state = PyGILState_Ensure()
                        group = fut.group
                        PyGILState_Release(state)
                    z.zyre_leave(zyre, group)
                    with gil:
                        state = PyGILState_Ensure()
                        fut.set_result(None)
                        PyGILState_Release(state)
                elif sig == signals.PEERS:
                    zlist = z.zyre_peers(zyre)
                    with gil:
                        state = PyGILState_Ensure()
                        retset = util.zlist_to_str_set(&zlist)
                        fut.set_result(retset)
                        PyGILState_Release(state)
                elif sig == signals.PEERS_BY_GROUP:
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
                elif sig == signals.OWN_GROUPS:
                    zlist = z.zyre_own_groups(zyre)
                    with gil:
                        state = PyGILState_Ensure()
                        retset = util.zlist_to_str_set(&zlist)
                        fut.set_result(retset)
                        PyGILState_Release(state)
                elif sig == signals.PEER_GROUPS:
                    zlist = z.zyre_peer_groups(zyre)
                    with gil:
                        state = PyGILState_Ensure()
                        retset = util.zlist_to_str_set(&zlist)
                        fut.set_result(retset)
                        PyGILState_Release(state)
                elif sig == signals.PEER_ADDRESS:
                    with gil:
                        state = PyGILState_Ensure()
                        peer = fut.peer
                        PyGILState_Release(state)
                    address = z.zyre_peer_address(zyre, peer)
                    with gil:
                        state = PyGILState_Ensure()
                        fut.set_result((<bytes>address).decode('utf8'))
                        PyGILState_Release(state)
                elif sig == signals.PEER_HEADER_VALUE:
                    with gil:
                        state = PyGILState_Ensure()
                        peer = fut.peer
                        header = fut.header
                        PyGILState_Release(state)
                    value = z.zyre_peer_header_value(zyre, peer, header)
                    with gil:
                        state = PyGILState_Ensure()
                        fut.set_result((<bytes>value).decode('utf8'))
                        PyGILState_Release(state)
                elif sig == signals.STOP:
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

            free(cmd)
            if z.zpoller_terminated(zpoller):
                terminated = 1
            with gil:
                state = PyGILState_Ensure()
                Py_DECREF(fut)
                PyGILState_Release(state)

    z.zpoller_destroy(&zpoller)

cdef class Nothing:
    """
    This class exists solely so this cython module is cimportable
    """
