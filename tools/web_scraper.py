# tools/web_scraper.py
import requests
from bs4 import BeautifulSoup

class WebScraperTool:
    """Ferramenta para extrair dados de uma página web."""

    def scrape(self, url, selector="p"):
        """
        Retorna o texto de todos os elementos que correspondem ao selector CSS.
        """
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        elements = soup.select(selector)
        return "\n".join([el.get_text().strip() for el in elements])