# cython: language_level=3

cdef class NodeConfig:
    cpdef public str name
    cpdef public object headers
    cpdef public object groups
    cpdef public str endpoint
    cpdef public str gossip_endpoint
    cpdef public int evasive_timeout_ms
    cpdef public int expired_timeout_ms
    cpdef public int verbose