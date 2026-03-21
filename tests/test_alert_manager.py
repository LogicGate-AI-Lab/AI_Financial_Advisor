"""Tests for the alert manager."""

from unittest.mock import MagicMock

import pytest

from ai_financial_advisor.notifications.alert_manager import AlertManager
from ai_financial_advisor.notifications.base import Notifier


class FakeNotifier(Notifier):
    """A fake notifier that records calls."""

    def __init__(self):
        self.messages: list[str] = []
        self.titles: list[str] = []

    def send(self, message: str, title: str = "") -> bool:
        self.messages.append(message)
        self.titles.append(title)
        return True

    def send_long(self, message: str, title: str = "") -> bool:
        self.messages.append(message)
        self.titles.append(title)
        return True


class TestAlertManager:
    def test_init_with_notifier(self):
        notifier = FakeNotifier()
        manager = AlertManager(notifier)
        assert manager._notifier is notifier

    def test_fake_notifier_works(self):
        notifier = FakeNotifier()
        ok = notifier.send("test", title="Test")
        assert ok
        assert len(notifier.messages) == 1

    def test_notifier_abc_enforced(self):
        """Cannot instantiate Notifier directly."""
        with pytest.raises(TypeError):
            Notifier()
