# services/mock_db.py
# In-memory key-value store — drop-in replacement for Postgres db.py
# Same interface: get(), save(), list_keys()

_store: dict = {}


def save(collection: str, key: str, value):
    if collection not in _store:
        _store[collection] = {}
    _store[collection][key] = value


def get(collection: str, key: str):
    return _store.get(collection, {}).get(key)


def list_keys(collection: str):
    return list(_store.get(collection, {}).keys())


def clear(collection: str = None):
    if collection:
        _store.pop(collection, None)
    else:
        _store.clear()
