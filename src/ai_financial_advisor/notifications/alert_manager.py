"""Alert manager — orchestrates anomaly detection and notification dispatch."""

import logging
from datetime import date

from .base import Notifier

logger = logging.getLogger(__name__)


class AlertManager:
    """Orchestrates anomaly detection and sends alerts via a Notifier.

    Args:
        notifier: A configured Notifier instance.
    """

    def __init__(self, notifier: Notifier) -> None:
        self._notifier = notifier

    def send_alerts(self, symbols: list[str], days: int = 5, threshold: float = 2.5) -> int:
        """Detect anomalies and send alerts for the given symbols.

        Args:
            symbols: List of ticker symbols to check.
            days: Look back N days for anomalies.
            threshold: Z-score threshold for anomaly detection.

        Returns:
            Number of anomalies found.
        """
        from ..analysis.anomaly import AnomalyDetector
        from ..data.stock_data import download_stock_data

        detector = AnomalyDetector(z_threshold=threshold)
        all_anomalies = []

        for symbol in symbols:
            try:
                df = download_stock_data(symbol, period="6mo")
                anomalies = detector.get_recent_anomalies(df, symbol, days=days)
                all_anomalies.extend(anomalies)
            except Exception:
                logger.exception("Failed to check %s", symbol)

        if not all_anomalies:
            logger.info("No anomalies detected for %s", ", ".join(symbols))
            return 0

        all_anomalies.sort(key=lambda a: a.date, reverse=True)

        lines = [f"🚨 *{len(all_anomalies)} Anomalies Detected*\n"]
        for a in all_anomalies:
            emoji = {"critical": "🔴", "alert": "🟡", "warning": "⚪"}.get(a.severity, "⚪")
            lines.append(f"{emoji} `{a.symbol}` {a.type} ({a.severity}) z={a.z_score:+.2f}")
            lines.append(f"   {a.description}\n")

        message = "\n".join(lines)
        self._notifier.send_long(message, title=f"Market Alerts — {date.today()}")
        return len(all_anomalies)

    def send_digest(
        self,
        symbols: list[str],
        period: str = "6mo",
    ) -> bool:
        """Send a daily digest with trend scores for the given symbols.

        Args:
            symbols: List of ticker symbols to analyze.
            period: Data period for analysis.

        Returns:
            True if the digest was sent successfully.
        """
        from ..agents.stock_agent import StockAgent

        agent = StockAgent()
        results = agent.analyze_multiple(symbols, period=period)
        results.sort(key=lambda r: r.trend.score, reverse=True)

        lines = [f"📊 *Daily Market Digest — {date.today()}*\n"]
        lines.append(f"`{'Symbol':<10} {'Close':>10} {'Score':>8} {'Signal':<10}`")
        lines.append("`" + "-" * 42 + "`")

        for r in results:
            emoji = {"Bullish": "🟢", "Bearish": "🔴"}.get(r.trend.interpretation, "⚪")
            lines.append(
                f"`{r.symbol:<10} {r.latest_close:>10.2f} {r.trend.score:>+7.4f}` {emoji} {r.trend.interpretation}"
            )

        message = "\n".join(lines)
        return self._notifier.send_long(message)
