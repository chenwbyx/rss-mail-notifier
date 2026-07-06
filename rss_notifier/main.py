"""主入口模块 - 编排 RSS 检查与通知流程。

职责：

1. 加载配置与状态
2. 检测首次运行
3. 遍历 RSS 源，获取新文章
4. 通过通知器发送更新
5. 更新并保存状态

主流程不依赖任何具体通知实现，只通过 Notifier 抽象接口调用。
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# 支持直接运行 `python rss_notifier/main.py`
# 也支持 `python -m rss_notifier.main`
if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rss_notifier.config import RSS_FEEDS
from rss_notifier.fetcher import fetch_new_articles
from rss_notifier.notifiers import NewArticles
from rss_notifier.notifiers.email_notifier import EmailNotifier
from rss_notifier.state import StateManager

logger = logging.getLogger(__name__)


def run(first_run: bool = False, force_send: bool = False) -> bool:
    """执行 RSS 检查与通知的主流程。

    Args:
        first_run: 是否为首次运行。首次运行只初始化状态，不发送通知。
        force_send: 强制发送邮件，跳过首次运行检测。用于测试 SMTP。

    Returns:
        True 表示流程正常完成，False 表示部分 RSS 源获取失败。
    """
    state = StateManager()
    state.load()

    # 强制发送：忽略 state，取每个源最新一篇文章发送，不更新 state
    if force_send:
        return _force_send()

    # 自动检测首次运行
    if first_run or state.is_empty:
        return _init_state(state)

    # 正常流程：获取新文章并发送通知
    return _check_and_notify(state)


def _init_state(state: StateManager) -> bool:
    """首次运行：为每个 RSS 源记录最新文章 ID，不发送通知。

    Args:
        state: 状态管理器实例。

    Returns:
        True 表示全部成功，False 表示部分源失败。
    """
    print(f"First run detected. Initializing {len(RSS_FEEDS)} RSS feed(s)...\n")

    has_failure = False

    for feed_config in RSS_FEEDS:
        feed_name: str = feed_config["name"]
        feed_url: str = feed_config["url"]

        try:
            articles = fetch_new_articles(feed_name, feed_url, last_id=None)
            if articles:
                last_article = articles[-1]
                state.update_last_id(feed_name, last_article.article_id)
                print(f"  ✓ {feed_name}: initialized ({last_article.article_id})")
            else:
                print(f"  ✓ {feed_name}: no articles found")
        except Exception:
            logger.exception("Failed to initialize '%s'.", feed_name)
            print(f"  ✗ {feed_name}: failed")
            has_failure = True

    state.save()
    print("\nState initialized. No notifications sent.")
    return not has_failure


def _force_send() -> bool:
    """强制发送：忽略 state，取每个源最新一篇文章发送邮件。

    不读取 state.json，不更新 state.json。
    仅用于测试 SMTP 和邮件模板。

    Returns:
        True 表示全部成功，False 表示部分源失败。
    """
    print("Force send mode enabled.")
    print("Ignoring state.json.\n")
    print(f"Fetching latest article from {len(RSS_FEEDS)} RSS feed(s)...\n")

    all_new: NewArticles = {}
    failed_feeds: list[str] = []

    for feed_config in RSS_FEEDS:
        feed_name: str = feed_config["name"]
        feed_url: str = feed_config["url"]

        try:
            # last_id=None 表示忽略 state，只取最新一篇
            articles = fetch_new_articles(feed_name, feed_url, last_id=None)
            if articles:
                all_new[feed_name] = articles
                print(f"  ✓ {feed_name}: {articles[0].title}")
            else:
                print(f"  ✓ {feed_name}: no articles found")
        except Exception:
            logger.exception("Failed to fetch '%s'.", feed_name)
            print(f"  ✗ {feed_name}: failed")
            failed_feeds.append(feed_name)

    # 发送邮件
    if all_new:
        total = sum(len(a) for a in all_new.values())
        print(f"\nPreparing email...")
        print("Sending email...")
        try:
            notifier = EmailNotifier()
            notifier.send(all_new)
            print("Email sent successfully.")
        except Exception:
            logger.exception("Failed to send notification.")
            print("Failed to send email.")
    else:
        print("\nNo articles found in any feed.")

    # 不更新 state
    print("\nState not modified (force send mode).")

    if failed_feeds:
        print(f"Failed feeds: {', '.join(failed_feeds)}")
        return False

    return True


def _check_and_notify(state: StateManager) -> bool:
    """正常流程：获取所有 RSS 源的新文章并发送通知。

    Args:
        state: 状态管理器实例。

    Returns:
        True 表示全部成功，False 表示部分源失败。
    """
    print(f"Checking {len(RSS_FEEDS)} RSS feed(s)...\n")

    all_new: NewArticles = {}
    failed_feeds: list[str] = []

    for feed_config in RSS_FEEDS:
        feed_name: str = feed_config["name"]
        feed_url: str = feed_config["url"]

        try:
            last_id = state.get_last_id(feed_name)
            articles = fetch_new_articles(feed_name, feed_url, last_id=last_id)

            if articles:
                all_new[feed_name] = articles
                count = len(articles)
                suffix = "article" if count == 1 else "articles"
                print(f"  ✓ {feed_name}: found {count} new {suffix}")
                # 更新为最新的文章 ID
                state.update_last_id(feed_name, articles[-1].article_id)
            else:
                print(f"  ✓ {feed_name}: no updates")
        except Exception:
            logger.exception("Failed to fetch '%s'.", feed_name)
            print(f"  ✗ {feed_name}: failed")
            failed_feeds.append(feed_name)

    # 发送通知
    email_sent = False
    if all_new:
        total = sum(len(a) for a in all_new.values())
        print(f"\nFound {total} new article(s) total.")
        print("Sending email...")
        try:
            notifier = EmailNotifier()
            notifier.send(all_new)
            print("Email sent successfully.")
            email_sent = True
        except Exception:
            logger.exception("Failed to send notification.")
            print("Failed to send email.")
    else:
        print("\nNo new articles found.")

    # 保存状态
    state.save()

    # 报告失败的源
    if failed_feeds:
        print(f"\nFailed feeds: {', '.join(failed_feeds)}")
        if email_sent:
            logger.warning(
                "Some feeds failed but email was sent with remaining articles."
            )
            return True
        return False

    return True


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    is_first_run = "--first-run" in sys.argv
    is_force_send = os.environ.get("FORCE_SEND", "false").lower() in ("true", "1", "yes")
    success = run(first_run=is_first_run, force_send=is_force_send)
    sys.exit(0 if success else 1)
