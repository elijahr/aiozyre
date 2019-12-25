header = '''
typedef struct {
    PyObject * callback;
    PyObject * loop;
    zsock_t * sock;
    int timeout;
} PyActorCallbackInfo;

static void 
py_actor_callback (zsock_t *pipe, void *args)
{
    PyActorCallbackInfo * info = (PyActorCallbackInfo *) args;

    zsock_signal (pipe, 0);     //  Signal "ready" to caller
    bool terminated = false;

    zpoller_t *poller = zpoller_new (pipe, info->sock, NULL);
    
    while (!terminated) {
        void *which = zpoller_wait (poller, info->timeout);
        if (which == pipe) {
            zmsg_t *msg = zmsg_recv (which);
            if (!msg) {
                break;              //  Interrupted
            }
            char *command = zmsg_popstr (msg);
            if (streq (command, "$TERM")) {
                terminated = true;
            }
            free (command);
            zmsg_destroy (&msg);
        } else if (which == info->sock) {
            // Acquire the GIL
            PyGILState_STATE gil_state;
            gil_state = PyGILState_Ensure();
            // The callback can call zyre_recv, or whatever
            PyObject * method_name = Py_BuildValue("s", "create_task", 11);
            PyObject * args = Py_BuildValue("()");
            PyObject * coro = PyEval_CallObject(info->callback, args);
            PyObject_CallMethodObjArgs(info->loop, method_name, coro, NULL);
            Py_DECREF(coro);
            Py_DECREF(method_name);
            Py_DECREF(args);
            // Release the GIL
            PyGILState_Release(gil_state);
        }
    }
    // Acquire the GIL
    PyGILState_STATE gil_state;
    gil_state = PyGILState_Ensure();
    Py_DECREF(info->loop);
    Py_DECREF(info->callback);
    // Release the GIL
    PyGILState_Release(gil_state);
    free(info);
    zpoller_destroy(&poller);
}

PyObject *
zlist_of_str_to_pyset ( zlist_t * zlist )
{
    PyObject * set = PySet_New(NULL);
    void * chars;
    PyObject * string;
    while (zlist_size(zlist) > 0) {
        chars = zlist_pop(zlist);
        if (chars) {
            string = PyUnicode_FromString((char *) chars);
            PySet_Add(set, string);
            Py_DECREF(string);
        }
    }
    return set;
}
'''

_wrap_zmq_getsockopt_int = '''
static PyObject *
_wrap_zmq_getsockopt_int(PyObject * PYBINDGEN_UNUSED(dummy), PyObject *args, PyObject *kwargs, PyObject **return_exception)
{
    PyObject *py_retval;
    int retval;
    size_t retval_size = sizeof(retval);
    int error_code;
    PyZsock_t *socket;
    zsock_t *socket_ptr;
    int option_name;
    const char *keywords[] = {"socket", "option_name", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, (char *) "O!i", (char **) keywords, &PyZsock_t_Type, &socket, &option_name)) {
        return NULL;
    }
    socket_ptr = (socket ? socket->obj : NULL);
    error_code = zmq_getsockopt((void *)socket_ptr, (int)option_name, (void *)&retval, (size_t*)&retval_size);
    // TODO, handle error codes (0, EINVAL, ETERM, ENOTSOCK, EINTR)
    py_retval = Py_BuildValue((char *) "i", retval);
    return py_retval;
}
'''

_wrap_zmq_setsockopt_int = '''
static PyObject *
_wrap_zmq_setsockopt_int(PyObject * PYBINDGEN_UNUSED(dummy), PyObject *args, PyObject *kwargs, PyObject **return_exception)
{
    PyObject *py_retval;
    int error_code;
    PyZsock_t *socket;
    zsock_t *socket_ptr;
    int option_name;
    int option_value;
    const char *keywords[] = {"socket", "option_name", "option_value", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, (char *) "O!ii", (char **) keywords, &PyZsock_t_Type, &socket, &option_name, &option_value)) {
        return NULL;
    }
    size_t option_value_size = sizeof(option_value);

    socket_ptr = (socket ? socket->obj : NULL);
    error_code = zmq_setsockopt((void*)socket_ptr, (int)option_name, (const void *)&option_value, (size_t)option_value_size);

    // TODO, handle error codes (0, EINVAL, ETERM, ENOTSOCK, EINTR)
    py_retval = Py_BuildValue((char *) "i", error_code);
    return py_retval;
}
'''

# _wrap_zactor_new = '''
# static PyObject *
# _wrap_zactor_new(PyObject * PYBINDGEN_UNUSED(dummy), PyObject *args, PyObject *kwargs, PyObject **return_exception)
# {
#     PyObject *py_retval;
#     zactor_t *retval;
#     PyObject *py_callback;
#     PyObject *loop;
#     PyZsock_t *sock;
#     zsock_t *sock_ptr;
#     int timeout;
#     const char *keywords[] = {"callback", "loop", "socket", "timeout", NULL};
#     PyZactor_t *py_zactor_t;
#
#     if (!PyArg_ParseTupleAndKeywords(args, kwargs, (char *) "OOO!i", (char **) keywords, &py_callback, &loop, &PyZsock_t_Type, &sock, &timeout)) {
#         return NULL;
#     }
#     sock_ptr = (sock ? sock->obj : NULL);
#     Py_INCREF(sock);
#     Py_INCREF(py_callback);
#     PyActorCallbackInfo * info = (PyActorCallbackInfo *) malloc(sizeof(PyActorCallbackInfo));
#     info->callback = py_callback;
#     info->loop = loop;
#     info->sock = sock_ptr;
#     info->timeout = timeout;
#     retval = zactor_new(py_actor_callback, (void*) info);
#     if (!(retval)) {
#         Py_INCREF(Py_None);
#         return Py_None;
#     }
#     py_zactor_t = PyObject_New(PyZactor_t, &PyZactor_t_Type);
#     py_zactor_t->obj = retval;
#     py_zactor_t->flags = PYBINDGEN_WRAPPER_FLAG_NONE;
#     py_retval = Py_BuildValue((char *) "N", py_zactor_t);
#     return py_retval;
# }
# '''

_wrap_zpoller_wait = '''
static PyObject *
_wrap_zpoller_wait(PyObject * PYBINDGEN_UNUSED(dummy), PyObject *args, PyObject *kwargs, PyObject **return_exception)
{
    PyObject *py_retval;
    void *retval;
    PyThreadState *py_thread_state = NULL;
    PyZpoller_t *self;
    zpoller_t *self_ptr;
    int timeout_ms;
    const char *keywords[] = {"self", "timeout_ms", NULL};
    PyZsock_t *py_zsock_t;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, (char *) "O!i", (char **) keywords, &PyZpoller_t_Type, &self, &timeout_ms)) {
        return NULL;
    }
    self_ptr = (self ? self->obj : NULL);

    if (PyEval_ThreadsInitialized ())
         py_thread_state = PyEval_SaveThread();

    retval = zpoller_wait(self_ptr, timeout_ms);
    if (py_thread_state)
         PyEval_RestoreThread(py_thread_state);    

    if (!(retval)) {
        Py_INCREF(Py_None);
        return Py_None;
    }
    py_zsock_t = PyObject_New(PyZsock_t, &PyZsock_t_Type);
    py_zsock_t->obj = (zsock_t *)retval;
    py_zsock_t->flags = PYBINDGEN_WRAPPER_FLAG_OBJECT_NOT_OWNED;
    py_retval = Py_BuildValue((char *) "N", py_zsock_t);
    return py_retval;
}
'''
_wrap_zyre_peers = '''
PyObject *
_wrap_zyre_peers(PyObject * PYBINDGEN_UNUSED(dummy), PyObject *args, PyObject *kwargs, PyObject **return_exception)
{
    PyThreadState *py_thread_state = NULL;
    PyZyre_t *self;
    zyre_t *self_ptr;
    const char *keywords[] = {"self", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, (char *) "O!", (char **) keywords, &PyZyre_t_Type, &self)) {
        return NULL;
    }
    self_ptr = (self ? self->obj : NULL);

    if (PyEval_ThreadsInitialized ())
         py_thread_state = PyEval_SaveThread();

    zlist_t * peers = zyre_peers(self_ptr);

    if (py_thread_state)
         PyEval_RestoreThread(py_thread_state);

    PyObject * set = zlist_of_str_to_pyset(peers);
    zlist_destroy(&peers);
    return set;
}
'''
_wrap_zyre_own_groups = '''
PyObject *
_wrap_zyre_own_groups(PyObject * PYBINDGEN_UNUSED(dummy), PyObject *args, PyObject *kwargs, PyObject **return_exception)
{
    PyThreadState *py_thread_state = NULL;
    PyZyre_t *self;
    zyre_t *self_ptr;
    const char *keywords[] = {"self", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, (char *) "O!", (char **) keywords, &PyZyre_t_Type, &self)) {
        return NULL;
    }
    self_ptr = (self ? self->obj : NULL);

    if (PyEval_ThreadsInitialized ())
         py_thread_state = PyEval_SaveThread();
    
    zlist_t * groups = zyre_own_groups(self_ptr);

    if (py_thread_state)
         PyEval_RestoreThread(py_thread_state);

    PyObject * set = zlist_of_str_to_pyset(groups);
    zlist_destroy(&groups);
    return set;
}
'''
_wrap_zyre_peer_groups = '''
PyObject *
_wrap_zyre_peer_groups(PyObject * PYBINDGEN_UNUSED(dummy), PyObject *args, PyObject *kwargs, PyObject **return_exception)
{
    PyThreadState *py_thread_state = NULL;
    PyZyre_t *self;
    zyre_t *self_ptr;
    const char *keywords[] = {"self", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, (char *) "O!", (char **) keywords, &PyZyre_t_Type, &self)) {
        return NULL;
    }
    self_ptr = (self ? self->obj : NULL);

    if (PyEval_ThreadsInitialized ())
         py_thread_state = PyEval_SaveThread();

    zlist_t * groups = zyre_peer_groups(self_ptr);

    if (py_thread_state)
         PyEval_RestoreThread(py_thread_state);

    PyObject * set = zlist_of_str_to_pyset(groups);
    Py_INCREF(set);
    zlist_destroy(&groups);
    return set;
}
'''
_wrap_zyre_peers_by_group = '''
PyObject *
_wrap_zyre_peers_by_group(PyObject * PYBINDGEN_UNUSED(dummy), PyObject *args, PyObject *kwargs, PyObject **return_exception)
{
    PyThreadState *py_thread_state = NULL;
    PyZyre_t *self;
    zyre_t *self_ptr;
    char * group;
    const char *keywords[] = {"self", "group", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, (char *) "O!s", (char **) keywords, &PyZyre_t_Type, &self, &group)) {
        return NULL;
    }
    self_ptr = (self ? self->obj : NULL);

    if (PyEval_ThreadsInitialized ())
         py_thread_state = PyEval_SaveThread();

    zlist_t * peers = zyre_peers_by_group(self_ptr, group);

    if (py_thread_state)
         PyEval_RestoreThread(py_thread_state);

    PyObject * set = zlist_of_str_to_pyset(peers);
    zlist_destroy(&peers);
    return set;
}
'''

_wrap_zpoller_new = '''
PyObject *
_wrap_zpoller_new(PyObject * PYBINDGEN_UNUSED(dummy), PyObject *args, PyObject *kwargs, PyObject **return_exception)
{
    PyObject *py_retval;
    zpoller_t *retval;
    PyZsock_t *reader;
    zsock_t *reader_ptr;
    const char *keywords[] = {"reader", NULL};
    PyZpoller_t *py_zpoller_t;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, (char *) "O!", (char **) keywords, &PyZsock_t_Type, &reader)) {
        return NULL;
    }
    reader_ptr = (reader ? reader->obj : NULL);
    retval = zpoller_new(reader_ptr, NULL);
    if (!(retval)) {
        Py_INCREF(Py_None);
        return Py_None;
    }
    Py_INCREF(reader);
    py_zpoller_t = PyObject_New(PyZpoller_t, &PyZpoller_t_Type);

    Py_INCREF(py_zpoller_t);
    py_zpoller_t->obj = retval;
    py_zpoller_t->flags = PYBINDGEN_WRAPPER_FLAG_NONE;
    py_retval = Py_BuildValue((char *) "N", py_zpoller_t);
    return py_retval;
}
'''

_wrap_zsys_interrupted = '''
PyObject *
_wrap_zsys_interrupted(PyObject * PYBINDGEN_UNUSED(dummy), PyObject *args, PyObject *kwargs, PyObject **return_exception)
{
    PyObject * retval = Py_BuildValue("i", zsys_interrupted);
    Py_INCREF(retval);
    return retval;
}
'''