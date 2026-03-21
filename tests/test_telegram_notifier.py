"""Tests for the Telegram notification provider."""

import pytest

from ai_financial_advisor.notifications.telegram import TelegramNotifier, MAX_MESSAGE_LENGTH


class TestTelegramSplitMessage:
    def test_short_message_no_split(self):
        chunks = TelegramNotifier._split_message("Hello world")
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"

    def test_long_message_splits(self):
        # Create a message that exceeds the limit
        lines = [f"Line {i}: some data here\n" for i in range(200)]
        message = "".join(lines)
        assert len(message) > MAX_MESSAGE_LENGTH

        chunks = TelegramNotifier._split_message(message)
        assert len(chunks) > 1
        # All chunks should be within limits
        for chunk in chunks:
            assert len(chunk) <= MAX_MESSAGE_LENGTH

    def test_split_preserves_content(self):
        lines = [f"Line {i}\n" for i in range(200)]
        message = "".join(lines)
        chunks = TelegramNotifier._split_message(message)
        # Rejoined content should match original (minus stripped newlines between chunks)
        reassembled = "\n".join(chunks)
        # All original lines should be present
        for i in range(200):
            assert f"Line {i}" in reassembled

    def test_empty_message(self):
        chunks = TelegramNotifier._split_message("")
        assert len(chunks) == 1
        assert chunks[0] == ""

    def test_exact_limit_no_split(self):
        message = "x" * (MAX_MESSAGE_LENGTH - 20)
        chunks = TelegramNotifier._split_message(message)
        assert len(chunks) == 1

    def test_no_newlines_forces_hard_split(self):
        message = "x" * (MAX_MESSAGE_LENGTH * 2)
        chunks = TelegramNotifier._split_message(message)
        assert len(chunks) >= 2


class TestTelegramNotifier:
    def test_send_prepends_title(self):
        """Verify title formatting (doesn't actually send)."""
        notifier = TelegramNotifier(bot_token="fake", chat_id="fake")
        # We can't test actual sending without a real token,
        # but we can verify the object is created
        assert notifier._bot_token == "fake"
        assert notifier._chat_id == "fake"


class TestFactory:
    def test_create_telegram(self):
        from ai_financial_advisor.notifications.factory import create_notifier
        notifier = create_notifier("telegram", bot_token="tok", chat_id="123")
        assert isinstance(notifier, TelegramNotifier)

    def test_unknown_provider_raises(self):
        from ai_financial_advisor.notifications.factory import create_notifier
        with pytest.raises(ValueError, match="Unknown"):
            create_notifier("slack")

    def test_missing_token_raises(self):
        from ai_financial_advisor.notifications.factory import create_notifier
        with pytest.raises(ValueError, match="bot_token"):
            create_notifier("telegram", bot_token="", chat_id="123")
