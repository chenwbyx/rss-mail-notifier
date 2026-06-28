"""通知器抽象基类模块。

所有通知方式（邮件、Bark、Telegram 等）都应继承 ``Notifier`` 抽象类，
实现 ``send`` 方法。主流程只依赖抽象接口，不依赖具体实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Article:
    """表示一篇 RSS 文章。

    Attributes:
        feed_name: RSS 源名称。
        title: 文章标题。
        link: 文章链接。
        published: 发布时间（已格式化字符串）。
        article_id: 文章唯一标识（优先 id，其次 link）。
    """

    feed_name: str
    title: str
    link: str
    published: str
    article_id: str


# feed_name -> 该源的新文章列表
NewArticles = dict[str, list[Article]]


class Notifier(ABC):
    """通知器抽象基类。

    所有通知渠道必须实现此接口。主流程通过此抽象调用，
    不关心具体通知方式的实现细节。

    扩展示例::

        class BarkNotifier(Notifier):
            def send(self, articles): ...

        class TelegramNotifier(Notifier):
            def send(self, articles): ...
    """

    @abstractmethod
    def send(self, articles: NewArticles) -> None:
        """发送通知。

        Args:
            articles: 按 RSS 源分组的新文章字典。
                      key 为源名称，value 为该源的新文章列表。

        Raises:
            Exception: 发送失败时抛出，由调用方统一捕获。
        """
