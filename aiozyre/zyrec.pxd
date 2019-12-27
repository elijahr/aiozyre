# cython: language_level=3

"""
Cython bindings for Zyre and various related zmq/czmq utilities
"""

from libc.stdint cimport uint64_t
from libcpp cimport bool

cdef extern from "zyre.h":

    ctypedef unsigned char byte

    ctypedef struct zlist_t

    ctypedef struct zmsg_t

    ctypedef struct zpoller_t

    ctypedef struct zsock_t

    ctypedef struct zyre_t

    void zlist_destroy(zlist_t** self_p) nogil

    void* zlist_pop(zlist_t* self) nogil

    size_t zlist_size(zlist_t* self) nogil

    zmsg_t* zmsg_new() nogil

    size_t zmsg_size(zmsg_t* self) nogil

    int zmsg_pushstr(zmsg_t* self, char* string) nogil

    char* zmsg_popstr(zmsg_t* self) nogil

    zpoller_t* zpoller_new(void* reader) nogil

    void zpoller_destroy(zpoller_t** self_p) nogil

    int zpoller_add(zpoller_t* self, void* reader) nogil

    int zpoller_remove(zpoller_t* self, void* reader) nogil

    void* zpoller_wait(zpoller_t* self, int timeout) nogil

    bool zpoller_expired(zpoller_t* self) nogil

    bool zpoller_terminated(zpoller_t* self) nogil

    zyre_t* zyre_new(char* name) nogil

    void zyre_destroy(zyre_t** self_p) nogil

    char* zyre_uuid(zyre_t* self) nogil

    char* zyre_name(zyre_t* self) nogil

    void zyre_set_header(zyre_t* self, char* name, char* format, ...) nogil

    void zyre_set_verbose(zyre_t* self) nogil

    void zyre_set_port(zyre_t* self, int port_nbr) nogil

    void zyre_set_evasive_timeout(zyre_t* self, int interval) nogil

    void zyre_set_expired_timeout(zyre_t* self, int interval) nogil

    # void zyre_set_interval(zyre_t* self, size_t interval) nogil

    # void zyre_set_interface(zyre_t* self, char* value) nogil

    int zyre_set_endpoint(zyre_t* self, char* format, ...) nogil

    void zyre_gossip_bind(zyre_t* self, char* format, ...) nogil

    void zyre_gossip_connect(zyre_t* self, char* format, ...) nogil

    int zyre_start(zyre_t* self) nogil

    void zyre_stop(zyre_t* self) nogil

    int zyre_join(zyre_t* self, char* group) nogil

    int zyre_leave(zyre_t* self, char* group) nogil

    zmsg_t* zyre_recv(zyre_t* self) nogil

    int zyre_whisper(zyre_t* self, char* peer, zmsg_t** msg_p) nogil

    int zyre_shout(zyre_t* self, char* group, zmsg_t** msg_p) nogil

    int zyre_whispers(zyre_t* self, char* peer, char* format, ...) nogil

    int zyre_shouts(zyre_t* self, char* group, char* format, ...) nogil

    zlist_t* zyre_peers(zyre_t* self) nogil

    zlist_t* zyre_peers_by_group(zyre_t* self, char* name) nogil

    zlist_t* zyre_own_groups(zyre_t* self) nogil

    zlist_t* zyre_peer_groups(zyre_t* self) nogil

    char* zyre_peer_address(zyre_t* self, char* peer) nogil

    char* zyre_peer_header_value(zyre_t* self, char* peer, char* name) nogil

    zsock_t* zyre_socket(zyre_t* self) nogil

    uint64_t zyre_version() nogil

