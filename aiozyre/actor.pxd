# cython: language_level=3

from . cimport zyre as z


cdef class NodeActor:
    cpdef public str uuid
    cpdef public object started
    cpdef public object stopped
    cpdef public object config
    cpdef public object loop

    # private
    cdef z.zyre_t * zyre
    cdef z.zpoller_t * zpoller
    cdef z.zactor_t * zactor
    cdef z.zsock_t * zactor_pipe
    cpdef unsigned long zthreadid
    cpdef unsigned long lthreadid
    cpdef object startstoplock
    cpdef object inbox
    cpdef object outbox


cdef void node_act(z.zsock_t * pipe, void * _actor) nogil
