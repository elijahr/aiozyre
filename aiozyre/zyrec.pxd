# cython: language_level=3

"""
Cython bindings for Zyre and various related zmq/czmq utilities
"""

from libc.stdint cimport uint64_t
from libcpp cimport bool

ctypedef unsigned char byte


cdef extern from "zyre.h" nogil:

    # zsys.h

    int zsys_interrupted

    # zclock.h

    void zclock_sleep (int msecs)

    # zsock.h

    ctypedef struct zsock_t

    int zsock_signal (void * self, byte status)

    int zsock_wait (void * self)

    # zlist.h

    ctypedef struct zlist_t

    void zlist_destroy(zlist_t ** self_p)

    void * zlist_pop(zlist_t * self)

    size_t zlist_size(zlist_t * self)

    # zframe.h

    ctypedef struct zframe_t

    zframe_t * zframe_recv (void *source)

    byte * zframe_data (zframe_t *self)

    void zframe_destroy (zframe_t **self_p)

    # zmsg.h

    ctypedef struct zmsg_t

    zmsg_t * zmsg_new()

    void zmsg_destroy(zmsg_t ** self_p)

    zmsg_t * zmsg_recv (void *source)

    size_t zmsg_size(zmsg_t * self)

    int zmsg_pushstr(zmsg_t * self, char * string)

    int zmsg_addstr(zmsg_t * self, char * string)

    char * zmsg_popstr(zmsg_t * self)

    zmsg_t * zmsg_popmsg(zmsg_t * self)

    int zmsg_send (zmsg_t **self_p, void *dest)

    int zmsg_addmsg (zmsg_t *self, zmsg_t **msg_p)

    int zmsg_addmem (zmsg_t *self, const void *src, size_t size)

    int zmsg_pushmem (zmsg_t *self, const void *src, size_t size)

    zframe_t * zmsg_pop (zmsg_t *self)

    # zstr.h

    int zstr_send (void *dest, const char *string)

    int zstr_sendx (void * dest, const char * string, ...)

    char * zstr_recv (void *source)

    int zstr_recvx (void *source, char **string_p, ...)

    # zactor.h

    ctypedef void zactor_fn(zsock_t * pipe, void * args)

    ctypedef struct zactor_t

    zactor_t * zactor_new(zactor_fn actor, void * args)

    int zactor_send (zactor_t * self, zmsg_t **msg_p)

    void zactor_destroy(zactor_t ** self_p)

    # zpoller.h

    ctypedef struct zpoller_t

    zpoller_t * zpoller_new(void * reader, ...)

    void zpoller_destroy(zpoller_t** self_p)

    int zpoller_add(zpoller_t * self, void * reader)

    int zpoller_remove(zpoller_t * self, void * reader)

    void * zpoller_wait(zpoller_t * self, int timeout)

    bool zpoller_expired(zpoller_t * self)

    bool zpoller_terminated(zpoller_t * self)

    ctypedef struct zyre_t

    zyre_t * zyre_new(char * name)

    void zyre_destroy(zyre_t** self_p)

    char * zyre_uuid(zyre_t * self)

    char * zyre_name(zyre_t * self)

    void zyre_set_header(zyre_t * self, char * name, char * format, ...)

    void zyre_set_verbose(zyre_t * self)

    void zyre_set_port(zyre_t * self, int port_nbr)

    void zyre_set_evasive_timeout(zyre_t * self, int interval)

    void zyre_set_expired_timeout(zyre_t * self, int interval)

    # void zyre_set_interval(zyre_t * self, size_t interval)

    # void zyre_set_interface(zyre_t * self, char * value)

    int zyre_set_endpoint(zyre_t * self, char * format, ...)

    void zyre_gossip_bind(zyre_t * self, char * format, ...)

    void zyre_gossip_connect(zyre_t * self, char * format, ...)

    int zyre_start(zyre_t * self)

    void zyre_stop(zyre_t * self)

    int zyre_join(zyre_t * self, char * group)

    int zyre_leave(zyre_t * self, char * group)

    zmsg_t * zyre_recv(zyre_t * self)

    int zyre_whisper(zyre_t * self, char * peer, zmsg_t** msg_p)

    int zyre_shout(zyre_t * self, char * group, zmsg_t** msg_p)

    int zyre_whispers(zyre_t * self, char * peer, char * format, ...)

    int zyre_shouts(zyre_t * self, char * group, char * format, ...)

    zlist_t * zyre_peers(zyre_t * self)

    zlist_t * zyre_peers_by_group(zyre_t * self, char * name)

    zlist_t * zyre_own_groups(zyre_t * self)

    zlist_t * zyre_peer_groups(zyre_t * self)

    char * zyre_peer_address(zyre_t * self, char * peer)

    char * zyre_peer_header_value(zyre_t * self, char * peer, char * name)

    zsock_t * zyre_socket(zyre_t * self)

    uint64_t zyre_version()
