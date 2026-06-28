"""状态管理模块 - 读写 state.json。

state.json 用于记录每个 RSS 源最后处理过的文章 ID，
实现跨运行的去重。

文件格式示例::

    {
        "阮一峰": "https://www.ruanyifeng.com/blog/2024/01/...",
        "少数派": "tag:sspai.com,2024:..."
    }
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 项目根目录下的 state.json
STATE_FILE: Path = Path(__file__).resolve().parent.parent / "state.json"


class StateManager:
    """管理 RSS 状态的加载与保存。

    只在状态实际发生变化时才写入磁盘，
    避免产生不必要的 Git commit。

    Args:
        path: state.json 文件路径，默认使用项目根目录。
    """

    def __init__(self, path: Path = STATE_FILE) -> None:
        self._path: Path = path
        self._state: dict[str, str] = {}
        self._original: dict[str, str] = {}

    def load(self) -> dict[str, str]:
        """加载 state.json。

        如果文件不存在或内容为空，返回空字典。

        Returns:
            状态字典，key 为 RSS 名称，value 为最后处理的文章 ID。
        """
        if not self._path.exists():
            logger.info("State file not found, starting fresh.")
            self._state = {}
            self._original = {}
            return self._state

        content = self._path.read_text(encoding="utf-8").strip()
        if not content:
            logger.info("State file is empty, starting fresh.")
            self._state = {}
            self._original = {}
            return self._state

        self._state = json.loads(content)
        self._original = dict(self._state)
        logger.info("Loaded state: %d feed(s).", len(self._state))
        return self._state

    def save(self) -> bool:
        """保存状态到 state.json（仅当状态发生变化时）。

        Returns:
            True 表示文件已写入，False 表示无变化、未写入。
        """
        if self._state == self._original:
            logger.info("State unchanged, skipping save.")
            return False

        self._path.write_text(
            json.dumps(self._state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        logger.info("State saved to %s.", self._path)
        return True

    def get_last_id(self, feed_name: str) -> str | None:
        """获取某个 RSS 最后处理的文章 ID。

        Args:
            feed_name: RSS 源名称。

        Returns:
            最后处理的文章 ID，不存在则返回 None。
        """
        return self._state.get(feed_name)

    def update_last_id(self, feed_name: str, article_id: str) -> None:
        """更新某个 RSS 最后处理的文章 ID（仅内存，不写盘）。

        Args:
            feed_name: RSS 源名称。
            article_id: 文章唯一标识。
        """
        self._state[feed_name] = article_id

    @property
    def is_empty(self) -> bool:
        """状态是否为空（首次运行判断）。"""
        return not self._state
