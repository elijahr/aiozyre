# cython: language_level=3


cdef class ThreadSafeFuture:
    cdef public object _loop
    cdef object future


cdef class SignalFuture(ThreadSafeFuture):
    cdef public int signal


cdef class StartFuture(ThreadSafeFuture):
    cdef public object node


cdef class StopFuture(SignalFuture):
    pass


cdef class ShoutFuture(SignalFuture):
    cdef public bytes group
    cdef public bytes blob


cdef class WhisperFuture(SignalFuture):
    cdef public bytes peer
    cdef public bytes blob


cdef class JoinFuture(SignalFuture):
    cdef public bytes group


cdef class LeaveFuture(SignalFuture):
    cdef public bytes group


cdef class PeersFuture(SignalFuture):
    pass


cdef class PeersByGroupFuture(SignalFuture):
    cdef public bytes group


cdef class OwnGroupsFuture(SignalFuture):
    pass


cdef class PeerGroupsFuture(SignalFuture):
    pass


cdef class PeerAddressFuture(SignalFuture):
    cdef public bytes peer


cdef class PeerHeaderValueFuture(SignalFuture):
    cdef public bytes peer
    cdef public bytes header
