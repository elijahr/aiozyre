
from czyre cimport zlist_size, zlist_t, zlist_pop, zmsg_t, zmsg_new, zmsg_pushstr, zmsg_size, zmsg_popstr


cdef set zlist_to_str_set(zlist_t* zlist):
    cdef object py_set = set()
    cdef void* item = NULL;
    while zlist_size(zlist):
        item = zlist_pop(zlist)
        b_item = b'%s' % <char*>item
        py_set.add(b_item.decode('utf8'))
    return py_set


cdef zmsg_t * msg_to_zmsg(msg: object):
    cdef zmsg_t *zmsg = zmsg_new()
    b_event = msg.event.encode('utf8')
    b_peer = msg.peer.encode('utf8')
    b_name = msg.name.encode('utf8')
    b_group = msg.group.encode('utf8')
    zmsg_pushstr(zmsg, <char*>b_event)
    zmsg_pushstr(zmsg, <char*>b_peer)
    zmsg_pushstr(zmsg, <char*>b_name)
    zmsg_pushstr(zmsg, <char*>b_group)
    zmsg_pushstr(zmsg, <char*>msg.blob)
    return zmsg


cdef object zmsg_to_msg(zmsg_t *zmsg):
    cdef char * item
    parts = {}
    for part in MSG_TEXT_PARTS:
        if not zmsg_size(zmsg):
            parts[part] = ''
            continue
        item = zmsg_popstr(zmsg)
        b_item = b'%s' % (<char*>item)
        parts[part] = b_item.decode('utf8')
    if zmsg_size(zmsg):
        item = zmsg_popstr(zmsg)
        # blob might be binary data, so don't decode it
        blob = b'%s' % (<bytes>item)
    else:
        blob = b''
    parts[MSG_BIN_PART] = blob
    msg =  Msg(**parts)
    return msg