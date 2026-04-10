"""
TechCrunch terminal UI: pick a category, browse headlines (text only), open full article.
"""

from __future__ import annotations

import asyncio
import logging

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView, Select, Static

from techcrunch.feeds import DEFAULT_FEED_URL, FEEDS
from techcrunch.scraper import Article, ArticleScraper, Headline, HeadlineScraper


class HeadlineListItem(ListItem):
    def __init__(self, headline: Headline) -> None:
        self.headline = headline
        super().__init__(Label(headline.title))


class ReaderScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("b", "back", "Back"),
    ]

    def __init__(self, article: Article) -> None:
        super().__init__()
        self.article = article

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="reader-root"):
            yield Static(self.article.title, id="reader-title", markup=False)
            meta_bits = []
            if self.article.author:
                meta_bits.append(self.article.author)
            if self.article.published_date:
                meta_bits.append(self.article.published_date)
            if meta_bits:
                yield Static(" · ".join(meta_bits), id="reader-meta", markup=False)
            with VerticalScroll(id="reader-scroll"):
                body = (self.article.content or "").strip() or "(No article body could be loaded.)"
                yield Static(body, id="reader-body", markup=False)
            tags_line = (
                "Tags: " + " · ".join(self.article.tags)
                if self.article.tags
                else "Tags: —"
            )
            yield Static(tags_line, id="reader-tags", markup=False)
        yield Footer()

    def action_back(self) -> None:
        self.app.pop_screen()


class CrunchApp(App):
    CSS = """
    #reader-root {
        height: 1fr;
        padding: 0 1;
    }
    #reader-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #reader-meta {
        color: $text-muted;
        margin-bottom: 1;
    }
    #reader-scroll {
        height: 1fr;
        border: tall $border-blurred;
        padding: 0 1;
        margin-bottom: 1;
    }
    #reader-body {
        height: auto;
    }
    #reader-tags {
        color: $accent;
        padding-top: 1;
        border-top: solid $border-blurred;
    }
    #main-row {
        height: 1fr;
    }
    #headlines {
        height: 1fr;
        border: tall $border-blurred;
    }
    #category {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "reload_feed", "Reload"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._feed_url: str | None = None
        self._feed_lock: asyncio.Lock | None = None

    def compose(self) -> ComposeResult:
        yield Header(name="TechCrunch")
        with Vertical(id="main-col"):
            yield Select(
                [(label, url) for label, url in FEEDS],
                value=DEFAULT_FEED_URL,
                id="category",
                prompt="Category",
            )
            with Container(id="main-row"):
                yield ListView(id="headlines")
        yield Footer()

    async def on_mount(self) -> None:
        self._feed_lock = asyncio.Lock()
        logging.getLogger("techcrunch.scraper").setLevel(logging.WARNING)
        sel = self.query_one("#category", Select)
        self._feed_url = str(sel.value)
        await self._load_feed_async(self._feed_url)

    @on(Select.Changed, "#category")
    async def category_changed(self, event: Select.Changed) -> None:
        if event.value is Select.NULL:
            return
        url = str(event.value)
        if url == self._feed_url:
            return
        self._feed_url = url
        await self._load_feed_async(url)

    async def _load_feed_async(self, url: str) -> None:
        assert self._feed_lock is not None
        async with self._feed_lock:
            lv = self.query_one("#headlines", ListView)
            await lv.clear()
            await lv.extend([ListItem(Label("Loading…"))])
            try:
                headlines = await asyncio.to_thread(HeadlineScraper(url).fetch)
            except Exception as e:
                await lv.clear()
                await lv.extend([ListItem(Label(f"Error loading feed: {e}"))])
                self.notify(f"Feed error: {e}", severity="error")
                return

            await lv.clear()
            if not headlines:
                await lv.extend([ListItem(Label("(No headlines)"))])
                return
            await lv.extend([HeadlineListItem(h) for h in headlines])

    def action_reload_feed(self) -> None:
        if self._feed_url:
            self.run_worker(
                self._load_feed_async(self._feed_url),
                exclusive=True,
                group="feed",
                exit_on_error=False,
            )

    @on(ListView.Selected, "#headlines")
    async def headline_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if not isinstance(item, HeadlineListItem):
            return
        self.notify("Loading article…", timeout=1.5)
        try:
            article = await asyncio.to_thread(
                ArticleScraper(delay=0).scrape_one,
                item.headline,
            )
        except Exception as e:
            self.notify(f"Could not load article: {e}", severity="error")
            return
        self.push_screen(ReaderScreen(article))


def run_app() -> None:
    CrunchApp().run()
