import unittest
from backend.stages import decision


class DecisionTests(unittest.TestCase):
    def test_member_of_fix(self):
        finding = {
            "start_id": "u1", "target_id": "g3",
            "path": ["u1", "g1", "g3"],
            "edges": [
                {"source": "u1", "target": "g1", "relationship": "MemberOf"},
                {"source": "g1", "target": "g3", "relationship": "MemberOf"},
            ],
            "score": 0.2, "risk": "Review", "high_risk_edges": [],
        }
        d = decision.decide(finding)
        self.assertIsNotNone(d["chosen"])
        self.assertEqual(d["chosen"]["kind"], "RemoveMember")

    def test_generic_all_fix(self):
        finding = {
            "start_id": "a", "target_id": "b",
            "path": ["a", "b"],
            "edges": [{"source": "a", "target": "b", "relationship": "GenericAll"}],
            "score": 1.0, "risk": "High", "high_risk_edges": [],
        }
        d = decision.decide(finding)
        self.assertIsNotNone(d["chosen"])
        self.assertEqual(d["chosen"]["kind"], "RemoveDaclAce")


if __name__ == "__main__":
    unittest.main()
