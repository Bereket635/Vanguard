import json
import unittest
from backend.stages import discovery, analysis, verification


class PipelineTests(unittest.TestCase):
    def _graph(self):
        return {
            "nodes": [
                {"id": "u1", "name": "alice", "type": "User"},
                {"id": "da", "name": "Domain Admins", "type": "Group"},
            ],
            "edges": [{"source": "u1", "target": "da", "relationship": "MemberOf"}],
            "notes": [],
        }

    def test_ingest_normalized(self):
        g = discovery.ingest("t.json", json.dumps(self._graph()).encode())
        self.assertEqual(len(g["nodes"]), 2)

    def test_verify_removes_path(self):
        before = self._graph()
        after = {
            "nodes": before["nodes"],
            "edges": [],
            "notes": [],
        }
        result = verification.compare(before, after)
        self.assertEqual(result["verdict"], "fixed")
        self.assertGreaterEqual(len(result["removed_paths"]), 1)


if __name__ == "__main__":
    unittest.main()
