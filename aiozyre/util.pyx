# cython: language_level=3

from .msg import Msg

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


cdef set zlist_to_str_set(z.zlist_t** zlist_p):
    """
    Convert a zlist to a set of strings.
    
    Destroys the original zlist. 
    """
    cdef object py_set = set()
    cdef void* item = NULL;
    cdef z.zlist_t * zlist = zlist_p[0]
    while z.zlist_size(zlist):
        item = z.zlist_pop(zlist)
        b_item = b'%s' % <char*>item
        py_set.add(b_item.decode('utf8'))
    z.zlist_destroy(zlist_p)
    return py_set


cdef object zmsg_to_msg(z.zmsg_t **zmsg_p):
    """
    Convert a zmsg to a Msg instance.
    
    Destroys the original zmg.
    """
    cdef char * item
    cdef z.zmsg_t * zmsg = zmsg_p[0]
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
    z.zmsg_destroy(zmsg_p)
    return msg