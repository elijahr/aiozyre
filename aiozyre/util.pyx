# cython: language_level=3

from .zyrec cimport zlist_size, zmsg_destroy, zlist_t, zlist_pop, zmsg_t, zmsg_new, zlist_destroy, zmsg_pushstr, zmsg_size, zmsg_popstr

from .msg import Msg

# ENTER peer name headers ipaddress:port
#     a new peer has entered the network
# EVASIVE peer name
#     a peer is being evasive (quiet for too long)
# EXIT peer name
#     a peer has left the network
# JOIN peer name group
#     a peer has joined a specific group
# LEAVE peer name group
#     a peer has joined a specific group
# WHISPER peer name message
#     a peer has sent this node a message
# SHOUT peer name group message
#     a peer has sent one of our groups a message


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


cdef set zlist_to_str_set(zlist_t** zlist_p):
    """
    Convert a zlist to a set of strings.
    
    Destroys the original zlist. 
    """
    cdef object py_set = set()
    cdef void* item = NULL;
    cdef zlist_t * zlist = zlist_p[0]
    while zlist_size(zlist):
        item = zlist_pop(zlist)
        b_item = b'%s' % <char*>item
        py_set.add(b_item.decode('utf8'))
    zlist_destroy(zlist_p)
    return py_set


cdef set zmsg_to_str_set(zmsg_t ** zmsg_p):
    """
    Convert a zmsg to a set of strings.
    
    Destroys the original zmg.
    """
    cdef object py_set = set()
    cdef void* item = NULL;
    cdef zmsg_t* zmsg = zmsg_p[0]
    while zmsg_size(zmsg):
        item = zmsg_popstr(zmsg)
        b_item = b'%s' % <char*>item
        py_set.add(b_item.decode('utf8'))
    zmsg_destroy(zmsg_p)
    return py_set


cdef zmsg_t* zlist_to_zmsg(zlist_t** zlist) nogil:
    """
    Convert a zlist to a zmsg.
    
    Destroys the original zlist.
    """
    cdef zmsg_t * zmsg = zmsg_new()
    cdef char* item;
    while zlist_size(<zlist_t *>zlist[0]):
        item = <char *>zlist_pop(<zlist_t *>zlist[0])
        zmsg_pushstr(zmsg, item)
    zlist_destroy(zlist)
    return zmsg


cdef zmsg_t * msg_to_zmsg(msg: object):
    parts = [msg.event.encode('utf8')]
    cdef zmsg_t * zmsg = zmsg_new()
    for slot in MSG_SLOTS[msg.event]:
        item = getattr(msg, slot, None) or ''
        if isinstance(item, str):
            item = item.encode('utf8')
        parts.append(item)
    for item in parts:
        zmsg_pushstr(zmsg, <char *>item)
    return zmsg


cdef object zmsg_to_msg(zmsg_t **zmsg_p):
    """
    Convert a zmsg to a Msg instance.
    
    Destroys the original zmg.
    """
    cdef char * item
    cdef zmsg_t * zmsg = zmsg_p[0]
    if not zmsg_size(zmsg):
        raise ValueError('Invalid message')
    item = zmsg_popstr(zmsg)
    event = item.decode('utf8')
    parts = {'event': event}
    event = item.decode('utf8')
    parts = {'event': event}
    for slot in MSG_SLOTS[event]:
        if not zmsg_size(zmsg):
            raise ValueError('Invalid message')
        item = zmsg_popstr(zmsg)
        if slot not in BIN_SLOTS:
            parts[slot] = item.decode('utf8')
        else:
            parts[slot] = item
    msg =  Msg(**parts)
    zmsg_destroy(zmsg_p)
    return msg