import logging
import os
import tempfile
import unittest

import gale.log.config as config
from gale.log import add_handler, configure, get_logger, remove_handler
from gale.log.level import LogLevel


class LogConfigTestCase(unittest.TestCase):
    def setUp(self) -> None:
        config._configured = False
        logging.getLogger("gale").handlers.clear()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.tmp_dir.name, "test.log")

    def tearDown(self) -> None:
        for handler in list(logging.getLogger("gale").handlers):
            handler.close()

        logging.getLogger("gale").handlers.clear()
        self.tmp_dir.cleanup()

    def test_configure_adds_console_and_file_handlers(self) -> None:
        configure(log_file=self.log_path, console=True)
        handler_types = {type(h) for h in get_logger().handlers}
        self.assertIn(logging.StreamHandler, handler_types)
        self.assertIn(logging.FileHandler, handler_types)

    def test_configure_console_false_omits_stream_handler(self) -> None:
        configure(log_file=self.log_path, console=False)
        handler_types = {type(h) for h in get_logger().handlers}
        self.assertNotIn(logging.StreamHandler, handler_types)
        self.assertIn(logging.FileHandler, handler_types)

    def test_configure_log_file_none_omits_file_handler(self) -> None:
        configure(log_file=None, console=True)
        handler_types = {type(h) for h in get_logger().handlers}
        self.assertNotIn(logging.FileHandler, handler_types)

    def test_get_logger_auto_configures_without_explicit_call(self) -> None:
        logger = get_logger()
        self.assertTrue(config._configured)
        self.assertGreater(len(logger.handlers), 0)

    def test_get_logger_with_name_is_nested_under_gale(self) -> None:
        logger = get_logger("space_trip.player")
        self.assertEqual(logger.name, "gale.space_trip.player")

    def test_messages_are_written_to_the_log_file(self) -> None:
        configure(log_file=self.log_path, console=False)
        logger = get_logger("test")
        logger.info("hello from a test")

        for handler in get_logger().handlers:
            handler.flush()

        with open(self.log_path, encoding="utf-8") as log_file:
            content = log_file.read()

        self.assertIn("hello from a test", content)
        self.assertIn("INFO", content)

    def test_add_handler_and_remove_handler(self) -> None:
        configure(log_file=self.log_path, console=False)
        records = []
        custom_handler = logging.Handler()
        custom_handler.emit = lambda record: records.append(record)

        add_handler(custom_handler)
        get_logger("test").warning("custom handler sees this")
        self.assertEqual(len(records), 1)

        remove_handler(custom_handler)
        get_logger("test").warning("custom handler no longer sees this")
        self.assertEqual(len(records), 1)

    def test_reconfigure_keeps_custom_handlers(self) -> None:
        configure(log_file=self.log_path, console=False)
        custom_handler = logging.Handler()
        add_handler(custom_handler)

        configure(log_file=self.log_path, console=True)

        self.assertIn(custom_handler, get_logger().handlers)

    def test_level_constants_match_stdlib(self) -> None:
        self.assertEqual(LogLevel.DEBUG, logging.DEBUG)
        self.assertEqual(LogLevel.INFO, logging.INFO)
        self.assertEqual(LogLevel.WARNING, logging.WARNING)
        self.assertEqual(LogLevel.ERROR, logging.ERROR)
        self.assertEqual(LogLevel.CRITICAL, logging.CRITICAL)


if __name__ == "__main__":
    unittest.main()
