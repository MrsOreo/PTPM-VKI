import re
from urllib.parse import urlparse

from .parser import ForumParser

HABR_ARTICLE_PATTERN = re.compile(r"/(?:ru|en)/(?:articles|post)/(\d+)(?:/|$)")


class HabrParser(ForumParser):
    @staticmethod
    def article_id(url: str) -> int:
        if not isinstance(url, str):
            raise TypeError("Ссылка должна быть строкой.")
        match = HABR_ARTICLE_PATTERN.search(urlparse(url).path)
        if match is None:
            raise ValueError("Ссылка не содержит идентификатор статьи Habr.")
        return int(match.group(1))

    @classmethod
    def comments_url(cls, url: str) -> str:
        return f"https://habr.com/ru/articles/{cls.article_id(url)}/comments/"

    def parse_page(self, url: str) -> list[dict]:
        return super().parse_page(self.comments_url(url))

    def parse_pages(self, start_url: str, max_pages: int | None = None) -> list[dict]:
        return super().parse_pages(self.comments_url(start_url), max_pages)
