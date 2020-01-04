
import asyncio


_SHOUT = 0
_WHISPER = 1
_JOIN = 2
_LEAVE = 3
_PEERS = 4
_PEERS_BY_GROUP = 5
_OWN_GROUPS = 6
_PEER_GROUPS = 7
_PEER_ADDRESS = 8
_PEER_HEADER_VALUE = 9


class ThreadSafeFuture:
    _asyncio_future_blocking = True

    def __init__(self, *, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self.future = self._loop.create_future()

    def result(self):
        """
        Return the result this future represents.

        If the future has been cancelled, raises CancelledError.  If the
        future's result isn't yet available, raises InvalidStateError.  If
        the future is done and has an exception set, this exception is raised.
        """
        return self.future.result()

    def set_result(self, result):
        """
        Set the future result.

        This method can be called from any thread but is not guaranteed to set the result immediately.
        """
        self._loop.call_soon_threadsafe(self.future.set_result, result)

    def cancel(self, *args, **kwargs):
        """
        Cancel the future and schedule callbacks.

        If the future is already done or cancelled, return False.  Otherwise,
        change the future's state to cancelled, schedule the callbacks and
        return True.

        This method can be called from any thread but is not guaranteed to cancel the future immediately.
        """
        self._loop.call_soon_threadsafe(self.future.cancel)

    def cancelled(self):
        """ Return True if the future was cancelled. """
        return self.future.cancelled()

    def done(self):
        """
        Return True if the future is done.

        Done means either that a result / exception are available, or that the
        future was cancelled.
        """
        return self.future.done()

    def exception(self):
        """
        Return the exception that was set on this future.

        The exception (or None if no exception was set) is returned only if
        the future is done.  If the future has been cancelled, raises
        CancelledError.  If the future isn't done yet, raises
        InvalidStateError.
        """
        return self.future.exception()

    def get_loop(self):
        """ Return the event loop the Future is bound to. """
        return self.future.get_loop()

    def add_done_callback(self, callback):
        """
        Add a callback to be run when the future becomes done.

        The callback is called with a single argument - the future object. If
        the future is already done when this is called, the callback is
        scheduled with call_soon.

        This method can be called from any thread but is not guaranteed to add the callback immediately.
        """
        self._loop.call_soon_threadsafe(self.future.add_done_callback, callback)

    def remove_done_callback(self, callback):
        """
        Remove all instances of a callback from the "call when done" list.

        Returns the number of callbacks removed.

        This method can be called from any thread but is not guaranteed to remove the callback immediately.
        """
        self._loop.call_soon_threadsafe(self.future.remove_done_callback, callback)

    def set_exception(self, exception):
        """
        Mark the future done and set an exception.

        If the future is already done when this method is called, raises
        InvalidStateError.

        This method can be called from any thread but is not guaranteed to set the exception immediately.
        """
        self._loop.call_soon_threadsafe(self.future.set_exception, exception)

    def __await__(self):
        return self.future.__await__()

    def __del__(self):
        return self.future.__del__()

    def __iter__(self):
        return self.future.__iter__()


class StartedFuture(ThreadSafeFuture):
    pass


class SignalFuture(ThreadSafeFuture):
    pass


class ShoutFuture(SignalFuture):
    signal = _SHOUT

    def __init__(self, *, group: str, blob: bytes, **kwargs):
        self.group = group.encode('utf8')
        self.blob = blob
        super().__init__(**kwargs)


class WhisperFuture(SignalFuture):
    signal = _WHISPER

    def __init__(self, *, peer: str, blob: bytes, **kwargs):
        self.peer = peer.encode('utf8')
        self.blob = blob
        super().__init__(**kwargs)


class JoinFuture(SignalFuture):
    signal = _JOIN

    def __init__(self, *, group: str, **kwargs):
        self.group = group.encode('utf8')
        super().__init__(**kwargs)


class LeaveFuture(SignalFuture):
    signal = _LEAVE

    def __init__(self, *, group: str, **kwargs):
        self.group = group.encode('utf8')
        super().__init__(**kwargs)


class PeersFuture(SignalFuture):
    signal = _PEERS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class PeersByGroupFuture(SignalFuture):
    signal = _PEERS_BY_GROUP

    def __init__(self, *, group: str, **kwargs):
        self.group = group.encode('utf8')
        super().__init__(**kwargs)


class OwnGroupsFuture(SignalFuture):
    signal = _OWN_GROUPS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class PeerGroupsFuture(SignalFuture):
    signal = _PEER_GROUPS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class PeerHeaderValueFuture(SignalFuture):
    signal = _PEER_HEADER_VALUE

    def __init__(self, *, peer: str, header: str, **kwargs):
        self.peer = peer.encode('utf8')
        self.header = header.encode('utf8')
        super().__init__(**kwargs)

