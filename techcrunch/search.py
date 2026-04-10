"""
TechCrunch Search Scraper

Searches TechCrunch via https://techcrunch.com/?s=query+terms
and returns headlines with title, link, image, author, date, and category.
"""

import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field, asdict
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

SEARCH_URL = "https://techcrunch.com/"


@dataclass
class SearchResult:
    """One result from TechCrunch search."""
    title: str
    link: str
    image_url: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    category: Optional[str] = None
    excerpt: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class TCSearchScraper:
    """Searches TechCrunch and parses the results page."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def search(self, query: str) -> list[SearchResult]:
        """
        Search TechCrunch for the given query.
        Returns list of SearchResult from th only* first page.
        """

        params = {"s": query}
        logger.info("[tc-search] Searching: %s", query)

        try:
            resp = self.session.get(
                SEARCH_URL,
                params=params,
                timeout=15,
                headers={"Referer": "https://techcrunch.com/"},
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error("[tc-search] Request failed: %s", e)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        return self._parse_results(soup)

    def _parse_results(self, soup: BeautifulSoup) -> list[SearchResult]:
        """
        Parse search results page.

        TechCrunch search results use the same WordPress post loop
        as category pages:
          - <li class="wp-block-post"> or <article> wrappers
          - <h3> or <h2> with <a> for title + link
          - <img> for thumbnail
          - <time> for date
          - <a rel="tag"> or category links
          - <a rel="author"> for author
          - <p> for excerpt
        """
        results: list[SearchResult] = []
        seen_urls: set = set()

      
        cards = soup.select("li.wp-block-post")
        if not cards:
            cards = soup.select("article")
        if not cards:
            
            cards = soup.select("div.post-block")

        for card in cards:
          
            title_tag = (
                card.select_one("h3 a")
                or card.select_one("h2 a")
                or card.select_one("h1 a")
            )
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "").strip()
            if not title or not link:
                continue
            if link in seen_urls:
                continue
            seen_urls.add(link)

        
            img = card.select_one("img")
            image_url = None
            if img:
                image_url = (
                    img.get("src")
                    or img.get("data-src")
                    or img.get("data-lazy-src")
                )

          
            author_tag = (
                card.select_one("a[rel='author']")
                or card.select_one(".author-name")
                or card.select_one("[class*='author'] a")
            )
            author = author_tag.get_text(strip=True) if author_tag else None

            time_tag = card.select_one("time")
            date = None
            if time_tag:
                date = time_tag.get("datetime") or time_tag.get_text(strip=True)

         
            cat_tag = (
                card.select_one("a[rel='tag']")
                or card.select_one("[class*='category'] a")
                or card.select_one("[class*='tag'] a")
            )
            category = cat_tag.get_text(strip=True) if cat_tag else None

           
            excerpt_tag = card.select_one("p")
            excerpt = None
            if excerpt_tag:
                text = excerpt_tag.get_text(strip=True)
                if len(text) > 20:
                    excerpt = text

            results.append(SearchResult(
                title=title,
                link=link,
                image_url=image_url,
                author=author,
                date=date,
                category=category,
                excerpt=excerpt,
            ))

        logger.info("[tc-search] Found %d results", len(results))
        return results
