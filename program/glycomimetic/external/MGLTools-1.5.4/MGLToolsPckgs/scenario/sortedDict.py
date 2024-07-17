class SortedDict(dict):
    """Dictionary that sorts the keys
"""
    def __init__(self):
        dict.__init__(self)
        self._sortedKeys = dict.keys(self) # list of sorted keys
        self._sortedKeys.sort()

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._sortedKeys.remove(key)

    def __setitem__(self, key, item):
        dict.__setitem__(self, key, item)
        if key not in self._sortedKeys:
            self._sortedKeys.append(key)
            self._sortedKeys.sort()

    def clear(self):
        dict.clear(self)
        self._sortedKeys = []

    def copy(self):
        dictionary = dict.copy(self)
        dictionary._sortedKeys = self._sortedKeys[:]
        return dictionary

    def items(self):
        return zip(self._sortedKeys, self.values())

    def keys(self):
        return self._sortedKeys

    def values(self):
        return map(self.get, self._sortedKeys)

    def popitem(self):
        try:
            key = self._sortedKeys[-1]
        except IndexError:
            raise KeyError('dictionary is empty')

        val = self[key]
        del self[key]

        return (key, val)

    def pop(self, key):
        try:
            val = self[key]
        except IndexError:
            raise KeyError( str(key))
        del self[key]

        return val

    def setdefault(self, key, failobj = None):
        dict.setdefault(self, key, failobj)
        if key not in self._sortedKeys: self._sortedKeys.append(key)

    def update(self, dictionary):
        dict.update(self, dictionary)
        self._sortedKeys = dict.keys(self)
        self._sortedKeys.sort()

    def index(self, i):
        return self.get(self._sortedKeys[i])
    
if __name__=='__main__':
    d = {20000:'b', 1000:'a', 4000000:'d', 300000:'e'}
    print d.items()
    sd = SortedDict()
    sd.update(d)
    print sd.items()
    sd[1500] = 'ab'
    print sd.items()
