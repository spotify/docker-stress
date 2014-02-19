from time import time, sleep


class TimeoutError(Exception):
    pass


class PreconditionError(Exception):
    pass


def await(name, f, timeout=300, interval=1, precondition=None):
    deadline = time() + timeout
    while time() < deadline:
        if precondition and not precondition():
            raise PreconditionError(name)
        value = f()
        if value:
            return value
        sleep(interval)
    raise TimeoutError(name)
