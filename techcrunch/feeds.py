"""
TechCrunch feed URLs: WordPress categories and tags share the same listing markup
as the startups page, so HeadlineScraper works for all of these.
"""


FEEDS: list[tuple[str, str]] = [
    ("Startups", "https://techcrunch.com/category/startups/"),
    ("Venture", "https://techcrunch.com/category/venture/"),
    ("Enterprise", "https://techcrunch.com/category/enterprise/"),
    ("Apps", "https://techcrunch.com/category/apps/"),
    ("Security", "https://techcrunch.com/category/security/"),
    ("AI", "https://techcrunch.com/category/artificial-intelligence/"),
    ("Fintech", "https://techcrunch.com/category/fintech/"),
    ("Hardware", "https://techcrunch.com/category/hardware/"),
    ("Transportation", "https://techcrunch.com/category/transportation/"),
    ("Media & Entertainment", "https://techcrunch.com/category/media-entertainment/"),
    ("Biotech & Health", "https://techcrunch.com/category/biotech-health/"),
    ("Space", "https://techcrunch.com/category/space/"),
    ("Climate", "https://techcrunch.com/category/climate/"),
    ("Government & Policy", "https://techcrunch.com/category/government-policy/"),
    ("Apple", "https://techcrunch.com/tag/apple/"),
    ("Google", "https://techcrunch.com/tag/google/"),
    ("Meta", "https://techcrunch.com/tag/meta/"),
    ("Amazon", "https://techcrunch.com/tag/amazon/"),
    ("Microsoft", "https://techcrunch.com/tag/microsoft/"),
]

DEFAULT_FEED_URL = FEEDS[0][1]
