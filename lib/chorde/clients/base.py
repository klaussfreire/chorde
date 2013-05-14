# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod, abstractproperty
from chorde.serialize import serialize_read, serialize_write

# Overridden by inproc_cache based on LRUCache availability
CacheMissError = KeyError

class NONE: pass

class BaseCacheClient(object):
    """
    Interface of all backing stores.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def async(self):
        return False
    
    @abstractmethod
    def put(self, key, value, ttl):
        raise NotImplementedError

    @abstractmethod
    def delete(self, key):
        raise NotImplementedError

    @abstractmethod
    def getTtl(self, key, default = NONE):
        """
        Returns: a tuple (value, ttl). If a default is given and the value
            is not in cache, return (default, -1). If a default is not given
            and the value is not in cache, raises CacheMissError. If the value
            is in the cache, but stale, ttl will be < 0, and value will be
            other than NONE. Note that ttl=0 is a valid and non-stale result.
        """
        if default is NONE:
            raise CacheMissError, key
        else:
            return (default, -1)
    
    def get(self, key, default = NONE):
        rv, ttl = self.getTtl(key, default)
        if ttl < 0 and default is NONE:
            raise CacheMissError, key
        else:
            return rv

    @abstractmethod
    def clear(self):
        raise NotImplementedError

    @abstractmethod
    def purge(self, timeout = 0):
        """
        Params
            
            timeout: if specified, only items that have been stale for
                this amount of time will be removed. That is, it is added to the
                initial entry's TTL vale.
        """
        raise NotImplementedError

    @abstractmethod
    def contains(self, key, ttl = None):
        """
        Verifies that a key is valid within the cache

        Params

            key: the key to check

            ttl: If provided and not None, a TTL margin. Keys with this or less
                time to live will be considered as stale. Provide if you want
                to check about-to-expire keys.
        """
        return False

class ReadWriteSyncAdapter(BaseCacheClient):
    def __init__(self, client):
        self.client = client

    @property
    def async(self):
        return self.client.async

    @serialize_write
    def put(self, key, value, ttl):
        return self.client.put(key, value, ttl)

    @serialize_write
    def delete(self, key):
        return self.client.delete(key)

    @serialize_read
    def getTtl(self, key, default = NONE):
        return self.client.getTtl(key, default)

    @serialize_write
    def clear(self):
        return self.client.clear()

    @serialize_write
    def purge(self, timeout = 0):
        return self.client.purge(timeout)

    @serialize_read
    def contains(self, key, ttl = None):
        return self.client.contains(key, ttl)


class DecoratedWrapper(BaseCacheClient):
    """
    A namespace wrapper client will decorate keys with a namespace, making it possible
    to share one client among many sub-clients without key collisions.
    """
    def __init__(self, client, key_decorator = None, value_decorator = None, value_undecorator = None):
        self.client = client
        self.key_decorator = key_decorator
        self.value_decorator = value_decorator
        self.value_undecorator = value_undecorator

    @property
    def async(self):
        return self.client.async

    def put(self, key, value, ttl):
        if self.key_decorator:
            key = self.key_decorator(key)
        if self.value_decorator:
            value = self.value_decorator(value)
        return self.client.put(key, value, ttl)

    def delete(self, key):
        if self.key_decorator:
            key = self.key_decorator(key)
        return self.client.delete(key)

    def getTtl(self, key, default = NONE):
        if self.key_decorator:
            key = self.key_decorator(key)
        rv = self.client.getTtl(key, default)
        if rv is not default and self.value_undecorator:
            rv = self.value_undecorator(rv)
        return rv

    def clear(self):
        return self.client.clear()

    def purge(self, timeout = 0):
        return self.client.purge(timeout)

    def contains(self, key, ttl = None):
        if self.key_decorator:
            key = self.key_decorator(key)
        return self.client.contains(key, ttl)

class NamespaceWrapper(DecoratedWrapper):
    """
    A namespace wrapper client will decorate keys with a namespace, making it possible
    to share one client among many sub-clients without key collisions.
    """
    def __init__(self, namespace, client):
        # super init not called on purpose, it would mess key_decorator
        super(NamespaceWrapper, self).__init__(client)
        self.namespace = namespace
        self.revision = client.get((namespace,'REVMARK'), 0)

    @property
    def key_decorator(self):
        return self._key_decorator

    @key_decorator.setter
    def key_decorator(self, value):
        pass

    def _key_decorator(self, key):
        return (self.namespace, self.revision, key)

    def clear(self):
        # Cannot clear a shared client, so, instead, switch revisions
        self.revision += 1
        self.client.put((self.namespace, 'REVMARK'), self.revision)
        return self.client.clear()

