

class _CollectionDeclarer(object):
    connection = None

    def __init__(self, _db, _col):
        if self.connection is None:
            from torext.errors import ConnectionError
            raise ConnectionError("""
                MongoDB connection is None in CollectionDeclarer,
                it may happen when your settings.py file is incorrect,
                or you involve the project in an outer place without properly configuration.
                """)
        self._db = _db
        self._col = _col
        # self.col = None
        # self._fetch_col()
        self.col = self.connection[self._db][self._col]

    # def _fetch_col(self):
    #     if self.col is None:

    def __get__(self, ins, owner):
        # if self.col is None:
        #     self.col = self.connection[self._db][self._col]
        return self.col
