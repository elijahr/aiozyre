
MSG_TEXT_PARTS = ('event', 'peer', 'name', 'group')
MSG_BIN_PART = 'blob'

class Msg:
    __slots__ = ('event', 'peer', 'name', 'group', 'blob')

    def __cinit__(
        self,
        *,
        event: str = None,
        peer: str = None,
        name: str = None,
        group: str = None,
        blob: bytes = None
    ):
        self.event = event or ''
        self.peer = peer or ''
        self.name = name or ''
        self.group = group or ''
        self.blob = blob or b''

    def __repr__(self):
        args = ['{}={}'.format(slot, repr(getattr(self, slot))) for slot in self.__slots__]
        return '{}({})'.format(self.__class__.__name__, ", ".join(args))

    def to_dict(self):
        return dict(
            event=self.event,
            peer=self.peer,
            name=self.name,
            group=self.group,
            blob=self.blob,
        )

