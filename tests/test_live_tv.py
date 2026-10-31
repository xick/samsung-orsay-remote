"""Live checks against the deployed TV app.

Skipped when the TV is off or the app is not deployed, so the unit suite still
runs on a computer without the TV.
"""
import json
import os
import time
import unittest
import urllib.error
import urllib.request

BASE = "http://%s:1080/remote" % os.environ.get("TV_IP", "192.168.1.216")


def get(path: str) -> tuple[int, str]:
    with urllib.request.urlopen(BASE + path, timeout=8) as response:
        return response.status, response.read().decode("utf-8", "replace")


def post(path: str, body: dict, timeout: float = 15) -> tuple[int, str]:
    request = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")


class LiveTvTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            status, _ = get("/api/status.php")
        except Exception as err:  # TV off, wrong IP, app not deployed
            raise unittest.SkipTest(f"TV app not reachable at {BASE}: {err}")
        if status != 200:
            raise unittest.SkipTest(f"TV app returned HTTP {status}")

    def volume(self) -> int:
        for _ in range(3):
            try:
                _, body = get("/api/volume.php")
                return json.loads(body)["volume"]
            except Exception:
                time.sleep(0.2)
        raise AssertionError("volume endpoint did not answer")

    def wait_volume(self, target: int, timeout: float = 15.0) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.volume() == target:
                return
            time.sleep(0.3)
        self.fail(f"volume did not reach {target}; now {self.volume()}")

    def restore(self, original: int) -> None:
        try:
            self.volume()  # make sure the app is still answering
            post("/api/volume.php", {"action": "set", "volume": original}, timeout=8)
            self.wait_volume(original)
            time.sleep(0.4)  # let the sweep release its lock
        except Exception:
            pass

    def test_array_key_is_rejected(self) -> None:
        status, body = post("/api/key.php", {"key": ["KEY_UP"]})
        self.assertEqual(status, 400, body)
        self.assertIn("error", body)

    def test_array_volume_is_rejected(self) -> None:
        original = self.volume()
        try:
            status, body = post("/api/volume.php", {"action": "set", "volume": []})
            self.assertEqual(status, 400, body)
            self.assertEqual(self.volume(), original)
        finally:
            self.restore(original)

    def test_exponent_volume_is_rejected(self) -> None:
        original = self.volume()
        try:
            status, body = post("/api/volume.php", {"action": "set", "volume": "1e2"})
            self.assertEqual(status, 400, body)
            self.assertEqual(self.volume(), original)
        finally:
            self.restore(original)

    def test_float_volume_is_rejected(self) -> None:
        original = self.volume()
        try:
            status, body = post("/api/volume.php", {"action": "set", "volume": 0.9})
            self.assertEqual(status, 400, body)
            self.assertEqual(self.volume(), original)
        finally:
            self.restore(original)

    def test_set_returns_before_the_volume_ramps(self) -> None:
        original = self.volume()
        target = min(100, original + 4)
        try:
            started = time.time()
            status, body = post("/api/volume.php", {"action": "set", "volume": target})
            elapsed = time.time() - started
            self.assertEqual(status, 200, body)
            self.assertLess(elapsed, 2.0, f"set blocked for {elapsed:.1f}s")
            self.wait_volume(target)
        finally:
            self.restore(original)


if __name__ == "__main__":
    unittest.main()
