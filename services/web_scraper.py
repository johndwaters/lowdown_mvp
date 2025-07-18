# services/web_scraper.py
import requests
from bs4 import BeautifulSoup
from typing import Optional

def fetch_and_parse_url(url: str) -> Optional[str]:
    """
    Fetches the content from a URL and parses the main text content by removing common clutter.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')

        # A more robust way to get main content by removing common non-content tags
        for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'form', 'button']):
            element.decompose()

        # Attempt to find a main content container
        main_content = soup.find('article') or soup.find('main') or soup.body

        if main_content:
            # Get text chunks and filter out short, likely irrelevant lines
            text_chunks = [chunk.strip() for chunk in main_content.get_text(separator='\n').splitlines() if len(chunk.strip()) > 25]
            content = "\n".join(text_chunks)
        else:
            content = ""

        return content

    except requests.RequestException as e:
        print(f"Error fetching or parsing URL {url}: {e}")
        return None
