"""
TechCrunch Scraper
Two classes:
  - HeadlineScraper: fetches all headlines, image URLs, and article links from the startups page
  - ArticleScraper:  visits each article link and scrapes the full content
"""

import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Optional
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

BASE_URL = "https://techcrunch.com/category/startups/"


@dataclass
class Headline:
    title: str
    link: str
    image_url: Optional[str] = None


@dataclass
class Article:
    title: str
    link: str
    image_url: Optional[str]
    author: Optional[str] = None
    published_date: Optional[str] = None
    content: Optional[str] = None
    tags: list = field(default_factory=list)


class HeadlineScraper:
    """Scrapes headlines, images, and links from TechCrunch startups page."""

    def __init__(self, url: str = BASE_URL):
        self.url = url
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch(self) -> list[Headline]:
        """Fetch and parse all headlines from the startups listing page."""
        logger.info("Fetching headlines from %s", self.url)
        resp = self.session.get(self.url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return self._parse(soup)

    def _parse(self, soup: BeautifulSoup) -> list[Headline]:
        headlines = []


        articles = soup.select("li.wp-block-post")

        if not articles:
           
            articles = soup.select("article")

        for item in articles:
            h3 = item.select_one("h3 a") or item.select_one("h2 a")
            if not h3:
                continue
            title = h3.get_text(strip=True)
            link = h3.get("href", "")

            
            img = item.select_one("img")
            image_url = None
            if img:
                image_url = img.get("src") or img.get("data-src")

            if title and link:
                headlines.append(Headline(title=title, link=link, image_url=image_url))

        logger.info("Found %d headlines", len(headlines))
        return headlines


class ArticleScraper:
    """Visits each article link and scrapes the full content."""

    def __init__(self, delay: float = 1.0):
        """
        Args:
            delay: seconds to wait between requests
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def scrape_all(self, headlines: list[Headline]) -> list[Article]:
        """Iterate over headlines and scrape each article."""
        articles = []
        for idx, h in enumerate(headlines):
            logger.info("[%d/%d] Scraping: %s", idx+1, len(headlines), h.link)
            try:
                article = self.scrape_one(h)
                articles.append(article)
            except (requests.RequestException, AttributeError, ValueError, TypeError) as e:
                logger.warning("Failed to scrape %s: %s", h.link, e)
                articles.append(Article(
                    title=h.title,
                    link=h.link,
                    image_url=h.image_url,
                    content=f"Error: {e}",
                ))
            if self.delay:
                time.sleep(self.delay)
        return articles

    def scrape_one(self, headline: Headline) -> Article:
        """Scrape a single article page."""
        resp = self.session.get(headline.link, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        author_tag = soup.select_one("a[rel='author']") or soup.select_one(".author-name")
        author = author_tag.get_text(strip=True) if author_tag else None

        time_tag = soup.select_one("time")
        published_date = time_tag.get("datetime") or time_tag.get_text(strip=True) if time_tag else None

        content_div = (
            soup.select_one(".entry-content")
            or soup.select_one("article .wp-block-post-content")
            or soup.select_one("article")
        )
        content = ""
        if content_div:
            for tag in content_div(["script", "style", "aside", "figure"]):
                tag.decompose()
            content = content_div.get_text(separator="\n", strip=True)

        
        tag_links = soup.select("a[rel='tag']") or soup.select(".tag-cloud a")
        tags = [t.get_text(strip=True) for t in tag_links]

        return Article(
            title=headline.title,
            link=headline.link,
            image_url=headline.image_url,
            author=author,
            published_date=published_date,
            content=content,
            tags=tags,
        )