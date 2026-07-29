import json
import os
import tempfile
import time
import unittest

from gale.save.manager import SaveError, SaveManager


class SaveManagerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.manager = SaveManager(save_dir=self.tmp_dir.name)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_save_creates_the_save_dir(self) -> None:
        nested = os.path.join(self.tmp_dir.name, "nested", "saves")
        SaveManager(save_dir=nested)
        self.assertTrue(os.path.isdir(nested))

    def test_save_and_load_round_trip(self) -> None:
        self.manager.save("slot1", {"level": 3, "hp": 80})
        self.assertEqual(self.manager.load("slot1"), {"level": 3, "hp": 80})

    def test_load_missing_slot_raises_save_error(self) -> None:
        self.assertRaises(SaveError, self.manager.load, "does-not-exist")

    def test_exists(self) -> None:
        self.assertFalse(self.manager.exists("slot1"))
        self.manager.save("slot1", {})
        self.assertTrue(self.manager.exists("slot1"))

    def test_delete(self) -> None:
        self.manager.save("slot1", {})
        self.manager.delete("slot1")
        self.assertFalse(self.manager.exists("slot1"))

    def test_delete_missing_slot_is_a_no_op(self) -> None:
        self.manager.delete("does-not-exist")

    def test_save_leaves_no_temporary_file_behind(self) -> None:
        self.manager.save("slot1", {})
        leftovers = [
            name for name in os.listdir(self.tmp_dir.name) if name.endswith(".tmp")
        ]
        self.assertEqual(leftovers, [])

    def test_metadata_is_stored_and_readable_without_loading_data(self) -> None:
        self.manager.save("slot1", {"level": 3}, play_time=120.5, chapter="Forest")
        metadata = self.manager.read_metadata("slot1")
        self.assertEqual(metadata.slot, "slot1")
        self.assertEqual(metadata.version, 1)
        self.assertEqual(metadata.extra, {"play_time": 120.5, "chapter": "Forest"})

    def test_read_metadata_missing_slot_raises_save_error(self) -> None:
        self.assertRaises(SaveError, self.manager.read_metadata, "does-not-exist")

    def test_created_at_is_preserved_across_overwrites(self) -> None:
        self.manager.save("slot1", {"level": 1})
        first_created_at = self.manager.read_metadata("slot1").created_at
        time.sleep(0.01)
        self.manager.save("slot1", {"level": 2})
        second_metadata = self.manager.read_metadata("slot1")
        self.assertEqual(second_metadata.created_at, first_created_at)
        self.assertGreater(second_metadata.updated_at, first_created_at)

    def test_list_saves_orders_by_most_recently_updated_first(self) -> None:
        self.manager.save("old", {})
        time.sleep(0.01)
        self.manager.save("new", {})
        slots = [save.slot for save in self.manager.list_saves()]
        self.assertEqual(slots, ["new", "old"])

    def test_list_saves_skips_corrupted_slots(self) -> None:
        self.manager.save("good", {})
        corrupted_path = os.path.join(self.tmp_dir.name, "bad.sav")
        with open(corrupted_path, "wb") as f:
            f.write(b"not json")

        slots = [save.slot for save in self.manager.list_saves()]
        self.assertEqual(slots, ["good"])

    def test_load_corrupted_slot_raises_save_error(self) -> None:
        corrupted_path = os.path.join(self.tmp_dir.name, "bad.sav")
        with open(corrupted_path, "wb") as f:
            f.write(b"not json")

        self.assertRaises(SaveError, self.manager.load, "bad")

    def test_slot_name_with_path_separator_raises_save_error(self) -> None:
        self.assertRaises(SaveError, self.manager.save, "../escape", {})
        self.assertRaises(SaveError, self.manager.load, "../escape")

    def test_custom_file_extension(self) -> None:
        manager = SaveManager(save_dir=self.tmp_dir.name, file_extension="json")
        manager.save("slot1", {"level": 1})
        self.assertTrue(os.path.exists(os.path.join(self.tmp_dir.name, "slot1.json")))

    def test_custom_serializer_and_deserializer(self) -> None:
        def serialize(envelope):
            return json.dumps(envelope).encode("utf-16")

        def deserialize(data):
            return json.loads(data.decode("utf-16"))

        manager = SaveManager(
            save_dir=self.tmp_dir.name, serializer=serialize, deserializer=deserialize
        )
        manager.save("slot1", {"level": 1})
        self.assertEqual(manager.load("slot1"), {"level": 1})

    def test_migration_upgrades_old_saves(self) -> None:
        old_manager = SaveManager(save_dir=self.tmp_dir.name, version=1)
        old_manager.save("slot1", {"hp": 80})

        def add_mana(data):
            return {**data, "mana": 50}

        new_manager = SaveManager(
            save_dir=self.tmp_dir.name, version=2, migrations={1: add_mana}
        )
        self.assertEqual(new_manager.load("slot1"), {"hp": 80, "mana": 50})

    def test_missing_migration_raises_save_error(self) -> None:
        old_manager = SaveManager(save_dir=self.tmp_dir.name, version=1)
        old_manager.save("slot1", {"hp": 80})

        new_manager = SaveManager(save_dir=self.tmp_dir.name, version=2)
        self.assertRaises(SaveError, new_manager.load, "slot1")

    def test_save_newer_than_manager_version_raises_save_error(self) -> None:
        newer_manager = SaveManager(save_dir=self.tmp_dir.name, version=5)
        newer_manager.save("slot1", {"hp": 80})

        older_manager = SaveManager(save_dir=self.tmp_dir.name, version=1)
        self.assertRaises(SaveError, older_manager.load, "slot1")


if __name__ == "__main__":
    unittest.main()
