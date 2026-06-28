"""邮件通知器实现。

通过 SMTP 发送 multipart（plain + html）邮件。
自动根据端口选择连接方式：

* 465 → SMTP_SSL（直接 TLS）
* 其他 → SMTP + STARTTLS

所有 SMTP 配置均读取环境变量，不硬编码。
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

from rss_notifier.notifiers import Article, NewArticles, Notifier

logger = logging.getLogger(__name__)


class EmailNotifier(Notifier):
    """邮件通知器。

    通过 SMTP 发送 HTML + 纯文本邮件。

    环境变量：

    * ``SMTP_HOST`` - SMTP 服务器地址
    * ``SMTP_PORT`` - SMTP 端口（465 或 587）
    * ``SMTP_USER`` - 登录用户名
    * ``SMTP_PASS`` - 登录密码
    * ``TO_EMAIL``  - 收件人地址

    Args:
        host: SMTP 主机，默认读取 ``SMTP_HOST`` 环境变量。
        port: SMTP 端口，默认读取 ``SMTP_PORT`` 环境变量。
        user: 登录用户，默认读取 ``SMTP_USER`` 环境变量。
        password: 登录密码，默认读取 ``SMTP_PASS`` 环境变量。
        to_email: 收件人，默认读取 ``TO_EMAIL`` 环境变量。
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        to_email: str | None = None,
    ) -> None:
        self._host: str | None = host
        self._port: int | None = port
        self._user: str | None = user
        self._password: str | None = password
        self._to_email: str | None = to_email

    def _resolve_config(self) -> tuple[str, int, str, str, str]:
        """从环境变量解析 SMTP 配置。

        Returns:
            (host, port, user, password, to_email) 元组。

        Raises:
            ValueError: 必需的环境变量缺失时抛出。
        """
        host = self._host or os.environ.get("SMTP_HOST", "")
        port = self._port or int(os.environ.get("SMTP_PORT", "0"))
        user = self._user or os.environ.get("SMTP_USER", "")
        password = self._password or os.environ.get("SMTP_PASS", "")
        to_email = self._to_email or os.environ.get("TO_EMAIL", "")

        missing: list[str] = []
        if not host:
            missing.append("SMTP_HOST")
        if not port:
            missing.append("SMTP_PORT")
        if not user:
            missing.append("SMTP_USER")
        if not password:
            missing.append("SMTP_PASS")
        if not to_email:
            missing.append("TO_EMAIL")

        if missing:
            msg = f"Missing required environment variables: {', '.join(missing)}"
            raise ValueError(msg)

        return host, port, user, password, to_email

    def send(self, articles: NewArticles) -> None:
        """发送 HTML + 纯文本邮件。

        Args:
            articles: 按 RSS 源分组的新文章。

        Raises:
            ValueError: SMTP 配置缺失。
            smtplib.SMTPException: SMTP 通信失败。
        """
        host, port, user, password, to_email = self._resolve_config()

        total = sum(len(a) for a in articles.values())
        subject = self._build_subject(articles, total)

        plain_body = self._build_plain_text(articles, total)
        html_body = self._build_html(articles, total)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to_email
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain="rss-mail-notifier")

        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        self._send_smtp(host, port, user, password, to_email, msg)

    def _send_smtp(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        to_email: str,
        msg: MIMEMultipart,
    ) -> None:
        """建立 SMTP 连接并发送邮件。

        根据端口自动选择连接方式：
        465 使用 SMTP_SSL，其他端口使用 STARTTLS。

        Args:
            host: SMTP 主机地址。
            port: SMTP 端口。
            user: 登录用户名。
            password: 登录密码。
            to_email: 收件人地址。
            msg: 构建好的邮件消息。
        """
        if port == 465:
            logger.debug("Connecting via SMTP_SSL (port %d)...", port)
            with smtplib.SMTP_SSL(host, port, timeout=30) as server:
                server.login(user, password)
                server.sendmail(user, [to_email], msg.as_bytes())
        else:
            logger.debug("Connecting via SMTP + STARTTLS (port %d)...", port)
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.starttls()
                server.login(user, password)
                server.sendmail(user, [to_email], msg.as_bytes())

        logger.debug("Mail sent successfully.")

    @staticmethod
    def _build_subject(articles: NewArticles, total: int) -> str:
        """根据源数量和文章数量动态生成邮件标题。

        规则：
        - 1 个源，1 篇文章：【RSS 更新】源名：文章标题
        - 1 个源，多篇文章：【RSS 更新】源名：N 篇新文章
        - 多个源：【RSS 更新】N 篇新文章（源1、源2）

        Args:
            articles: 按 RSS 源分组的新文章。
            total: 新文章总数。

        Returns:
            格式化后的邮件标题。
        """
        feed_names = list(articles.keys())

        if len(feed_names) == 1:
            name = feed_names[0]
            feed_articles = articles[name]
            if len(feed_articles) == 1:
                return f"【RSS 更新】{name}：{feed_articles[0].title}"
            return f"【RSS 更新】{name}：{len(feed_articles)} 篇新文章"

        names = "、".join(feed_names)
        return f"【RSS 更新】{total} 篇新文章（{names}）"

    @staticmethod
    def _build_plain_text(articles: NewArticles, total: int) -> str:
        """构建纯文本邮件正文。

        Args:
            articles: 按 RSS 源分组的新文章。
            total: 新文章总数。

        Returns:
            格式化后的纯文本字符串。
        """
        lines: list[str] = [
            "【RSS 更新通知】",
            "",
            f"本次共发现 {total} 篇新文章。",
            "",
            "=" * 40,
        ]

        for feed_name, feed_articles in articles.items():
            lines.append("")
            lines.append(f"📚 {feed_name}")
            lines.append("")
            for article in feed_articles:
                lines.append(f"• {article.title}")
                published = article.published or "未知"
                lines.append(f"  发布时间：{published}")
                if article.link:
                    lines.append(f"  链接：{article.link}")
                lines.append("")
            lines.append("-" * 40)

        lines.append("")
        lines.append("Generated by rss-mail-notifier.")
        lines.append("https://github.com/rss-mail-notifier")

        return "\n".join(lines)

    @staticmethod
    def _build_html(articles: NewArticles, total: int) -> str:
        """构建 HTML 邮件正文。

        白底、简洁排版，支持标题 / 发布时间 / 链接 / 来源。

        Args:
            articles: 按 RSS 源分组的新文章。
            total: 新文章总数。

        Returns:
            格式化后的 HTML 字符串。
        """
        sections: list[str] = []
        for feed_name, feed_articles in articles.items():
            article_html_parts: list[str] = []
            for article in feed_articles:
                published = article.published or "未知"
                if article.link:
                    title_html = (
                        f'<a href="{article.link}" '
                        f'style="color:#1a73e8;text-decoration:none;'
                        f'font-size:16px;font-weight:600;'
                        f'line-height:1.4;">'
                        f"{article.title}</a>"
                    )
                else:
                    title_html = (
                        f'<span style="font-size:16px;font-weight:600;'
                        f'line-height:1.4;">{article.title}</span>'
                    )
                article_html_parts.append(
                    f'<div style="margin-bottom:20px;padding-bottom:16px;'
                    f'border-bottom:1px solid #eeeeee;">'
                    f'<div style="margin-bottom:6px;">{title_html}</div>'
                    f'<div style="font-size:12px;color:#999999;">'
                    f"{published}</div>"
                    f"</div>"
                )
            articles_html = "\n".join(article_html_parts)
            sections.append(
                f'<div style="margin-bottom:32px;">'
                f'<h2 style="font-size:16px;font-weight:700;color:#1a1a1a;'
                f"border-bottom:2px solid #1a73e8;"
                f'padding-bottom:8px;margin-bottom:16px;">'
                f"{feed_name}</h2>"
                f"{articles_html}"
                f"</div>"
            )

        sections_html = "\n".join(sections)
        return (
            '<!DOCTYPE html><html><head><meta charset="UTF-8"></head>'
            '<body style="background-color:#ffffff;margin:0;padding:20px;'
            "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',"
            f'Roboto,Helvetica Neue,Arial,sans-serif;">'
            f'<div style="max-width:600px;margin:0 auto;'
            f"background-color:#ffffff;border:1px solid #e0e0e0;"
            f'border-radius:8px;padding:24px;">'
            f'<div style="text-align:center;margin-bottom:24px;'
            f'padding-bottom:16px;border-bottom:1px solid #eeeeee;">'
            f'<h1 style="font-size:20px;color:#1a1a1a;margin:0 0 8px 0;">'
            f"【RSS 更新通知】</h1>"
            f'<p style="font-size:14px;color:#666666;margin:0;">'
            f'本次共发现 <strong style="color:#1a73e8;">{total}</strong>'
            f" 篇新文章</p></div>"
            f"{sections_html}"
            f'<div style="text-align:center;padding-top:16px;'
            f"border-top:1px solid #eeeeee;"
            f'font-size:12px;color:#999999;">'
            f"Generated by "
            f'<a href="https://github.com/rss-mail-notifier" '
            f'style="color:#999999;text-decoration:none;">'
            f"rss-mail-notifier</a></div></div></body></html>"
        )
