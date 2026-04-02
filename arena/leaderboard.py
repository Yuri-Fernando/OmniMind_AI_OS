"""Leaderboard da arena: ranking e estatísticas por agente."""
from typing import List, Dict


class Leaderboard:
    def __init__(self, results: List[dict] = None):
        self.results = results or []

    def compute(self) -> List[dict]:
        """Calcula ranking agregado por agente."""
        stats: Dict[str, dict] = {}
        for task in self.results:
            for agent, data in task.get("scores", {}).items():
                if agent not in stats:
                    stats[agent] = {"agent": agent, "total": 0, "score_sum": 0.0,
                                    "latency_sum": 0.0, "errors": 0}
                stats[agent]["total"] += 1
                stats[agent]["score_sum"] += data.get("score", 0)
                stats[agent]["latency_sum"] += data.get("latency_ms", 0)
                if not data.get("ok", True):
                    stats[agent]["errors"] += 1

        ranking = []
        for agent, s in stats.items():
            n = s["total"]
            ranking.append({
                "agent": agent,
                "tasks": n,
                "avg_score": round(s["score_sum"] / n, 3) if n else 0,
                "avg_latency_ms": round(s["latency_sum"] / n, 1) if n else 0,
                "errors": s["errors"],
                "accuracy": round((n - s["errors"]) / n, 3) if n else 0,
            })
        return sorted(ranking, key=lambda x: x["avg_score"], reverse=True)

    def display(self) -> str:
        ranking = self.compute()
        if not ranking:
            return "Leaderboard vazio."
        header = f"{'#':<3} {'Agente':<20} {'Score':<8} {'Latência':<12} {'Erros':<6}"
        sep = "-" * len(header)
        lines = [header, sep]
        for i, r in enumerate(ranking, 1):
            lines.append(
                f"{i:<3} {r['agent']:<20} {r['avg_score']:<8.3f} "
                f"{r['avg_latency_ms']:<12.1f} {r['errors']:<6}"
            )
        return "\n".join(lines)
