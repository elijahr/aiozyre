# cython: language_level=3

from . cimport zyre as z


cdef set zlist_to_str_set(z.zlist_t * zlist)


cdef set zlist_to_bytes_set(z.zlist_t * zlist)


cdef object zmsg_to_msg(z.zmsg_t * zmsg)