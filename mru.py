import pickle
import hashlib


class MRUCache:
    null = object()
    hits = 0
    misses = 0

    def __init__(self, size):
        self.size = size
        self._data = []
        self._last_used_index = None

    def set(self, key, value):
        data = (key, value)
        if self._last_used_index is not None:
            self._data[self._last_used_index] = data
        else:
            self._data.append(data)

            if len(self._data) == self.size:
                self._last_used_index = len(self._data) - 1

    def get(self, key):
        for index, cached in enumerate(self._data):
            if key == cached[0]:
                if self._last_used_index is not None:
                    self._last_used_index = index
                self.hits += 1
                return cached[1]
        self.misses += 1
        return self.null


class MRUCacheOptimized(MRUCache):
    fast_hits = 0

    def __init__(self, size):
        super().__init__(size)
        self._saved_keys = {}

    @staticmethod
    def _hash_key(raw_key):
        return hashlib.sha256(pickle.dumps(raw_key)).digest()

    def _remove_saved_key(self, raw_key):
        try:
            hashed_key = self._hash_key(raw_key=raw_key)
            del self._saved_keys[hashed_key]
        except Exception:
            pass

    def _save_key(self, raw_key):
        try:
            hashed_key = self._hash_key(raw_key=raw_key)
            index = self._last_used_index if self._last_used_index else len(self._data) - 1
            self._saved_keys[hashed_key] = index
        except Exception:
            pass

    def set(self, key, value):
        data = (key, value)
        if self._last_used_index is not None:
            self._remove_saved_key(self._data[self._last_used_index][0])
            self._data[self._last_used_index] = data
        else:
            self._data.append(data)
            if len(self._data) == self.size:
                self._last_used_index = len(self._data) - 1

        self._save_key(raw_key=key)

    def get_fast(self, key):
        try:
            hashed_key = self._hash_key(raw_key=key)
            index = self._saved_keys.get(hashed_key)
            if index is not None:
                k, v = self._data[index]
                if k == key:
                    if self._last_used_index is not None:
                        self._last_used_index = index
                    self.hits += 1
                    self.fast_hits += 1
                    return v
        except Exception:
            pass
        return self.null

    def get(self, key):
        fast_result = self.get_fast(key)
        return fast_result if fast_result is not self.null else super().get(key)


def _mru_cache(func, size, optimization):
    def wrapper(*args, **kwargs):
        key = (args, kwargs)
        result = wrapper.cache.get(key=key)
        if result is wrapper.cache.null:
            result = func(*args, **kwargs)
            wrapper.cache.set(key=key, value=result)
        return result
    wrapper.cache = MRUCacheOptimized(size=size) if optimization else MRUCache(size=size)
    return wrapper


def mru_cache(size=10, optimization=False):
    if callable(size):
        return _mru_cache(func=size, size=10, optimization=optimization)

    if not isinstance(size, int) or size <= 0:
        def wrapper(func):
            return func
        return wrapper

    def wrapper(func):
        return _mru_cache(func=func, size=size, optimization=optimization)
    return wrapper
