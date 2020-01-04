
class Msg:
    __slots__ = ('event', 'peer', 'name', 'headers', 'address', 'group', 'blob')

    def __init__(
        self,
        *,
        event: str = None,
        peer: str = None,
        name: str = None,
        headers: str = None,
        address: str = None,
        group: str = None,
        blob: bytes = None
    ):
        self.event = event or ''
        self.peer = peer or ''
        self.name = name or ''
        self.headers = headers or ''
        self.address = address or ''
        self.group = group or ''
        self.blob = blob or b''

    def __repr__(self):
        args = ['{}={}'.format(slot, repr(getattr(self, slot))) for slot in self.__slots__]
        return '{}({})'.format(self.__class__.__name__, ", ".join(args))

    @property
    def string(self):
        return self.blob.decode('utf8') if self.blob is not None else None

    def to_dict(self):
        return dict(
            event=self.event,
            peer=self.peer,
            name=self.name,
            headers=self.headers,
            address=self.address,
            group=self.group,
            blob=self.blob,
        )