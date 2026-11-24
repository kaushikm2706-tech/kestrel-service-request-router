import json, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app


class Smoke(unittest.TestCase):
    def setUp(self):
        self.c = app.test_client()

    def post(self, d):
        return self.c.post("/route", data=json.dumps(d), content_type="application/json")

    def test_health(self):
        self.assertEqual(self.c.get("/health").get_json()["status"], "ok")

    def test_ui_loads(self):
        self.assertEqual(self.c.get("/").status_code, 200)

    def test_installer_with_payment_is_not_billing(self):
        j = self.post({"request_text": "installer did not turn up for cooktop i paid extra for this"}).get_json()
        self.assertEqual(j["recommended_team"], "Installs & Demo")

    def test_last_issue_wins(self):
        j = self.post({"request_text": "hi, want to reschedule installation of mixer, which mixer is right for 4 people"}).get_json()
        self.assertEqual(j["recommended_team"], "Product Advice")

    def test_vague_needs_clarification(self):
        j = self.post({"request_text": "someone contact me about my mixer"}).get_json()
        self.assertEqual(j["action"], "needs_clarification")

    def test_bad_input_is_polite(self):
        r = self.post({"request_text": ""})
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", r.get_json())


if __name__ == "__main__":
    unittest.main()
