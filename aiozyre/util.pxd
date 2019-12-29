# cython: language_level=3

from .zyrec cimport zmsg_t, zlist_t

cdef set zlist_to_str_set(zlist_t** zlist_p)

cdef zmsg_t * msg_to_zmsg(msg: object)

cdef object zmsg_to_msg(zmsg_t** zmsg_p)

cdef set zmsg_to_str_set(zmsg_t** zmsg_p)

cdef zmsg_t * zlist_to_zmsg(zlist_t** zlist) nogil