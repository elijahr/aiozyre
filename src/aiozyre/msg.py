from .xzyre import zmsg_popstr, zmsg_pushstr, zmsg_popbytes, zmsg_pushbytes, zmsg_new


class Msg:
    __slots__ = ('event', 'peer', 'name', 'group', 'message')

    def __init__(self, *, event: str, peer: str, name: str, group: str, message: bytes):
        self.event = event
        self.peer = peer
        self.name = name
        self.group = group
        self.message = message

    def __repr__(self):
        args = [f'{slot}={repr(getattr(self, slot))}' for slot in self.__slots__]
        return f'{self.__class__.__name__}({", ".join(args)})'

    @classmethod
    def from_zmsg(cls, zmsg):
        return cls(
            event=zmsg_popstr(zmsg),
            peer=zmsg_popstr(zmsg),
            name=zmsg_popstr(zmsg),
            group=zmsg_popstr(zmsg),
            message=zmsg_popbytes(zmsg),
        )

    def to_zmsg(self):
        zmsg = zmsg_new()
        zmsg_pushstr(zmsg, self.event)
        zmsg_pushstr(zmsg, self.peer)
        zmsg_pushstr(zmsg, self.name)
        zmsg_pushstr(zmsg, self.group)
        zmsg_pushbytes(zmsg, self.message)
        return zmsg

    def to_dict(self):
        return dict(
            event=self.event,
            peer=self.peer,
            name=self.name,
            group=self.group,
            message=self.message,
        )
