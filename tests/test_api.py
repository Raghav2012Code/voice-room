"""API tests that need no TTS models: the example adapter writes a WAV."""
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from server.server import build


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        config = {
            "server": {"host": "127.0.0.1", "port": 0},
            "models_dir": str(Path(cls.tmp.name) / "models"),
            "engines": {"example": {"enabled": True}},
        }
        path = Path(cls.tmp.name) / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        cls.httpd = build(str(path))
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)
        cls.tmp.cleanup()

    def url(self, path):
        return "http://127.0.0.1:%d%s" % (self.port, path)

    def get(self, path):
        with urllib.request.urlopen(self.url(path), timeout=5) as r:
            return r.status, json.loads(r.read())

    def post(self, payload):
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.url("/api/speak"), data=data,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read(), dict(e.headers)

    def test_health(self):
        status, body = self.get("/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertIn("example", body["engines"])

    def test_static_ui(self):
        with urllib.request.urlopen(self.url("/"), timeout=5) as r:
            html = r.read().decode("utf-8")
        self.assertIn("voice room", html.lower())
        self.assertIn("/app.js", html)
        self.assertIn("/styles.css", html)

    def test_engines(self):
        status, body = self.get("/api/engines")
        self.assertEqual(status, 200)
        engine = body["engines"][0]
        self.assertEqual(engine["id"], "example")
        self.assertTrue(engine["voices"])

    def test_speak(self):
        status, body, headers = self.post(
            {"engine": "example", "text": "Hello from the test suite.", "voice": "440", "speed": 1.0}
        )
        self.assertEqual(status, 200)
        self.assertTrue(body.startswith(b"RIFF"))
        self.assertTrue(body[8:12] == b"WAVE")
        self.assertIn("X-Gen-Seconds", headers)
        self.assertIn("X-Audio-Seconds", headers)
        self.assertEqual(headers["X-Sample-Rate"], "24000")

    def test_unknown_engine(self):
        status, body, _ = self.post({"engine": "nope", "text": "hello"})
        self.assertEqual(status, 500)
        self.assertIn("Unknown engine", json.loads(body)["error"])

    def test_empty_text(self):
        status, body, _ = self.post({"engine": "example", "text": "  "})
        self.assertEqual(status, 500)
        self.assertIn("Type something", json.loads(body)["error"])


if __name__ == "__main__":
    unittest.main()
