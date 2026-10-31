"""Contract tests for the TV-hosted app in ``remote/``.

The PHP endpoints run on the TV (PHP 5.2, no local interpreter), so these
tests pin the invariants that are cheap to check from the repo: the key map,
the verified read/write split for volume, and the UI's API paths.  Live
behaviour is covered by the live tests in ``test_live_tv.py``.
"""
import re
import unittest
from pathlib import Path

from tvbridge import KEY_CODES

BASE = Path(__file__).resolve().parent.parent
APP = BASE / "remote"


def read(name: str) -> str:
    path = APP / name
    if not path.exists():
        raise AssertionError(f"{path} is missing")
    return path.read_text(encoding="utf-8")


class KeyMapTest(unittest.TestCase):
    def test_php_key_map_matches_python(self) -> None:
        text = read("lib/keys.php")
        pairs = {
            m.group(1): int(m.group(2))
            for m in re.finditer(r"'(KEY_[A-Z0-9_]+)'\s*=>\s*(\d+)", text)
        }
        self.assertEqual(pairs, KEY_CODES)


class VolumeEndpointTest(unittest.TestCase):
    def test_reads_via_upnp_and_writes_via_keys(self) -> None:
        text = read("lib/upnp.php") + read("api/volume.php")
        # Reads are the only UPnP calls that work from the TV itself.
        self.assertIn("upnp_soap('GetVolume')", text)
        self.assertIn("upnp_soap('GetMute')", text)
        self.assertNotIn("upnp_soap('SetVolume'", text)
        self.assertNotIn("upnp_soap('SetMute'", text)
        # Writes go through the local key path.
        for key in ("KEY_VOLUP", "KEY_VOLDOWN", "KEY_MUTE"):
            self.assertIn(key, text)

    def test_set_ramps_in_the_background(self) -> None:
        text = read("api/volume.php") + read("lib/volume_sweep.sh")
        self.assertIn("volume_sweep.sh", text)
        self.assertIn("flock -n", text)
        self.assertIn("sleep 0.15", text)
        self.assertIn("is_int", text)
        self.assertIn("ctype_digit", text)
        self.assertIn("is_file", text)
        self.assertIn("/bin/sh", text)


class KeyEndpointTest(unittest.TestCase):
    def test_whitelists_names_and_uses_full_paths(self) -> None:
        text = read("api/key.php") + read("lib/keypress.php") + read("lib/config.php")
        self.assertIn("keys.php", text)
        self.assertIn("KEY_CODES", text)
        self.assertIn("key_code_for", text)
        self.assertIn("/mnt/opt/privateer/usr/bin/samyGOrc", text)
        self.assertIn("escapeshellarg", text)
        self.assertIn("pidof exeTV", text)
        self.assertIn("flock", text)
        # The request value must never become the command.
        self.assertNotIn("exec($name", text)
        self.assertNotIn("exec($_", text)

    def test_status_endpoint_returns_json(self) -> None:
        text = read("api/status.php")
        self.assertIn("json_encode", text)
        self.assertIn("pidof exeTV", text)


class UiTest(unittest.TestCase):
    def test_uses_tv_local_api_paths(self) -> None:
        html = read("index.html")
        for path in ("api/key.php", "api/volume.php"):
            self.assertIn(path, html)
        self.assertNotIn("/api/config", html)
        self.assertNotIn('id="setup"', html)
        self.assertNotIn("openSetup", html)
        self.assertNotIn("volTimer", html)
        self.assertIn("data.error", html)

    def test_every_data_key_is_known(self) -> None:
        html = read("index.html")
        keys = set(re.findall(r'data-key="([A-Z0-9_]+)"', html))
        self.assertTrue(keys)
        self.assertEqual(keys - set(KEY_CODES), set())


if __name__ == "__main__":
    unittest.main()
