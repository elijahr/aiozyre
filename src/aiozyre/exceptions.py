class AIOZyreError(Exception):
    pass


class Timeout(AIOZyreError):
    pass


class NodeStartError(AIOZyreError):
    pass


class NodeRecvError(AIOZyreError):
    pass


class Stopped(AIOZyreError):
    pass
