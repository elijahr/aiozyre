# cython: language_level=3

"""
Cython bindings for Zyre and various related zmq/czmq utilities
"""

cdef class Nothing:
    """
    This only exists so that the module has an entrypoint
    """
    pass