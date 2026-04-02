# tools/web_search.py
import requests
from bs4 import BeautifulSoup

class WebSearchTool:
    """Ferramenta para buscar informações simples na web."""

    def search(self, query, num_results=3):
        """
        Retorna uma lista de títulos + snippets.
        """
        search_url = f"https://www.google.com/search?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        results = []
        for g in soup.select('.tF2Cxc')[:num_results]:
            title = g.select_one('.DKV0Md').text
            snippet = g.select_one('.VwiC3b').text
            link = g.a['href']
            results.append({"title": title, "snippet": snippet, "link": link})

        return results