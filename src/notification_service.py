from abc import ABC, abstractmethod


class NotificationService(ABC):
    @abstractmethod
    def send(self, result_message: str) -> bool:
        pass


class EmailNotificationService(NotificationService):
    def __init__(self):
        self.sent_messages = []

    def send(self, result_message: str) -> bool:
        self.sent_messages.append(result_message)
        return True