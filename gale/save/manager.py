"""
SaveManager: a general-purpose save-game system. It only ever moves
whatever JSON-serializable dict a game gives it in and out of named
"slots" on disk -- what that dict contains (a player's position, an
inventory, a whole world) is entirely up to the game, so the same
class works for any of them.

Everything a specific game is likely to need to customize is a
constructor parameter, each with a sensible default resolved from
gale.conf.settings: where saves live (save_dir), what a save file is
named (file_extension), the wire format (serializer/deserializer,
following the same pluggable-function pattern gale.net.Server/Client
already use), and a schema version + migrations for evolving what a
save contains across releases without breaking old saves.

Author: Alejandro Mujica (aledrums@gmail.com)
"""

import os
import pathlib
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from gale.conf import settings

from .serialization import Deserializer, Serializer, json_deserialize, json_serialize

Migration = Callable[[Dict[str, Any]], Dict[str, Any]]


class SaveError(Exception):
    """
    Raised for anything that keeps a save from being read back:
    a missing slot, a corrupted file, or a stored version newer than
    the manager's own, or one with no registered migration path up to it.
    """


@dataclass(frozen=True)
class SaveMetadata:
    """
    What a save-select screen needs to know about a slot without
    loading (and migrating) its full data.

    :param slot: The slot's name.
    :param version: The schema version the save is stored at, before migration.
    :param created_at: ``time.time()`` when the slot was first saved.
    :param updated_at: ``time.time()`` of the most recent save to this slot.
    :param extra: Whatever game-specific metadata was passed to ``save()``
        (e.g. a chapter name, play time, a thumbnail path) -- SaveManager
        never looks inside this, it's purely for the game's own use.
    """

    slot: str
    version: int
    created_at: float
    updated_at: float
    extra: Dict[str, Any] = field(default_factory=dict)


class SaveManager:
    """
    Usage example:

        manager = SaveManager()
        manager.save("slot1", {"level": 3, "hp": 80}, play_time=120.5)
        data = manager.load("slot1")   # {"level": 3, "hp": 80}

        for save in manager.list_saves():
            print(save.slot, save.extra.get("play_time"))
    """

    def __init__(
        self,
        save_dir: Optional[Union[str, pathlib.Path]] = None,
        version: Optional[int] = None,
        file_extension: Optional[str] = None,
        serializer: Serializer = json_serialize,
        deserializer: Deserializer = json_deserialize,
        migrations: Optional[Dict[int, Migration]] = None,
    ) -> None:
        self.save_dir = pathlib.Path(
            save_dir if save_dir is not None else settings.SAVE_DIR
        )
        self.version = version if version is not None else settings.SAVE_VERSION
        self.file_extension = (
            file_extension
            if file_extension is not None
            else settings.SAVE_FILE_EXTENSION
        )
        self.serializer = serializer
        self.deserializer = deserializer
        self.migrations: Dict[int, Migration] = dict(migrations) if migrations else {}

        self.save_dir.mkdir(parents=True, exist_ok=True)

    def _validate_slot(self, slot: str) -> None:
        if not slot or os.path.basename(slot) != slot:
            raise SaveError(
                f"Invalid slot name {slot!r}: it must be a plain name, "
                "not a path (no separators, no '..')."
            )

    def _path(self, slot: str) -> pathlib.Path:
        self._validate_slot(slot)
        return self.save_dir / f"{slot}.{self.file_extension}"

    def _read_envelope(self, slot: str) -> Dict[str, Any]:
        path = self._path(slot)

        if not path.exists():
            raise SaveError(f"No save found in slot {slot!r}.")

        try:
            return self.deserializer(path.read_bytes())
        except ValueError as error:
            raise SaveError(f"Save {slot!r} is corrupted: {error}") from error

    def exists(self, slot: str) -> bool:
        """
        :param slot: The slot's name.
        :returns: Whether a save exists in slot.
        """
        return self._path(slot).exists()

    def save(self, slot: str, data: Dict[str, Any], **metadata: Any) -> None:
        """
        Writes data to slot, tagged with the manager's current
        version and any metadata. Written atomically (via a temporary
        file renamed into place) so a crash mid-write can never leave
        a corrupted save behind.

        :param slot: The slot's name.
        :param data: A JSON-serializable dict with whatever the game
            wants to persist.
        :param metadata: Arbitrary game-specific extras (play time, a
            thumbnail path, a chapter name, ...), later available
            through list_saves()/read_metadata() without loading data.
        """
        path = self._path(slot)
        now = time.time()
        created_at = now

        if path.exists():
            try:
                created_at = self._read_envelope(slot).get("created_at", now)
            except SaveError:
                pass

        envelope = {
            "version": self.version,
            "created_at": created_at,
            "updated_at": now,
            "metadata": metadata,
            "data": data,
        }

        payload = self.serializer(envelope)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_bytes(payload)
        os.replace(tmp_path, path)

    def load(self, slot: str) -> Dict[str, Any]:
        """
        :param slot: The slot's name.
        :returns: The slot's data dict, migrated up to the manager's
            current version if it was stored at an older one.
        :raises SaveError: If the slot doesn't exist, is corrupted, is
            stored at a version newer than the manager's own, or is
            missing a migration needed to reach it.
        """
        envelope = self._read_envelope(slot)
        stored_version = envelope.get("version", 1)
        data = envelope.get("data", {})

        if stored_version > self.version:
            raise SaveError(
                f"Save {slot!r} is at version {stored_version}, newer than "
                f"this SaveManager's version {self.version}."
            )

        for from_version in range(stored_version, self.version):
            migration = self.migrations.get(from_version)

            if migration is None:
                raise SaveError(
                    f"Save {slot!r} is at version {stored_version} but no "
                    f"migration from version {from_version} to "
                    f"{from_version + 1} was registered."
                )

            data = migration(data)

        return data

    def read_metadata(self, slot: str) -> SaveMetadata:
        """
        :param slot: The slot's name.
        :returns: The slot's SaveMetadata, without loading (or migrating) its data.
        :raises SaveError: If the slot doesn't exist or is corrupted.
        """
        envelope = self._read_envelope(slot)
        return SaveMetadata(
            slot=slot,
            version=envelope.get("version", 1),
            created_at=envelope.get("created_at", 0.0),
            updated_at=envelope.get("updated_at", 0.0),
            extra=envelope.get("metadata", {}),
        )

    def list_saves(self) -> List[SaveMetadata]:
        """
        :returns: Every existing slot's SaveMetadata, most recently
            updated first. A slot that fails to read (corrupted) is
            skipped rather than raising.
        """
        saves = []

        for path in self.save_dir.glob(f"*.{self.file_extension}"):
            try:
                saves.append(self.read_metadata(path.stem))
            except SaveError:
                continue

        saves.sort(key=lambda save: save.updated_at, reverse=True)
        return saves

    def delete(self, slot: str) -> None:
        """
        :param slot: The slot's name. Deleting a slot that doesn't
            exist is a no-op.
        """
        path = self._path(slot)

        if path.exists():
            path.unlink()
