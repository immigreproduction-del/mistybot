"""Local-only transfer tests. No Railway credentials or network calls."""

import base64
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("transfer", Path(__file__).with_name("railway-memory-transfer.py"))
transfer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transfer)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.proc = self.root / "proc"
        self.proc.mkdir()
        self.old = b'{"previous":{"permanent_memory":["old"]}}'
        self.new = '{"474146761091579921":{"permanent_memory":["caf\u00e9"],"conversation":[]}}'.encode()
        self.destination = self.root / "memory.json"
        self.destination.write_bytes(self.old)
        self.request = {"operation": "restore", "transfer_id": "test-id", "sha256": transfer.digest(self.new),
                        "data": base64.b64encode(self.new).decode()}
        if os.name == "nt":
            # Linux-only primitives are mocked; bytes, backups and atomic replacement are real.
            fake = types.SimpleNamespace(LOCK_EX=2, LOCK_NB=4, flock=lambda *args: None)
            self.enterContext(patch.dict(sys.modules, {"fcntl": fake}))
            self.enterContext(patch.object(transfer, "sync_directory"))

    def restore(self):
        return transfer.restore(self.root, self.request, self.proc)

    def test_restore_backup_and_retry(self):
        result = self.restore()
        self.assertEqual(self.destination.read_bytes(), self.new)
        backup = Path(result["backup"])
        self.assertEqual(backup.read_bytes(), self.old)
        self.assertEqual(result["sha256"], transfer.digest(self.new))
        self.assertTrue(self.restore()["unchanged"])
        self.assertEqual(backup.read_bytes(), self.old)
        self.assertFalse(list(self.root.glob(".misty-memory-*")))

    def test_restore_empty_volume(self):
        self.destination.unlink()
        self.assertIsNone(self.restore()["backup"])
        self.assertEqual(self.destination.read_bytes(), self.new)

    def test_corrupt_payload_preserves_target(self):
        self.request["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.restore()
        self.assertEqual(self.destination.read_bytes(), self.old)

    def test_invalid_json_preserves_target(self):
        data = b'[]'
        self.request.update(data=base64.b64encode(data).decode(), sha256=transfer.digest(data))
        with self.assertRaises(ValueError):
            self.restore()
        self.assertEqual(self.destination.read_bytes(), self.old)

    def test_running_bot_refused(self):
        entry = self.proc / "42"
        entry.mkdir()
        (entry / "cmdline").write_bytes(b"python\0/app/main.py\0")
        with self.assertRaisesRegex(ValueError, "Bot cible actif"):
            self.restore()
        self.assertEqual(self.destination.read_bytes(), self.old)

    def test_process_check_unavailable(self):
        with self.assertRaises(ValueError):
            transfer.require_stopped(self.root / "missing")

    def test_backup_failure_preserves_target(self):
        (self.root / "memory-before-transfer-test-id.json").write_bytes(b"existing backup")
        with self.assertRaises(FileExistsError):
            self.restore()
        self.assertEqual(self.destination.read_bytes(), self.old)
        self.assertFalse(list(self.root.glob(".misty-memory-*")))

    def test_replace_failure_keeps_backup_and_target(self):
        with patch.object(transfer.os, "replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                self.restore()
        self.assertEqual(self.destination.read_bytes(), self.old)
        self.assertEqual((self.root / "memory-before-transfer-test-id.json").read_bytes(), self.old)

    def test_bot_restarts_during_restore(self):
        with patch.object(transfer, "require_stopped", side_effect=[None, ValueError("Bot cible actif")]):
            with self.assertRaises(ValueError):
                self.restore()
        self.assertEqual(self.destination.read_bytes(), self.old)

    def test_concurrent_transfer_refused(self):
        import fcntl
        with patch.object(fcntl, "flock", side_effect=BlockingIOError("transfer in progress")):
            with self.assertRaises(BlockingIOError):
                self.restore()
        self.assertEqual(self.destination.read_bytes(), self.old)

    def test_invalid_transfer_id(self):
        self.request["transfer_id"] = "../outside"
        with self.assertRaises(ValueError):
            self.restore()

    def test_snapshot_and_protocol(self):
        output = io.StringIO()
        with patch.object(transfer, "volume_path", return_value=self.root), contextlib.redirect_stdout(output):
            transfer.run({"operation": "export", "transfer_id": "export-test"})
        result = json.loads(output.getvalue().removeprefix("MISTY_RESULT:"))
        self.assertTrue(result["ok"])
        self.assertEqual(result["transfer_id"], "export-test")
        self.assertEqual(base64.b64decode(result["data"]), self.old)
        self.assertEqual(result["sha256"], transfer.digest(self.old))

    def test_missing_volume(self):
        with patch.dict(os.environ, {"RAILWAY_VOLUME_MOUNT_PATH": ""}):
            with self.assertRaises(ValueError):
                transfer.volume_path()

    def test_failed_probe_protocol(self):
        output = io.StringIO()
        with patch.object(transfer, "volume_path", side_effect=ValueError("volume absent")), contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit):
                transfer.run({"operation": "probe", "transfer_id": "probe-test"})
        result = json.loads(output.getvalue().removeprefix("MISTY_RESULT:"))
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "volume absent")


if __name__ == "__main__":
    unittest.main()
