import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from src.database import DatabaseRepository
from src.habr_parser import HabrParser

ARTICLE_URL = "https://habr.com/ru/articles/1107748/"
COMMENTS_URL = "https://habr.com/ru/articles/1107748/comments/"

HABR_HTML = """
<div class="tm-comments__tree" data-comments-list>
    <section class="tm-comment-thread">
        <article class="tm-comment-thread__comment" id="30637372">
            <div class="tm-comment">
                <a class="tm-user-info__username" href="/ru/users/Mixael_sas/">Mixael_sas</a>
                <div class="tm-comment__body-content"><p>Т.е. по сути sing-box с удобным интерфейсом.</p></div>
            </div>
        </article>
        <div class="tm-comment-thread__children">
            <section class="tm-comment-thread">
                <article class="tm-comment-thread__comment" id="30638298">
                    <div class="tm-comment">
                        <a class="tm-user-info__username" href="/ru/users/dotnetfx40/">dotnetfx40</a>
                        <div class="tm-comment__body-content"><p>ну или на openwrt x86</p></div>
                    </div>
                </article>
            </section>
        </div>
    </section>
    <section class="tm-comment-thread">
        <article class="tm-comment-thread__comment" id="30637466">
            <div class="tm-comment">
                <a class="tm-user-info__username" href="/ru/users/atrevido/">atrevido</a>
                <div class="tm-comment__body-content"><p>Сейчас версия mainline, я планирую обновлять.</p></div>
            </div>
        </article>
    </section>
    <section class="tm-comment-thread">
        <article class="tm-comment-thread__comment" id="30639578">
            <div class="tm-comment">
                <a class="tm-user-info__username" href="/ru/users/qclo66/">qclo66</a>
                <div class="tm-comment__body-content"><blockquote><p>Цитата</p></blockquote><p>Ответ про sing-box.</p></div>
            </div>
        </article>
    </section>
    <section class="tm-comment-thread">
        <article class="tm-comment-thread__comment" id="30640872">
            <div class="tm-comment">
                <a class="tm-user-info__username" href="/ru/users/toxblh/">toxblh</a>
                <div class="tm-comment__body-content"><p>Ссылка: <a href="https://github.com/Toxblh/Keenetic-Manager">Keenetic-Manager</a></p></div>
            </div>
        </article>
    </section>
    <section class="tm-comment-thread">
        <article class="tm-comment-thread__comment" id="30637432">
            <div class="tm-comment">
                <a class="tm-user-info__username" href="/ru/users/Zivaka/">Zivaka</a>
                <div class="tm-comment__body-content"><p>Тоже использовал KVAS.</p></div>
            </div>
        </article>
    </section>
</div>
"""


class HabrParserTest(unittest.TestCase):
    def setUp(self):
        self.html = HABR_HTML
        self.parser = HabrParser()

    def test_article_id_from_article_url(self):
        self.assertEqual(1107748, self.parser.article_id(ARTICLE_URL))

    def test_article_id_from_comments_url(self):
        self.assertEqual(1107748, self.parser.article_id(COMMENTS_URL))

    def test_article_id_from_old_post_url(self):
        self.assertEqual(
            1107748,
            self.parser.article_id("https://habr.com/ru/post/1107748/"),
        )

    def test_article_id_from_english_url(self):
        self.assertEqual(
            1107748,
            self.parser.article_id("https://habr.com/en/articles/1107748/"),
        )

    def test_article_id_rejects_url_without_article_id(self):
        with self.assertRaises(ValueError):
            self.parser.article_id("https://habr.com/ru/articles/")
        with self.assertRaises(ValueError):
            self.parser.article_id("https://habr.com/ru/hubs/python/")

    def test_article_id_rejects_non_string_url(self):
        with self.assertRaises(TypeError):
            self.parser.article_id(1107748)

    def test_comments_url_converts_article_url(self):
        self.assertEqual(COMMENTS_URL, self.parser.comments_url(ARTICLE_URL))

    def test_comments_url_converts_old_post_url(self):
        self.assertEqual(
            COMMENTS_URL,
            self.parser.comments_url("https://habr.com/ru/post/1107748/"),
        )

    def test_comments_url_is_idempotent(self):
        self.assertEqual(
            COMMENTS_URL, self.parser.comments_url(COMMENTS_URL)
        )

    def test_parse_html_extracts_comments_from_habr_markup(self):
        comments = self.parser.parse_html(self.html)

        self.assertEqual(6, len(comments))
        self.assertEqual(30637372, comments[0]["id"])
        self.assertEqual("Mixael_sas", comments[0]["name"])
        self.assertIn("sing-box", comments[0]["message"])
        self.assertTrue(all(isinstance(comment["id"], int) for comment in comments))

    def test_parse_html_preserves_habr_message_markup(self):
        comments = {
            comment["id"]: comment
            for comment in self.parser.parse_html(self.html)
        }

        self.assertTrue(comments[30637372]["message"].startswith("<p>"))
        self.assertIn("<blockquote>", comments[30639578]["message"])

    def test_parse_html_extracts_all_known_authors(self):
        comments = self.parser.parse_html(self.html)
        names = {comment["name"] for comment in comments}

        self.assertIn("Mixael_sas", names)
        self.assertIn("atrevido", names)
        self.assertIn("toxblh", names)

    def test_parse_html_extracts_nested_replies(self):
        comments = {
            comment["id"]: comment
            for comment in self.parser.parse_html(self.html)
        }

        self.assertEqual("dotnetfx40", comments[30638298]["name"])
        self.assertIn("openwrt", comments[30638298]["message"])

    def test_parse_page_requests_comments_url(self):
        self.parser.fetch_page = MagicMock(return_value=self.html)

        comments = self.parser.parse_page(ARTICLE_URL)

        self.parser.fetch_page.assert_called_once_with(COMMENTS_URL)
        self.assertEqual(6, len(comments))

    def test_parse_pages_requests_comments_url(self):
        self.parser.fetch_page = MagicMock(return_value=self.html)

        comments = self.parser.parse_pages(ARTICLE_URL)

        self.parser.fetch_page.assert_called_once_with(COMMENTS_URL)
        self.assertEqual(6, len(comments))

    def test_save_to_db_stores_habr_comments(self):
        repo = DatabaseRepository(":memory:")
        self.addCleanup(repo.close)
        comments = self.parser.parse_html(self.html)

        saved = self.parser.save_to_db(comments, repo)

        self.assertEqual(6, saved)
        self.assertEqual("Mixael_sas", repo.get_by_id(30637372)["name"])
        self.assertIn("sing-box", repo.get_by_id(30637372)["message"])


if __name__ == "__main__":
    unittest.main()
