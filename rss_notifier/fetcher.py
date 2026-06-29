"""RSS 获取模块 - 解析 RSS/Atom 源并提取新文章。

使用 feedparser 解析 RSS，支持 Atom 和 RSS 2.0 格式。
每个源独立获取，单个源失败不影响其他源。
"""

from __future__ import annotations

import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone

import feedparser

from rss_notifier.notifiers import Article

logger = logging.getLogger(__name__)


def fetch_new_articles(
    feed_name: str,
    feed_url: str,
    last_id: str | None = None,
) -> list[Article]:
    """获取某个 RSS 源的新文章。

    从最新文章开始遍历，遇到 ``last_id`` 停止。
    返回结果按时间从新到旧排列，最新文章在前。

    Args:
        feed_name: RSS 源名称（用于日志和邮件分组）。
        feed_url: RSS 源的 URL。
        last_id: 上次最后处理的文章 ID。
                 为 None 时只返回最新一篇（适用于新增源）。

    Returns:
        新文章列表，按发布时间从新到旧排序。

    Raises:
        ValueError: feedparser 解析失败时抛出。
    """
    logger.debug("Fetching: %s (%s)", feed_name, feed_url)

    req = urllib.request.Request(
        feed_url, headers={"User-Agent": "rss-mail-notifier/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_data = resp.read()
    except urllib.error.URLError as e:
        msg = f"Failed to fetch feed '{feed_name}': {e}"
        raise ValueError(msg) from e

    feed = feedparser.parse(raw_data)

    if feed.bozo and not feed.entries:
        msg = f"Failed to parse feed '{feed_name}': {feed.bozo_exception}"
        raise ValueError(msg)

    if not feed.entries:
        logger.debug("No entries found for '%s'.", feed_name)
        return []

    # feedparser 的 entries 通常是最新在前
    entries = list(feed.entries)
    new_entries: list[object] = []

    if last_id is None:
        # 新增的源：只取最新一篇，避免发送大量历史文章
        new_entries = [entries[0]]
        logger.debug(
            "No last_id for '%s', taking latest article only.",
            feed_name,
        )
    else:
        for entry in entries:
            entry_id: str = getattr(entry, "id", "") or getattr(
                entry, "link", ""
            )
            if entry_id == last_id:
                break
            new_entries.append(entry)

    if not new_entries:
        logger.debug("No new articles for '%s'.", feed_name)
        return []

    # 最新在前，方便第一时间看到最新内容

    articles: list[Article] = []
    for entry in new_entries:
        article = _parse_entry(entry, feed_name)
        articles.append(article)

    logger.debug(
        "Found %d new article(s) for '%s'.",
        len(articles),
        feed_name,
    )
    return articles


def _parse_entry(entry: object, feed_name: str) -> Article:
    """将 feedparser entry 解析为 Article 数据类。

    Args:
        entry: feedparser 的 entry 对象。
        feed_name: RSS 源名称。

    Returns:
        解析后的 Article 对象。
    """
    title: str = getattr(entry, "title", "无标题") or "无标题"
    link: str = getattr(entry, "link", "") or ""
    article_id: str = getattr(entry, "id", "") or link

    published_raw: str = getattr(entry, "published", "") or ""
    published_parsed = getattr(entry, "published_parsed", None)
    if not published_raw and published_parsed is None:
        published_raw = getattr(entry, "updated", "") or ""
        published_parsed = getattr(entry, "updated_parsed", None)

    published = _format_published(published_raw, published_parsed)

    return Article(
        feed_name=feed_name,
        title=title,
        link=link,
        published=published,
        article_id=article_id,
    )


def _format_published(
    raw: str,
    parsed: object | None,
) -> str:
    """格式化发布时间。

    优先使用 feedparser 解析后的 time struct，
    回退到原始字符串。

    Args:
        raw: 原始发布时间字符串。
        parsed: feedparser 解析后的时间结构体。

    Returns:
        格式化后的时间字符串，解析失败返回 "未知"。
    """
    if parsed is not None:
        try:
            dt = datetime(*parsed[:6], tzinfo=timezone.utc)  # type: ignore[misc,index]
            return dt.strftime("%Y-%m-%d %H:%M UTC")
        except (TypeError, ValueError):
            pass
    if raw:
        return str(raw)
    return "未知"
