import unittest
from backend.stages import analysis


class AnalysisTests(unittest.TestCase):
    def _graph(self):
        return {
            "nodes": [
                {"id": "u1", "name": "alice", "type": "User"},
                {"id": "g1", "name": "Helpdesk", "type": "Group"},
                {"id": "c1", "name": "LAB-SRV01", "type": "Computer"},
                {"id": "g2", "name": "Server Operators", "type": "Group"},
                {"id": "g3", "name": "Domain Admins", "type": "Group"},
            ],
            "edges": [
                {"source": "u1", "target": "g1", "relationship": "MemberOf"},
                {"source": "g1", "target": "c1", "relationship": "AdminTo"},
                {"source": "c1", "target": "g2", "relationship": "GenericAll"},
                {"source": "g2", "target": "g3", "relationship": "MemberOf"},
            ],
            "notes": [],
        }

    def test_finds_high_risk_path(self):
        r = analysis.analyze(self._graph())
        self.assertGreater(r["path_count"], 0)
        self.assertTrue(any(f["risk"] == "High" for f in r["findings"]))

    def test_critical_edges_nonempty(self):
        r = analysis.analyze(self._graph())
        self.assertGreaterEqual(len(r["critical_edges"]), 1)


if __name__ == "__main__":
    unittest.main()
