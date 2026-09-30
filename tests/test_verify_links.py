import os
import subprocess
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VL = Path(__file__).resolve().parents[1] / "skills/study-shared/scripts/verify_links.py"
FLAKY = {"n": 0}


class Normal(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def page(self, code, title):
        body = f"<html><head><title>{title}</title></head><body>x</body></html>".encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def go(self, code, where):
        self.send_response(code)
        self.send_header("Location", where)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        p = self.path
        if p == "/ok":
            self.page(200, "OK page")
        elif p == "/slash":
            self.go(301, "/slash/")
        elif p == "/slash/":
            self.page(200, "Slash page")
        elif p == "/elsewhere-302":
            self.go(302, "/landing")
        elif p == "/perm-308":
            self.go(308, "/ok")
        elif p == "/landing":
            self.page(200, "Landing")
        elif p == "/flaky":
            FLAKY["n"] += 1
            self.page(429 if FLAKY["n"] <= 1 else 200, "Flaky")
        elif p == "/always-429":
            self.page(429, "Busy")
        elif p == "/forbidden":
            self.page(403, "Forbidden")
        else:
            self.page(404, "Not found")

    do_HEAD = do_GET


class Spa(Normal):
    def do_GET(self):
        self.page(200, "Same Title Everywhere")

    do_HEAD = do_GET


def serve(handler):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


class VerifyLinks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv, cls.base = serve(Normal)
        cls.spa, cls.spa_base = serve(Spa)

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.spa.shutdown()

    def run_vl(self, *paths, base=None):
        urls = [(base or self.base) + p for p in paths]
        env = dict(os.environ, STUDY_LINK_BACKOFF="0,0")
        r = subprocess.run(["python3", str(VL), *urls], capture_output=True, text=True, env=env, timeout=60)
        rows = {}
        for line in r.stdout.splitlines():
            parts = line.split()
            rows[parts[2]] = (parts[0], parts[4] if len(parts) > 4 else None)
        return r.returncode, rows

    def status(self, path, base=None):
        return self.run_vl(path, base=base)[1][(base or self.base) + path]

    def test_plain_200_is_ok(self):
        self.assertEqual(self.status("/ok")[0], "OK")

    def test_trailing_slash_redirect_is_ok(self):
        self.assertEqual(self.status("/slash")[0], "OK")

    def test_redirect_to_other_path_is_flagged_with_final_url(self):
        st, final = self.status("/elsewhere-302")
        self.assertEqual(st, "REDIRECT")
        self.assertTrue(final.endswith("/landing"))

    def test_308_is_followed(self):
        st, final = self.status("/perm-308")
        self.assertEqual(st, "REDIRECT")
        self.assertTrue(final.endswith("/ok"))

    def test_404_is_bad(self):
        self.assertEqual(self.status("/nope")[0], "BAD")

    def test_429_then_200_is_ok_after_retry(self):
        FLAKY["n"] = 0
        self.assertEqual(self.status("/flaky")[0], "OK")

    def test_persistent_429_is_rate_limited_not_bad(self):
        self.assertEqual(self.status("/always-429")[0], "RATE-LIMITED")

    def test_403_is_blocked_not_bad(self):
        self.assertEqual(self.status("/forbidden")[0], "BLOCKED")

    def test_catch_all_host_with_same_title_is_spa(self):
        self.assertEqual(self.status("/docs/real-looking-page", base=self.spa_base)[0], "SPA?")

    def test_exit_codes(self):
        self.assertEqual(self.run_vl("/ok")[0], 0)
        self.assertEqual(self.run_vl("/ok", "/elsewhere-302")[0], 2)
        self.assertEqual(self.run_vl("/ok", "/nope")[0], 1)


if __name__ == "__main__":
    unittest.main()
