import logging

log = logging.getLogger(__name__)

from time import time
from threading import RLock


# Adapted from http://code.activestate.com/recipes/511490/
class TokenBucket(object):
    """An implementation of the token bucket algorithm.

    >>> bucket = TokenBucket(80, 0.5)
    >>> print bucket.consume(10)
    True
    >>> print bucket.consume(90)
    False
    """
    def __init__(self, tokens, fill_rate):
        """tokens is the total tokens in the bucket. fill_rate is the
        rate in tokens/second that the bucket will be refilled."""
        self.capacity = float(tokens)
        self._tokens = float(tokens)
        self.fill_rate = float(fill_rate)
        self.timestamp = time()
        self.lock = RLock()

    def consume(self, tokens):
        """Consume tokens from the bucket. Returns True if there were
        sufficient tokens otherwise False."""
        with self.lock:
            if tokens <= self.tokens:
                self._tokens -= tokens
            else:
                return False
            return True

    def get_tokens(self):
        with self.lock:
            if self._tokens < self.capacity:
                now = time()
                delta = self.fill_rate * (now - self.timestamp)
                self._tokens = min(self.capacity, self._tokens + delta)
                self.timestamp = now
            return self._tokens

    tokens = property(get_tokens)


def rate_limited(name, tokens, fill_rate):

    def decorate(func):
        token_bucket = TokenBucket(tokens, fill_rate)

        def trampoline(*args, **kargs):
            token = token_bucket.consume(1)
            if not token:
                log.warning('rate limited: %s', name)
                return
            return func(*args, **kargs)
        return trampoline
    return decorate


if __name__ == '__main__':
    from time import sleep

    logging.basicConfig(format='%(asctime)s %(levelname)-7s %(message)s',
                        level=logging.INFO)

    @rate_limited('foobar', 2, 0.5)
    def foobar():
        print 'foobar!'

    for i in xrange(100):
        foobar()
        sleep(0.1)

    bucket = TokenBucket(10, 0.05)
    print "tokens =", bucket.tokens
    print "consume(1) =", bucket.consume(1)
    print "consume(1) =", bucket.consume(1)
    sleep(1)
    print "tokens =", bucket.tokens
    sleep(1)
    print "tokens =", bucket.tokens
    print "consume(1) =", bucket.consume(1)
    print "tokens =", bucket.tokens
    for i in xrange(20):
        print "consume(1) =", bucket.consume(1)
        print "tokens =", bucket.tokens
        sleep(1)
