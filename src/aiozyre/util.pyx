# cython: language_level=3

from .messages import Msg

from . cimport zyre as z


# Zyre message grammar:
#     ENTER peer name headers ipaddress:port
#         a new peer has entered the network
#     EVASIVE peer name
#         a peer is being evasive (quiet for too long)
#     EXIT peer name
#         a peer has left the network
#     JOIN peer name group
#         a peer has joined a specific group
#     LEAVE peer name group
#         a peer has joined a specific group
#     WHISPER peer name message
#         a peer has sent this node a message
#     SHOUT peer name group message
#         a peer has sent one of our groups a message


MSG_SLOTS = {
    'ENTER': ('peer', 'name', 'headers', 'address'),
    'EVASIVE': ('peer', 'name'),
    'EXIT': ('peer', 'name'),
    'JOIN': ('peer', 'name', 'group'),
    'LEAVE': ('peer', 'name', 'group'),
    'WHISPER': ('peer', 'name', 'blob'),
    'SHOUT': ('peer', 'name', 'group', 'blob')
}
BIN_SLOTS = ('blob',)


cdef set zlist_to_str_set(z.zlist_t* zlist):
    """
    Convert a zlist to a set of str objects.
    
    Destroys the original zlist. 
    """
    return {s.decode('utf8') for s in zlist_to_bytes_set(zlist)}


cdef set zlist_to_bytes_set(z.zlist_t* zlist):
    """
    Convert a zlist to a set of bytes objects.
    
    Destroys the original zlist. 
    """
    cdef object py_set = set()
    cdef void* item = NULL;
    while z.zlist_size(zlist):
        item = z.zlist_pop(zlist)
        b_item = b'%s' % <char*>item
        py_set.add(b_item)
    z.zlist_destroy(&zlist)
    return py_set


cdef object zmsg_to_msg(z.zmsg_t *zmsg):
    """
    Convert a zmsg to a Msg instance.
    
    Destroys the original zmg.
    """
    cdef char * item
    try:
        if not z.zmsg_size(zmsg):
            raise ValueError('Invalid message')
        item = z.zmsg_popstr(zmsg)
        event = item.decode('utf8')
        parts = {'event': event}
        event = item.decode('utf8')
        parts = {'event': event}
        for slot in MSG_SLOTS[event]:
            if not z.zmsg_size(zmsg):
                raise ValueError('Invalid message')
            item = z.zmsg_popstr(zmsg)
            if slot not in BIN_SLOTS:
                parts[slot] = item.decode('utf8')
            else:
                parts[slot] = item
        msg =  Msg(**parts)
        return msg
    finally:
        z.zmsg_destroy(&zmsg)