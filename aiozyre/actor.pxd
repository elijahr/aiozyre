# cython: language_level=3

from . cimport zyre as z

cdef void node_zactor_fn(z.zsock_t * pipe, void * _future) nogil

cdef class Nothing:
    """
    This class exists solely so this cython module is cimportable
    """