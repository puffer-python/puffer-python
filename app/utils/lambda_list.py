from functools import reduce


class LambdaList:
    def __init__(self, _list):
        self._list = list(_list)

    def filter(self, filter_func):
        self._list = list(filter(filter_func, self._list))
        return self

    def map(self, map_func):
        self._list = list(map(map_func, self._list))
        return self

    def reduce(self, reduce_func):
        return reduce(reduce_func, self._list)

    def first(self):
        return self._list[0] if self._list else None

    def take(self, count):
        self._list = self._list[:count]
        return self

    def skip(self, count):
        self._list = self._list[count:]
        return self

    def list(self):
        return list(self._list)

    def find(self, find_func):
        return self.filter(find_func).first()

    def find_all(self, find_func):
        return self.filter(find_func).list()

    def any(self):
        return any(self._list)

    def sum(self, map_func=None):
        if not self.any():
            return 0
        if map_func is None:
            return self.reduce(lambda x, y: x + y)
        else:
            return self.map(map_func).reduce(lambda x, y: x + y)

    def sort(self, key_func=None, reverse=False):
        self._list = list(sorted(self._list, key=key_func, reverse=reverse))
        return self

    def string_join(self, separator):
        return separator.join(self.map(lambda x: str(x)).list())

