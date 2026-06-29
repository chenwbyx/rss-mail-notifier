# RSS Mail Notifier

基于 Python + GitHub Actions 的 RSS 邮件通知工具。

定时检查你关注的 RSS 源，有新内容时自动发送 HTML 邮件通知。

## ✨ 功能

- ✅ 支持多个 RSS / Atom 源
- ✅ 自动去重，不会收到重复邮件
- ✅ 多个 RSS 更新合并为一封邮件
- ✅ HTML 邮件，排版清晰
- ✅ 支持 163 / QQ / Gmail / Outlook 等任意 SMTP
- ✅ GitHub Actions 免费运行，无需服务器
- ✅ 可扩展通知方式（Bark / Telegram / 企业微信等）
- ✅ 首次运行自动初始化，不会发送历史邮件

## 🚀 快速开始

### 1. Fork 本项目

点击右上角 **Fork** 按钮。

### 2. 配置 GitHub Secrets

进入仓库 **Settings → Secrets and variables → Actions → New repository secret**，添加以下 5 个变量：

| Secret 名称 | 说明 | 示例 |
|---|---|---|
| `SMTP_HOST` | SMTP 服务器地址 | `smtp.163.com` |
| `SMTP_PORT` | SMTP 端口 | `465` |
| `SMTP_USER` | 登录用户名（通常是邮箱） | `you@163.com` |
| `SMTP_PASS` | 密码或授权码 | `your_auth_code` |
| `TO_EMAIL` | 收件人邮箱 | `you@example.com` |

### 3. 启用 GitHub Actions

进入仓库 **Actions** 页面，点击 **I understand my workflows, go ahead and enable them**。

### 4. 手动测试

在 **Actions → RSS Mail Notifier → Run workflow** 手动触发一次。

首次运行只会初始化状态（记录当前最新文章），不会发送邮件。
第二次运行开始，如果有新文章，就会发送邮件。

### 5. 自动运行

配置完成后，每 6 小时自动检查一次 RSS 更新。

你也可以随时通过 **workflow_dispatch** 手动触发。

## 📧 支持的邮箱

| 邮箱 | SMTP_HOST | SMTP_PORT | 备注 |
|---|---|---|---|
| 163 邮箱 | `smtp.163.com` | `465` | 需开启 SMTP 并使用授权码 |
| 126 邮箱 | `smtp.126.com` | `465` | 需开启 SMTP 并使用授权码 |
| QQ 邮箱 | `smtp.qq.com` | `465` | 需开启 SMTP 并使用授权码 |
| Gmail | `smtp.gmail.com` | `587` | 需开启应用密码或使用 STARTTLS |
| Outlook | `smtp-mail.outlook.com` | `587` | 直接使用账号密码 |

> 端口 465 自动使用 SSL，端口 587 自动使用 STARTTLS，无需额外配置。

## 📡 新增 RSS 源

编辑 `rss_notifier/config.py`，在 `RSS_FEEDS` 列表中新增一个字典：

```python
RSS_FEEDS = [
    {
        "name": "阮一峰",
        "url": "https://www.ruanyifeng.com/blog/atom.xml",
    },
    {
        "name": "少数派",
        "url": "https://sspai.com/feed",
    },
    # 在这里添加新的 RSS 源...
]
```

新增后，下次运行时会自动检测并初始化新源（只发送最新一篇，不会发送历史文章）。

## 📡 支持的 RSS

任意标准 RSS 2.0 或 Atom 格式的源均可使用。例如：

- [阮一峰的网络日志](https://www.ruanyifeng.com/blog/atom.xml)
- [少数派](https://sspai.com/feed)
- [InfoQ](https://www.infoq.cn/feed)
- [OpenAI Blog](https://openai.com/blog/rss.xml)
- [GitHub Releases](https://github.com/{owner}/{repo}/releases.atom)
- 任意 RSS / Atom 源

## 📁 项目结构

```
rss-mail-notifier
├── .github/
│   └── workflows/
│       └── rss.yml              # GitHub Actions 工作流
├── rss_notifier/
│   ├── __init__.py              # 包入口
│   ├── config.py                # RSS 源配置
│   ├── fetcher.py               # RSS 获取与解析
│   ├── state.py                 # 状态管理（去重）
│   ├── main.py                  # 主流程入口
│   └── notifiers/
│       ├── __init__.py          # Notifier 抽象基类 + Article 数据类
│       └── email_notifier.py    # 邮件通知实现
├── state.json                   # 运行状态（自动维护，由 GitHub Actions 提交到 Git）
├── requirements.txt             # Python 依赖
├── README.md
├── LICENSE
└── .gitignore
```

## 🔧 本地开发

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/rss-mail-notifier.git
cd rss-mail-notifier

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export SMTP_HOST="smtp.163.com"
export SMTP_PORT="465"
export SMTP_USER="you@163.com"
export SMTP_PASS="your_auth_code"
export TO_EMAIL="you@example.com"

# 运行（首次只初始化状态）
python rss_notifier/main.py

# 再次运行（检测更新并发送邮件）
python rss_notifier/main.py
```

## 🔌 扩展通知方式

项目采用接口设计，新增通知方式只需：

1. 在 `rss_notifier/notifiers/` 下创建新文件
2. 继承 `Notifier` 抽象基类
3. 实现 `send` 方法
4. 在 `main.py` 中注册

```python
from rss_notifier.notifiers import Notifier, NewArticles

class TelegramNotifier(Notifier):
    """Telegram 通知。"""

    def send(self, articles: NewArticles) -> None:
        # 实现你的通知逻辑
        pass
```

计划支持的通知方式（欢迎贡献）：

- [ ] Bark
- [ ] Telegram
- [ ] 企业微信
- [ ] Server 酱
- [ ] AI 摘要

## 📄 License

[MIT](LICENSE)
