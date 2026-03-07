from __future__ import annotations

from pathlib import Path
from struct import pack, unpack
from types import TracebackType
from typing import Literal, Protocol, TypeAlias, cast

import lmdb

BytesLike: TypeAlias = bytes | bytearray | memoryview


class StoreTransaction(Protocol):
    def add(self, text: str) -> int: ...
    def get(self, key: int) -> str: ...


class KeyValueStoreManager:
    """
    Owns a single LMDB Environment and hands out cached per-DB KeyValueStore wrappers.

    Notes:
      - Not thread-safe (per your requirement).
      - The manager owns the env lifetime; stores are invalid after manager close().
    """

    def __init__(
        self,
        path_to_store: str | Path,
        max_dbs: int = 10,
        map_size: int = 1024 * 1024 * 1024,
    ):
        self._env: lmdb.Environment | None = None
        self._stores: dict[str, KeyValueStore] = {}

        store_path = Path(path_to_store)
        store_path.mkdir(parents=True, exist_ok=True)

        self._env = lmdb.open(
            str(store_path),
            max_dbs=max_dbs,
            map_size=map_size,
            subdir=True,
            lock=True,
        )

    def flush(self) -> None:
        """Flush environment buffers to disk (env.sync()). Safe to call multiple times."""
        env = self._env
        if env is None:
            return
        env.sync()

    def close(self, *, do_sync: bool = True) -> None:
        """
        Optionally flush and then close the LMDB environment.

        Safe to call multiple times.
        After this, any previously returned stores are invalid.
        """
        env = self._env
        if env is None:
            return

        try:
            if do_sync:
                env.sync()
        finally:
            env.close()
            self._env = None

            # Invalidate and drop cached wrappers
            for store in self._stores.values():
                store._invalidate()  # intentional internal call
            self._stores.clear()

    def _require_env(self) -> lmdb.Environment:
        env = self._env
        if env is None:
            raise RuntimeError("LMDB environment is not initialized or already closed")
        return env

    def store(self, db_name: str) -> KeyValueStore:
        """
        Return a cached KeyValueStore wrapper for the named DB, creating/opening it if needed.
        """
        existing = self._stores.get(db_name)
        if existing is not None:
            return existing
        if not db_name or not db_name.strip():
            raise ValueError("db_name must be a non-empty string")

        env = self._require_env()
        db_handle: lmdb._Database = env.open_db(db_name.encode("utf-8"), create=True)

        store = KeyValueStore(manager=self, db_name=db_name, db_handle=db_handle)
        self._stores[db_name] = store
        return store

    def delete_db(self, db_name: str) -> None:
        """
        Delete (drop) the named LMDB sub-database.

        Intended for unit tests / cleanup. Safe to call even if the DB doesn't exist.
        Any cached KeyValueStore wrapper for this db_name is removed and invalidated.
        """
        if not db_name or not db_name.strip():
            raise ValueError("db_name must be a non-empty string")

        env = self._require_env()

        # Remove cached wrapper (and invalidate it) if present
        cached = self._stores.pop(db_name, None)
        if cached is not None:
            cached._invalidate_db()  # intentional internal call

        try:
            with env.begin(write=True) as txn:
                db_handle: lmdb._Database = env.open_db(
                    db_name.encode("utf-8"),
                    txn=txn,
                    create=False,
                )
                # drop() takes the DB handle directly (no db= kwarg here)
                txn.drop(db_handle, delete=True)
        except lmdb.NotFoundError:
            # DB didn't exist — that's fine for cleanup.
            return

    def delete_all_dbs(self) -> None:
        """
        Delete (drop) *all* sub-databases in this environment (excluding the unnamed/main DB).

        Intended for unit tests / cleanup. Safe to call multiple times.
        Any cached KeyValueStore wrappers are invalidated and cleared.
        """
        env = self._require_env()

        # Invalidate and drop cached wrappers first (they'll be invalid once dropped anyway)
        for store in self._stores.values():
            store._invalidate_db()  # intentional internal call
        self._stores.clear()

        # Collect DB names from the unnamed/main DB (LMDB stores named DBs as keys there)
        with env.begin(write=False) as rtxn:
            with rtxn.cursor() as cursor:  # unnamed DB
                names: list[bytes] = [k for k, _v in cursor]

        if not names:
            return

        # Drop each named DB
        with env.begin(write=True) as wtxn:
            for name in names:
                try:
                    db_handle: lmdb._Database = env.open_db(name, txn=wtxn, create=False)
                    wtxn.drop(db_handle, delete=True)
                except lmdb.NotFoundError:
                    # Might have been dropped already; ignore for cleanup.
                    continue

    def __enter__(self) -> KeyValueStoreManager:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        self.close(do_sync=True)
        return False


class KeyValueStore:
    """
    Per-DB key/value wrapper (keys: unsigned 32-bit int; values: UTF-8 strings).

    The manager owns the LMDB Environment lifetime; this wrapper must not close it.
    """

    def _require_manager(self) -> KeyValueStoreManager:
        mgr = self._manager
        if mgr is None:
            raise RuntimeError("Store is invalid (its manager/environment has been closed)")
        return mgr

    def _require_env(self) -> lmdb.Environment:
        return self._require_manager()._require_env()

    def _require_db(self) -> lmdb._Database:
        db = self._db
        if db is None:
            raise RuntimeError("Store is invalid (database handle unavailable)")
        return db

    def _get_next_id(self) -> int:
        """
        Return the next key to use, computed as (largest existing key + 1),
        assuming unsigned int keys packed big-endian.
        """
        env = self._require_env()
        db = self._require_db()

        with env.begin(write=False) as txn:
            with txn.cursor(db=db) as cursor:  # explicit db=
                if cursor.last():
                    return self.unpack_int(cursor.key()) + 1
                return 0

    def __init__(
        self,
        manager: KeyValueStoreManager,
        db_name: str,
        db_handle: lmdb._Database,
    ):
        self._manager: KeyValueStoreManager | None = manager
        self._db_name: str = db_name
        self._db: lmdb._Database | None = db_handle

        # next id is per db
        self._next_id: int = self._get_next_id()

    def txn(self) -> KeyValueStoreTransaction:
        """
        Create a context-managed transaction wrapper for this store.

        The returned object must be used as a context manager:
            with store.txn() as t:
                ...
        """
        # Validate early so failures happen at txn() call site.
        self._require_env()
        self._require_db()
        return KeyValueStoreTransaction(self)

    def _add_in_txn(self, txn: lmdb.Transaction, *, db: lmdb._Database, text: str) -> int:
        """
        Adds a new key/value pair to this DB (no overwrite) using an existing transaction.

        This method is responsible for allocating the key and advancing _next_id.
        Gaps are allowed if the transaction later aborts (per requirement).
        """
        new_key = self._next_id

        key_bytes = self.pack_int(new_key)
        value_bytes = self.pack_str(text)

        ok: bool = txn.put(
            key_bytes,
            value_bytes,
            db=db,  # explicit db=
            overwrite=False,
        )
        if not ok:
            # Don't advance _next_id if we didn't actually store anything.
            raise KeyError(f"Key already exists: {new_key}")

        self._next_id += 1
        return new_key

    def _add_to_db(self, text: str) -> int:
        """
        Adds a new key/value pair to this DB (no overwrite) using a fresh write transaction.
        """
        env = self._require_env()
        db = self._require_db()

        with env.begin(write=True) as txn:
            return self._add_in_txn(txn, db=db, text=text)

    def add(self, text: str) -> int:
        """
        Add a new entry to this DB and return the assigned key.
        Note: not thread-safe (per requirement).
        """
        return self._add_to_db(text)

    def _get_in_txn(self, txn: lmdb.Transaction, *, db: lmdb._Database, key: int) -> str | None:
        key_bytes = self.pack_int(key)

        raw = txn.get(key_bytes, db=db)  # explicit db=
        if raw is None:
            return None

        return self.unpack_str(cast(BytesLike, raw))

    def _get_from_db(self, key: int) -> str:
        env = self._require_env()
        db = self._require_db()

        with env.begin(write=False) as txn:
            value: str | None = self._get_in_txn(txn, db=db, key=key)
            if value is None:
                raise KeyError(key)
            return value

    def get(self, key: int) -> str:
        return self._get_from_db(key)

    def _clear_db(self) -> None:
        """
        Clears (empties) this LMDB database.
        """
        env = self._require_env()
        db = self._require_db()

        with env.begin(write=True) as txn:
            # drop() takes the DB handle directly (no db= kwarg here)
            txn.drop(db, delete=False)

    def clear(self) -> None:
        """Clear this DB and reset next-id to 0."""
        self._clear_db()
        self._next_id = 0

    def _invalidate_db(self) -> None:
        """Called by the manager when the DB is dropped (manager may still be alive)."""
        self._db = None

    def _invalidate(self) -> None:
        """Called by the manager on close()."""
        self._manager = None
        self._db = None

    @classmethod
    def pack_int(cls, key: int) -> bytes:
        """
        Pack an int into 4 bytes suitable for use as an LMDB key.

        Uses unsigned 32-bit big-endian ('>I') so lexicographic byte order
        matches numeric order (0, 1, 2, ...).

        Valid range: 0 <= key <= 2**32 - 1
        """
        if not isinstance(key, int):
            raise TypeError(f"key must be int, got {type(key).__name__}")
        if key < 0:
            raise ValueError("key must be non-negative (unsigned)")
        if key > 0xFFFFFFFF:
            raise ValueError("key too large for unsigned 32-bit")

        return pack(">I", key)

    @classmethod
    def unpack_int(cls, key_bytes: BytesLike) -> int:
        """Reverse of pack_int(): convert a 4-byte LMDB key back into an int."""
        mv = memoryview(key_bytes)
        if mv.nbytes != 4:
            raise ValueError("packed key must be exactly 4 bytes")
        return int(unpack(">I", mv)[0])

    @classmethod
    def pack_str(cls, value: str) -> bytes:
        """Encode a Python str into bytes suitable for storing as an LMDB value."""
        if not isinstance(value, str):
            raise TypeError(f"value must be str, got {type(value).__name__}")
        return value.encode("utf-8")

    @classmethod
    def unpack_str(cls, value_bytes: BytesLike) -> str:
        """Decode bytes-like LMDB values into a UTF-8 string."""
        if isinstance(value_bytes, bytes | bytearray):
            return value_bytes.decode("utf-8")
        return value_bytes.tobytes().decode("utf-8")

    def __repr__(self) -> str:
        return f"KeyValueStore(db_name={self._db_name!r}, valid={self._db is not None})"


class KeyValueStoreTransaction(StoreTransaction):
    """
    Context-managed transaction wrapper bound to a single KeyValueStore.

    Owns an LMDB write transaction. Commits on normal exit; aborts on exception.
    """

    def __init__(self, parent: KeyValueStore):
        self._parent: KeyValueStore = parent
        self._txn: lmdb.Transaction | None = None

    def _require_txn(self) -> lmdb.Transaction:
        txn = self._txn
        if txn is None:
            raise RuntimeError("Transaction is not active (use within a 'with' block)")
        return txn

    def add(self, text: str) -> int:
        txn = self._require_txn()
        db = self._parent._require_db()
        return self._parent._add_in_txn(txn, db=db, text=text)

    def get(self, key: int) -> str:
        txn = self._require_txn()
        db = self._parent._require_db()
        value: str | None = self._parent._get_in_txn(txn, db=db, key=key)
        if value is None:
            raise KeyError(key)
        return value

    def __enter__(self) -> KeyValueStoreTransaction:
        env = self._parent._require_env()
        # Prefer db= explicitly on operations, not on begin().
        self._txn = env.begin(write=True)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        txn = self._require_txn()
        try:
            if exc_type is None:
                txn.commit()
            else:
                txn.abort()
        finally:
            self._txn = None
        return False
