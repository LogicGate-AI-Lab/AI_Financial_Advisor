"""Abstract base class for notification providers."""

from abc import ABC, abstractmethod


class Notifier(ABC):
    """Base class for all notification providers."""

    @abstractmethod
    def send(self, message: str, title: str = "") -> bool:
        """Send a notification message.

        Args:
            message: The message body (may contain markdown).
            title: Optional title/subject.

        Returns:
            True if sent successfully, False otherwise.
        """

    @abstractmethod
    def send_long(self, message: str, title: str = "") -> bool:
        """Send a long message, splitting if necessary.

        Args:
            message: The full message (may exceed provider limits).
            title: Optional title/subject.

        Returns:
            True if all parts sent successfully.
        """
