"""Ferramenta de busca web via DuckDuckGo (sem API key)."""
import urllib.request, urllib.parse, json
from typing import List


def ddg_search(query: str, max_results: int = 5) -> List[dict]:
    """Busca no DuckDuckGo Instant Answer API."""
    try:
        params = urllib.parse.urlencode({"q": query, "format": "json", "no_html": 1, "skip_disambig": 1})
        url = f"https://api.duckduckgo.com/?{params}"
        with urllib.request.urlopen(url, timeout=6) as r:
            data = json.loads(r.read())

        results = []
        if data.get("AbstractText"):
            results.append({"title": data.get("Heading", ""), "snippet": data["AbstractText"],
                            "url": data.get("AbstractURL", "")})
        for item in data.get("RelatedTopics", [])[:max_results - len(results)]:
            if isinstance(item, dict) and item.get("Text"):
                results.append({"title": item.get("Text", "")[:80], "snippet": item.get("Text", ""),
                                "url": item.get("FirstURL", "")})
        return results[:max_results]
    except Exception as e:
        return [{"error": str(e)}]


class SearchTool:
    name = "search"
    description = "Busca na web via DuckDuckGo. Input: string de busca."

    def run(self, query: str) -> str:
        results = ddg_search(query, max_results=3)
        if not results:
            return "Nenhum resultado encontrado."
        lines = []
        for r in results:
            if "error" in r:
                lines.append(f"Erro: {r['error']}")
            else:
                lines.append(f"• {r['title']}\n  {r['snippet'][:200]}")
        return "\n\n".join(lines)
