import re
from collections import deque
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

DEFAULT_POST_SELECTOR = ".post"
DEFAULT_NAME_SELECTOR = ".username"
DEFAULT_MESSAGE_SELECTOR = ".message"
DEFAULT_ID_ATTRIBUTES = ("data-id", "data-comment-id", "data-post-id", "id")
DEFAULT_NEXT_PAGE_SELECTOR = "a[rel='next'], a.next"
DEFAULT_PAGINATION_SELECTOR = (
    ".pagination a, a.page-link, a[href*='page='], a[href*='/page/']"
)


class ForumParser:
    def __init__(
        self,
        post_selector: str = DEFAULT_POST_SELECTOR,
        name_selector: str = DEFAULT_NAME_SELECTOR,
        message_selector: str = DEFAULT_MESSAGE_SELECTOR,
        id_attributes: tuple[str, ...] = DEFAULT_ID_ATTRIBUTES,
        next_page_selector: str = DEFAULT_NEXT_PAGE_SELECTOR,
        pagination_selector: str = DEFAULT_PAGINATION_SELECTOR,
        headers: dict | None = None,
        timeout: int = 10,
        session: requests.Session | None = None,
    ):
        self.post_selector = post_selector
        self.name_selector = name_selector
        self.message_selector = message_selector
        self.id_attributes = id_attributes
        self.next_page_selector = next_page_selector
        self.pagination_selector = pagination_selector
        self.timeout = timeout
        self.headers = dict(DEFAULT_HEADERS)
        if headers:
            self.headers.update(headers)
        self.session = session if session is not None else requests.Session()

    def fetch_page(self, url: str) -> str:
        response = self.session.get(url, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()
        if response.encoding is None:
            response.encoding = response.apparent_encoding or "utf-8"
        return response.text

    def parse_page(self, url: str) -> list[dict]:
        return self.parse_html(self.fetch_page(url))

    def parse_pages(self, start_url: str, max_pages: int | None = None) -> list[dict]:
        if max_pages is not None:
            if isinstance(max_pages, bool) or not isinstance(max_pages, int):
                raise TypeError("max_pages должен быть целым числом или None.")
            if max_pages < 1:
                raise ValueError("max_pages должен быть больше нуля.")

        start_url = self._normalize_url(start_url)
        allowed_host = urlparse(start_url).netloc.lower()
        comments = []
        visited = set()
        queue = deque([start_url])

        while queue and (max_pages is None or len(visited) < max_pages):
            current_url = queue.popleft()
            if current_url in visited:
                continue

            visited.add(current_url)
            soup = self._make_soup(self.fetch_page(current_url))
            comments.extend(self._parse_soup(soup))

            for page_url in self._discover_page_urls(
                soup, current_url, allowed_host
            ):
                if page_url not in visited and page_url not in queue:
                    queue.append(page_url)

        return comments

    def switch_page(self, url: str, page: int) -> str:
        if isinstance(page, bool) or not isinstance(page, int):
            raise TypeError("Номер страницы должен быть целым числом.")
        if page < 1:
            raise ValueError("Номер страницы должен быть больше нуля.")

        parsed = urlparse(url)
        query = [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key != "page"
        ]
        query.append(("page", str(page)))
        return urlunparse(
            parsed._replace(query=urlencode(query), fragment="")
        )

    def parse_page_range(
        self, url_template: str, start_page: int, end_page: int
    ) -> list[dict]:
        if "{page}" not in url_template:
            raise ValueError("Шаблон URL должен содержать плейсхолдер {page}.")
        if isinstance(start_page, bool) or not isinstance(start_page, int):
            raise TypeError("start_page должен быть целым числом.")
        if isinstance(end_page, bool) or not isinstance(end_page, int):
            raise TypeError("end_page должен быть целым числом.")
        if start_page < 1:
            raise ValueError("start_page должен быть больше нуля.")
        if end_page < start_page:
            raise ValueError("end_page не может быть меньше start_page.")

        comments = []
        for page in range(start_page, end_page + 1):
            url = url_template.format(page=page)
            comments.extend(self.parse_page(url))
        return comments

    def parse_html(self, html: str) -> list[dict]:
        return self._parse_soup(self._make_soup(html))

    @staticmethod
    def _make_soup(html: str) -> BeautifulSoup:
        if not isinstance(html, str):
            raise TypeError("HTML-код страницы должен быть строкой.")
        return BeautifulSoup(html, "lxml")

    def _parse_soup(self, soup: BeautifulSoup) -> list[dict]:
        parsed = []
        for post in soup.select(self.post_selector):
            comment = self._parse_post(post)
            if comment is not None:
                parsed.append(comment)
        return parsed

    def _discover_page_urls(
        self, soup: BeautifulSoup, current_url: str, allowed_host: str
    ) -> list[str]:
        candidates = []

        next_url = self._extract_next_url(soup, current_url)
        if next_url:
            candidates.append(next_url)

        for link in soup.select(self.pagination_selector):
            href = link.get("href")
            if not href:
                continue

            href = str(href).strip()
            if (
                not href
                or href.startswith("#")
                or href.lower().startswith("javascript:")
            ):
                continue

            candidates.append(self._normalize_url(urljoin(current_url, href)))

        page_urls = []
        for page_url in candidates:
            parsed = urlparse(page_url)
            if parsed.scheme not in ("http", "https"):
                continue
            if allowed_host and parsed.netloc.lower() != allowed_host:
                continue
            if page_url == current_url or page_url in page_urls:
                continue
            page_urls.append(page_url)

        return page_urls

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url)
        return urlunparse(parsed._replace(fragment=""))

    def _extract_next_url(
        self, soup: BeautifulSoup, current_url: str
    ) -> str | None:
        link = soup.select_one(self.next_page_selector)
        if link is None:
            return None

        href = link.get("href")
        if not href:
            return None

        href = str(href).strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            return None

        return self._normalize_url(urljoin(current_url, href))

    def save_to_db(self, parsed_data: list[dict], repository) -> int:
        saved = 0
        for comment in parsed_data:
            repository.add(
                comment_id=comment["id"],
                username=comment["name"],
                message=comment["message"],
            )
            saved += 1
        return saved

    def _parse_post(self, post) -> dict | None:
        comment_id = self._extract_id(post)
        name_tag = post.select_one(self.name_selector)
        message_tag = post.select_one(self.message_selector)

        if comment_id is None or name_tag is None or message_tag is None:
            return None

        name = name_tag.get_text(" ", strip=True)
        message = message_tag.decode_contents().strip()

        if not name or not message:
            return None

        return {"id": comment_id, "name": name, "message": message}

    def _extract_id(self, post) -> int | None:
        for attribute in self.id_attributes:
            raw_value = post.get(attribute)
            if raw_value is None:
                continue
            match = re.search(r"\d+", str(raw_value))
            if match:
                return int(match.group())
        return None
