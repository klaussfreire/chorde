from chorde.serialize import serialize

import logging
import time
import weakref

# No need for real multiprocessing. In fact, using real
# multiprocessing would force pickling of values, which would be
# undesirable, pushing pickling cost into foreground threads.
from multiprocessing.pool import ThreadPool
from threading import Event

from .base import BaseCacheClient, CacheMissError, NONE


class _NONE:pass
class _DELETE:pass
class _PURGE:pass
class _CLEAR:pass

class Defer(object):
    """
    Wrap a callable in this, and pass it as a value to an AsyncWriteCacheClient,
    and the evaluation of the given callable will happen asynchronously. The cache
    will return stale entries until the callable is finished computing a new value.
    """
    
    def __init__(self, callable_, *args, **kwargs):
        self.callable_ = callable_
        self.args = args
        self.kwargs = kwargs

    def undefer(self):
        return self.callable_(*self.args, **self.kwargs)

class AsyncCacheWriterPool(ThreadPool):
    def __init__(self, size, workers, client):
        self.client = client
        self.logger = logging.getLogger("AsyncCache")
        self.size = size
        self.workers = workers
        
        # queueset holds the values to be written, associated
        # by key, providing some write-back coalescense in
        # high-load environments
        self.queueset = {}
        self.done_event = Event()
        
        ThreadPool.__init__(self, workers)

    def _wait_done(self, timeout=None):
        ev = self.done_event
        if timeout is not None:
            ev.wait(timeout)
            if ev.isSet():
                ev.clear()
        else:
            ev.wait()
            ev.clear()

    @staticmethod
    def _writer(self, key):
        # self is weakref
        self = self()
        if self is None:
            return

        ev = self.done_event
        value, ttl = self.dequeue(key)

        try:
            if value is _NONE:
                # Something's hinky
                return
            elif isinstance(value, Defer):
                try:
                    value = value.undefer()
                except:
                    self.logger.error("Error in background cache refresh", exc_info=True)
            
            elif value is _DELETE:
                try:
                    self.client.delete(key)
                except:
                    self.logger.error("Error deleting key", exc_info=True)
            
            elif value is _CLEAR:
                try:
                    self.client.clear()
                except:
                    self.logger.error("Error clearing cache", exc_info = True)
            
            elif value is _PURGE:
                try:
                    self.client.purge()
                except:
                    self.logger.error("Error purging cache", exc_info = True)
            
            else:
                try:
                    self.client.put(key, value, ttl)
                except:
                    self.logger.error("Error saving data in cache", exc_info=True)
        finally:
            # Signal waiting threads
            ev.set()
        
    @serialize
    def dequeue(self, key):
        return self.queueset.pop(key, _NONE)

    def enqueue(self, key, value, ttl=None):
        while len(self.queueset) >= self.size:
            self._wait_done(1.0)
        self._enqueue(key, value, ttl)

    @serialize
    def clearqueue(self):
        self.queueset.clear()
    
    @serialize
    def _enqueue(self, key, value, ttl):
        if key not in self.queueset:
            self.queueset[key] = value, ttl
            self.apply_async(self._writer, (weakref.ref(self), key))
        else:
            self.queueset[key] = value, ttl
    
    def waitkey(self, key, timeout=None):
        if timeout is None:
            while key in self.queueset:
                self._wait_done(1.0)
        else:
            tfin = time.time() + timeout
            while key in self.queueset and tfin >= time.time():
                self._wait_done(max(1.0, timeout))
                timeout = tfin - time.time()
    
    def getTtl(self, key, default = None):
        return self.queueset.get(key, default)
    
    def contains(self, key):
        return key in self.queueset

    def put(self, key, value, ttl):
        self.enqueue(key, value, ttl)

    def delete(self, key):
        self.enqueue(key, _DELETE)

    def clear(self):
        self.clearqueue()
        self.enqueue(_CLEAR, _CLEAR)

    def purge(self):
        self.enqueue(_PURGE, _PURGE)
    
class AsyncWriteCacheClient(BaseCacheClient):
    def __init__(self, client, writer_queue_size, writer_workers):
        self.client = client
        self.writer_queue_size = writer_queue_size
        self.writer_workers = writer_workers
        self.writer = None
        
    def assert_started(self):
        if self.writer is None:
            self.writer = AsyncCacheWriterPool(
                self.writer_queue_size, 
                self.writer_workers,
                self.client)
    
    def is_started(self):
        return self.writer is not None
    
    def start(self):
        if self.writer is not None:
            raise AssertionError, "Starting AsyncCacheClient twice"
        self.assert_started()
    
    def stop(self, abort_tasks=False):
        if self.writer is not None:
            if not abort_tasks:
                self.writer.join()
            self.writer.terminate()
    
    @property
    def async(self):
        return True
    
    def put(self, key, value, ttl):
        self.assert_started()
        self.writer.put(key, value, ttl)
    
    def delete(self, key):
        self.assert_started()
        self.writer.delete(key)

    def clear(self):
        if self.is_started():
            self.writer.clear()

    def purge(self):
        if self.is_started():
            self.writer.purge()
    
    def getTtl(self, key, default = NONE):
        if self.is_started():
            # Try to read pending writes as if they were on the cache
            value = self.writer.getTtl(key, _NONE)
            if value is not _NONE:
                value, ttl = value
                if not isinstance(value, Defer):
                    return value, ttl
            # Yep, _NONE when querying the writer, because we don't want
            # to return a default if the writer doesn't have it, we must
            # still check the client.
        
        # Ok, read the cache then
        value, ttl = self.client.getTtl(key, default)
        if value is NONE:
            raise CacheMissError, key
        else:
            return value, ttl
    
    def contains(self, key):
        if self.is_started():
            if self.writer.contains(key):
                return True
            else:
                return self.client.contains(key)
        else:
            return self.client.contains(key)
