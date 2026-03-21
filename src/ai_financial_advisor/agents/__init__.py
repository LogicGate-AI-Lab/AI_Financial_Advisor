"""Agent orchestration layer.

Agents are imported lazily to avoid pulling in heavy dependencies
(e.g., newspaper3k) when only one agent is needed.
"""

__all__ = ["AnalystAgent", "NewsAgent", "StockAgent"]


def __getattr__(name: str):  # noqa: N807
    if name == "NewsAgent":
        from .news_agent import NewsAgent
        return NewsAgent
    if name == "StockAgent":
        from .stock_agent import StockAgent
        return StockAgent
    if name == "AnalystAgent":
        from .analyst_agent import AnalystAgent
        return AnalystAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
