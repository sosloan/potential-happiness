import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import JqHandler, run_query


class RunQueryTests(unittest.TestCase):
    def test_runs_jq_query(self):
        result = run_query(".name", '{"name":"Ada"}')
        self.assertEqual(result, {"ok": True, "output": '"Ada"'})

    def test_returns_jq_parse_errors(self):
        result = run_query(".name", "{")
        self.assertFalse(result["ok"])
        self.assertIn("parse error", result["output"])

    def test_rejects_empty_query(self):
        with self.assertRaisesRegex(ValueError, "Enter a jq query"):
            run_query("  ", "{}")


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), JqHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def post(self, path, body):
        request = Request(
            self.base_url + path,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            response = urlopen(request)
        except HTTPError as error:
            response = error
        return response.status, json.loads(response.read())

    def test_serves_playground(self):
        with urlopen(self.base_url) as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b"JSON query workbench", response.read())

    def test_runs_query_endpoint(self):
        status, result = self.post("/api/run", {"query": ".n", "input": '{"n":2}'})
        self.assertEqual(status, 200)
        self.assertEqual(result, {"ok": True, "output": "2"})

    def test_rejects_invalid_payload(self):
        status, result = self.post("/api/run", [])
        self.assertEqual(status, 400)
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
