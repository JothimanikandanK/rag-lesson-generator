from __future__ import annotations
import sqlite3, json
from collections import Counter, defaultdict


class MemoryStore:
    """Persistent memory (SQLite). Learns from (1) failed checks + their reasons, (2) human feedback.
    It changes GUIDANCE for the generator only; the rubric is never edited automatically."""

    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT NOT NULL,
            attempt_no INTEGER NOT NULL, lesson TEXT NOT NULL, passed INTEGER NOT NULL, failed_checks TEXT NOT NULL,
            reasons TEXT NOT NULL DEFAULT '[]', created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT NOT NULL,
            status TEXT NOT NULL, attempts_used INTEGER NOT NULL, rubric_version TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT NOT NULL,
            text TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        self.conn.commit()

    def save_attempt(self, topic, attempt_no, lesson, result):
        self.conn.execute("INSERT INTO attempts(topic,attempt_no,lesson,passed,failed_checks,reasons) VALUES(?,?,?,?,?,?)",
                          (topic, attempt_no, lesson, int(result["passed"]),
                           json.dumps(result["failed_checks"]), json.dumps(result["reasons"])))
        self.conn.commit()

    def save_run(self, topic, status, attempts_used, rubric_version):
        self.conn.execute("INSERT INTO runs(topic,status,attempts_used,rubric_version) VALUES(?,?,?,?)",
                          (topic, status, attempts_used, rubric_version))
        self.conn.commit()

    def add_feedback(self, topic, text):
        self.conn.execute("INSERT INTO feedback(topic,text) VALUES(?,?)", (topic, text.strip()))
        self.conn.commit()

    def _failure_stats(self):
        counts, last_reason = Counter(), {}
        rows = self.conn.execute("SELECT failed_checks, reasons FROM attempts WHERE passed=0 ORDER BY id DESC LIMIT 100").fetchall()
        for failed, reasons in rows:
            try:
                names, rs = json.loads(failed), json.loads(reasons)
            except json.JSONDecodeError:
                continue
            counts.update(names)
            for r in rs:
                last_reason.setdefault(r.split(":", 1)[0], r)
        return counts, last_reason

    def get_hints(self, topic=None, limit=3):
        counts, last = self._failure_stats()
        parts = []
        if counts:
            parts.append("Checks that failed most often in earlier runs (fix these first): " + " | ".join(
                last.get(n, n) for n, _ in counts.most_common(limit)))
        fb = [t for (t,) in self.conn.execute("SELECT text FROM feedback ORDER BY id DESC LIMIT 3")]
        if fb:
            parts.append("Human reviewer feedback to respect: " + " | ".join(fb))
        return "\n".join(parts)

    def export_snapshot(self):
        counts, _ = self._failure_stats()
        runs = self.conn.execute("SELECT topic,status,attempts_used,rubric_version,created_at FROM runs ORDER BY id").fetchall()
        return {"total_runs": len(runs), "failure_counts": dict(counts),
                "rubric_review_flags": [n for n, k in counts.items() if k >= 5],
                "runs": [dict(zip(("topic", "status", "attempts_used", "rubric_version", "created_at"), r)) for r in runs],
                "human_feedback": [t for (t,) in self.conn.execute("SELECT text FROM feedback ORDER BY id")]}

    def close(self):
        self.conn.close()
