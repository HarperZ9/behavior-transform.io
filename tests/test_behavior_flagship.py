import unittest

from tools.behavior_flagship import (
    SCHEMA,
    demo_envelope,
    doctor_envelope,
    status_envelope,
)


class BehaviorFlagshipTests(unittest.TestCase):
    def test_status_uses_telos_schema(self) -> None:
        envelope = status_envelope()

        self.assertEqual(envelope["schema"], SCHEMA)
        self.assertEqual(envelope["tool"], "behavior-transform.io")
        self.assertEqual(envelope["status"], "MATCH")
        self.assertIn("CLI JSON", envelope["native"]["host_surfaces"])
        self.assertFalse(envelope["native"]["runtime_contract"]["raw_secret_export"])

    def test_doctor_checks_contract_and_secret_boundary(self) -> None:
        envelope = doctor_envelope()
        checks = {
            item["id"]
            for output in envelope["outputs"]
            if output["kind"] == "checks"
            for item in output["items"]
        }

        self.assertIn("required:docs/INTEGRATION_CONTRACT.md", checks)
        self.assertIn("raw-secret-boundary", checks)
        self.assertEqual(envelope["status"], "MATCH")

    def test_demo_is_local_io_only(self) -> None:
        envelope = demo_envelope()
        demo = envelope["outputs"][0]

        self.assertEqual(demo["runtime_surface"], "local_io")
        self.assertIn("switch back to ops calibration", demo["steps"])


if __name__ == "__main__":
    unittest.main()
