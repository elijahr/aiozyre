
class AIOZyreError(Exception):
    pass


class StartFailed(AIOZyreError):
    pass


class StopFailed(AIOZyreError):
    pass


class Stopped(AIOZyreError):
    pass
