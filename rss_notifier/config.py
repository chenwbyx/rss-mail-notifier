"""配置模块 - RSS 源及相关设置。

新增 RSS 源只需在 ``RSS_FEEDS`` 列表中增加一个字典即可，
程序其他部分无需修改。
"""

from __future__ import annotations

RSS_FEEDS: list[dict[str, str]] = [
    {
        "name": "阮一峰",
        "url": "https://www.ruanyifeng.com/blog/atom.xml",
    },
]
