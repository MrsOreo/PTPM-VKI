import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from src.database import DatabaseRepository
from src.parser import ForumParser

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
START_URL = "https://forum.example/threads/1/page_1.html"
PAGE_URLS = [
    START_URL,
    "https://forum.example/threads/1/page_2.html",
    "https://forum.example/threads/1/page_3.html",
]


def read_fixture(filename: str) -> str:
    with open(os.path.join(FIXTURES_DIR, filename), encoding="utf-8") as fixture:
        return fixture.read()


class ForumParserTest(unittest.TestCase):
    def setUp(self):
        self.html = read_fixture("forum_page.html")
        self.pages = {
            PAGE_URLS[0]: read_fixture("page_1.html"),
            PAGE_URLS[1]: read_fixture("page_2.html"),
            PAGE_URLS[2]: read_fixture("page_3.html"),
        }
        self.parser = ForumParser()

    def test_parse_html_extracts_all_posts_with_ids(self):
        comments = self.parser.parse_html(self.html)

        self.assertEqual([101, 102, 103], [comment["id"] for comment in comments])
        self.assertEqual(3, len(comments))

    def test_parse_html_extracts_names_and_messages(self):
        comments = {
            comment["id"]: comment
            for comment in self.parser.parse_html(self.html)
        }

        self.assertEqual("alice", comments[101]["name"])
        self.assertEqual("Привет, <b>мир</b>!", comments[101]["message"])
        self.assertEqual("bob", comments[102]["name"])
        self.assertIn("Второе сообщение", comments[102]["message"])
        self.assertEqual("alice", comments[103]["name"])
        self.assertEqual("Третье и последнее", comments[103]["message"])

    def test_parse_html_preserves_inner_html_of_message(self):
        comments = {
            comment["id"]: comment
            for comment in self.parser.parse_html(self.html)
        }

        self.assertIn("<b>мир</b>", comments[101]["message"])
        self.assertIn("<p>Второе сообщение</p>", comments[102]["message"])

    def test_parse_html_skips_posts_without_id(self):
        comments = self.parser.parse_html(self.html)

        self.assertNotIn("no-id", [comment["name"] for comment in comments])

    def test_parse_page_fetches_html_and_parses_it(self):
        self.parser.fetch_page = MagicMock(return_value=self.html)

        comments = self.parser.parse_page("https://forum.example/thread/1")

        self.parser.fetch_page.assert_called_once_with(
            "https://forum.example/thread/1"
        )
        self.assertEqual(3, len(comments))

    def test_parse_pages_follows_next_links_through_all_pages(self):
        self.parser.fetch_page = MagicMock(
            side_effect=lambda url: self.pages[url]
        )

        comments = self.parser.parse_pages(START_URL)

        self.assertEqual(
            [201, 202, 203, 204],
            [comment["id"] for comment in comments],
        )
        self.assertEqual(
            PAGE_URLS,
            [call.args[0] for call in self.parser.fetch_page.call_args_list],
        )

    def test_parse_pages_respects_max_pages(self):
        self.parser.fetch_page = MagicMock(
            side_effect=lambda url: self.pages[url]
        )

        comments = self.parser.parse_pages(START_URL, max_pages=2)

        self.assertEqual(
            [201, 202, 203],
            [comment["id"] for comment in comments],
        )
        self.assertEqual(2, self.parser.fetch_page.call_count)

    def test_parse_pages_stops_when_there_is_no_next_link(self):
        self.parser.fetch_page = MagicMock(
            side_effect=lambda url: self.pages[url]
        )

        comments = self.parser.parse_pages(PAGE_URLS[2])

        self.assertEqual([204], [comment["id"] for comment in comments])
        self.parser.fetch_page.assert_called_once_with(PAGE_URLS[2])

    def test_parse_pages_protects_against_link_loops(self):
        loop_html = (
            '<div class="post" data-id="301">'
            '<span class="username">loop</span>'
            '<div class="message">Зацикленная страница</div>'
            "</div>"
            '<a rel="next" href="loop.html">Следующая</a>'
        )
        self.parser.fetch_page = MagicMock(return_value=loop_html)

        comments = self.parser.parse_pages(
            "https://forum.example/threads/1/loop.html"
        )

        self.assertEqual([301], [comment["id"] for comment in comments])
        self.assertEqual(1, self.parser.fetch_page.call_count)

    def test_parse_pages_rejects_invalid_max_pages(self):
        with self.assertRaises(ValueError):
            self.parser.parse_pages(START_URL, max_pages=0)
        with self.assertRaises(TypeError):
            self.parser.parse_pages(START_URL, max_pages="2")

    def test_parse_pages_switches_numbered_pages(self):
        def make_page(page_number, comment_id):
            links = "".join(
                f'<a class="page-link" href="?page={number}">{number}</a>'
                for number in (1, 2, 3)
            )
            return (
                f'<div class="post" data-id="{comment_id}">'
                f'<span class="username">user{page_number}</span>'
                f'<div class="message">Страница {page_number}</div>'
                "</div>"
                f'<div class="pagination">{links}</div>'
                '<a class="page-link" href="https://other.example/thread?page=2">'
                "Другой сайт</a>"
            )

        base_url = "https://forum.example/thread"
        pages = {
            f"{base_url}?page={page}": make_page(page, 400 + page)
            for page in (1, 2, 3)
        }
        self.parser.fetch_page = MagicMock(side_effect=lambda url: pages[url])

        comments = self.parser.parse_pages(f"{base_url}?page=1")

        self.assertEqual([401, 402, 403], [c["id"] for c in comments])
        self.assertEqual(
            [f"{base_url}?page={page}" for page in (1, 2, 3)],
            [call.args[0] for call in self.parser.fetch_page.call_args_list],
        )

    def test_switch_page_replaces_existing_page_parameter(self):
        url = "https://forum.example/thread?sort=asc&page=1"

        switched = self.parser.switch_page(url, 3)

        self.assertEqual(
            "https://forum.example/thread?sort=asc&page=3", switched
        )

    def test_switch_page_adds_page_parameter(self):
        url = "https://forum.example/thread?sort=asc"

        switched = self.parser.switch_page(url, 2)

        self.assertEqual(
            "https://forum.example/thread?sort=asc&page=2", switched
        )

    def test_switch_page_validates_page_number(self):
        with self.assertRaises(ValueError):
            self.parser.switch_page(START_URL, 0)
        with self.assertRaises(TypeError):
            self.parser.switch_page(START_URL, "2")

    def test_parse_page_range_uses_url_template(self):
        requested_urls = []

        def fake_fetch(url):
            requested_urls.append(url)
            page_number = int(url.rsplit("=", 1)[1])
            return self.pages[PAGE_URLS[page_number - 1]]

        self.parser.fetch_page = MagicMock(side_effect=fake_fetch)
        template = "https://forum.example/threads/1?page={page}"

        comments = self.parser.parse_page_range(template, 1, 2)

        self.assertEqual(
            [
                "https://forum.example/threads/1?page=1",
                "https://forum.example/threads/1?page=2",
            ],
            requested_urls,
        )
        self.assertEqual([201, 202, 203], [c["id"] for c in comments])

    def test_parse_page_range_requires_page_placeholder(self):
        with self.assertRaises(ValueError):
            self.parser.parse_page_range(
                "https://forum.example/threads/1", 1, 2
            )

    def test_fetch_page_sends_user_agent_header(self):
        response = MagicMock()
        response.text = self.html
        session = MagicMock()
        session.get.return_value = response
        parser = ForumParser(session=session)

        result = parser.fetch_page("https://forum.example/thread/1")

        self.assertEqual(self.html, result)
        response.raise_for_status.assert_called_once()
        _, kwargs = session.get.call_args
        self.assertIn("User-Agent", kwargs["headers"])
        self.assertTrue(kwargs["headers"]["User-Agent"])

    def test_save_to_db_stores_all_parsed_comments(self):
        repo = DatabaseRepository(":memory:")
        self.addCleanup(repo.close)
        comments = self.parser.parse_html(self.html)

        saved = self.parser.save_to_db(comments, repo)

        self.assertEqual(3, saved)
        self.assertEqual("alice", repo.get_by_id(101)["name"])
        self.assertEqual(2, len(repo.get_by_name("alice")))
        self.assertEqual(
            "<p>Второе сообщение</p>", repo.get_by_id(102)["message"]
        )

    def test_save_to_db_stores_comments_from_all_pages(self):
        repo = DatabaseRepository(":memory:")
        self.addCleanup(repo.close)
        self.parser.fetch_page = MagicMock(
            side_effect=lambda url: self.pages[url]
        )

        comments = self.parser.parse_pages(START_URL)
        saved = self.parser.save_to_db(comments, repo)

        self.assertEqual(4, saved)
        self.assertEqual("dave", repo.get_by_id(204)["name"])
        self.assertEqual(1, len(repo.get_by_name("alice")))
        self.assertEqual(1, len(repo.get_by_name("bob")))


if __name__ == "__main__":
    unittest.main()
