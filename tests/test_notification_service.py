# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from notification_service import EmailNotificationService, NotificationService


class TestNotificationService(unittest.TestCase):
    def test_abstract_notification_service_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            NotificationService()

    def test_email_notifier_stores_sent_message_and_reports_success(self):
        notifier = EmailNotificationService()
        self.assertTrue(notifier.send("Регистрация прошла успешно."))
        self.assertEqual(["Регистрация прошла успешно."], notifier.sent_messages)

    def test_email_notifier_accumulates_several_messages(self):
        notifier = EmailNotificationService()
        notifier.send("Первое сообщение")
        notifier.send("Второе сообщение")
        self.assertEqual(
            ["Первое сообщение", "Второе сообщение"], notifier.sent_messages
        )


if __name__ == "__main__":
    unittest.main()