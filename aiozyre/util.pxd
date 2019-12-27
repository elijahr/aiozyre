from .zyrec cimport zmsg_t, zlist_t

cdef set zlist_to_str_set(zlist_t* zlist)

cdef zmsg_t * msg_to_zmsg(msg: object)

cdef object zmsg_to_msg(zmsg_t *zmsg)