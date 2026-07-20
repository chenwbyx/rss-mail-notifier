"""配置模块 - RSS 源及相关设置。

新增 RSS 源只需在 ``RSS_FEEDS`` 列表中增加一个字典即可，
程序其他部分无需修改。

每个源包含以下字段：

* ``name`` - 显示名称（用于日志、邮件分组、状态 key）
* ``url`` - RSS/Atom 源地址
* ``category`` - 分类标签（用于整理，不影响运行逻辑）
"""

from __future__ import annotations

RSS_FEEDS: list[dict[str, str]] = [
    # ── AI / ML ──────────────────────────────────────────
    {
        "name": "One Useful Thing",
        "url": "https://www.oneusefulthing.org/feed",
        "category": "AI / ML",
    },
    # ── 软件工程 / 架构 ──────────────────────────────────
    {
        "name": "Martin Fowler",
        "url": "https://martinfowler.com/feed.atom",
        "category": "软件工程 / 架构",
    },
    {
        "name": "High Scalability",
        "url": "http://highscalability.com/rss",
        "category": "软件工程 / 架构",
    },
    {
        "name": "The Pragmatic Engineer",
        "url": "https://blog.pragmaticengineer.com/rss/",
        "category": "软件工程 / 架构",
    },
    # ── 云计算 / 基础设施 ────────────────────────────────
    {
        "name": "Cloudflare Blog",
        "url": "https://blog.cloudflare.com/rss/",
        "category": "云计算 / 基础设施",
    },
    {
        "name": "AWS News Blog",
        "url": "https://aws.amazon.com/blogs/aws/feed/",
        "category": "云计算 / 基础设施",
    },
    # ── 综合技术 ─────────────────────────────────────────
    {
        "name": "InfoQ",
        "url": "https://www.infoq.com/feed/",
        "category": "综合技术",
    },
    {
        "name": "阮一峰",
        "url": "https://www.ruanyifeng.com/blog/atom.xml",
        "category": "综合技术",
    },
    # ── 技术博客 / 独立作者 ──────────────────────────────
    {
        "name": "Simon Willison",
        "url": "https://simonwillison.net/atom/everything/",
        "category": "技术博客 / 独立作者",
    },
    {
        "name": "Benedict Evans",
        "url": "https://www.ben-evans.com/benedictevans?format=rss",
        "category": "技术博客 / 独立作者",
    },
    # ── 中文社区 ─────────────────────────────────────────
    {
        "name": "少数派",
        "url": "https://sspai.com/feed",
        "category": "中文社区",
    },
    {
        "name": "60s News",
        "url": "https://60s.viki.moe/v2/60s/rss",
        "category":  "中文社区",
    },
    {
        "name": "V2EX",
        "url": "https://www.v2ex.com/index.xml",
        "category": "中文社区",
    },
]
