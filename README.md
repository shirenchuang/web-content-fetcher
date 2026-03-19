<div align="center">

# Web Content Fetcher

**网页正文提取 · 永久免费 · 支持微信公众号**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## 简介

Web Content Fetcher 是一个轻量级的网页正文提取工具，能够自动将任意网页转换为干净的 Markdown 格式，保留标题、链接、图片和列表结构。

**核心优势：**
- Scrapling 优先提取，内置 fast / stealth 双模式，自动降级
- Jina Reader 作为二级备选
- 完美支持微信公众号、掘金、CSDN 等国内平台
- 返回标准 Markdown 格式，便于后续处理
- 零配置，开箱即用

---

## 安装

### 作为 Claude Code Skill 安装

```bash
# Clone
git clone https://github.com/shirenchuang/web-content-fetcher.git

# Copy to Claude Code skills directory
cp -r web-content-fetcher ~/.claude/skills/
```

### 安装 Python 依赖

```bash
pip install scrapling html2text
```

> **注意**：在系统管理的 Python (macOS/Linux) 上，加 `--break-system-packages` 或使用 venv。

---

## 使用方式

### 在 Claude Code 中使用

直接告诉 AI 你要读取的 URL，会自动选择最佳方案：

```
帮我读取这篇文章：https://mp.weixin.qq.com/s/EwVItQH4JUsONqv_Fmi4wQ
Extract the content from https://openai.com/blog/gpt-4o
```

### 命令行单独使用

```bash
# 基础用法（自动选择 fast 或 stealth 模式）
python3 scripts/fetch.py https://sspai.com/post/73145

# 强制 stealth 模式（用于 JS 渲染页面）
python3 scripts/fetch.py https://mp.weixin.qq.com/s/xxx --stealth

# 限制输出字符数（默认 30000）
python3 scripts/fetch.py https://example.com/article 15000

# JSON 输出（含 url, mode, selector, content_length）
python3 scripts/fetch.py https://example.com --json

# 输出到文件
python3 scripts/fetch.py https://example.com/article > output.md
```

---

## 提取策略

```
URL 输入
    │
    ▼
┌─────────────────────────────────────┐
│  1. Scrapling（首选）                │
│     · fast 模式：~1-3s，大部分网站   │
│     · stealth 模式：~5-15s，JS 渲染  │
│     · 内容太少时自动 fast → stealth   │
└─────────────────────────────────────┘
    │ 失败 / 未安装依赖
    ▼
┌─────────────────────────────────────┐
│  2. Jina Reader（备选）              │
│     · 速度快（~1-2s），格式干净      │
│     · 免费额度：200次/天             │
│     · 不支持：微信公众号、部分国内站  │
└─────────────────────────────────────┘
```

### 域名路由

| 域名 | 模式 | 说明 |
|------|------|------|
| `mp.weixin.qq.com` | `--stealth` | JS 渲染内容 |
| `zhuanlan.zhihu.com` | `--stealth` | 反爬 + JS |
| `juejin.cn` | `--stealth` | JS 渲染 SPA |
| `sspai.com` | fast | 静态 HTML |
| `blog.csdn.net` | fast | 静态 HTML |
| 其他 | fast | 自动降级 |

---

## 支持平台

| 平台 | 模式 | 状态 |
|------|------|:----:|
| 微信公众号 | stealth | ✅ |
| 掘金 | stealth | ✅ |
| CSDN | fast | ✅ |
| 少数派 | fast | ✅ |
| Substack | fast | ✅ |
| Medium | fast | ✅ |
| OpenAI / Google Blog | fast | ✅ |
| 阮一峰博客 | fast | ✅ |
| GitHub | fast | ✅ |
| 知乎 | stealth | ✅ |
| 小红书 | ❌ 需登录态 | ❌ |

---

## 输出格式

返回标准 Markdown，自动保留：

- **标题层级**：`# ## ###`
- **超链接**：`[文字](url)`
- **图片**：`![alt](url)`（data-src 懒加载自动处理）
- **列表、代码块、引用块**

---

## 相关项目

### [Kuaifa（快发）](https://github.com/shirenchuang/kuaifa) — 公众号一键排版发布

如果你需要将 Markdown 文章发布到微信公众号，推荐使用 **Kuaifa**：

- 一键 Markdown 排版，支持多种主题
- 自动上传图片到 CDN
- 一键创建公众号草稿
- 支持预览和发布

```bash
pip install kuaifa
kuaifa publish your-article.md
```

---

## 作者

<div align="center">

**石臻说AI**

AI科技博主 · 10+年大厂AI提效专家

专注于个人提效、超级个体、AI 资讯

<img src="qrcode_for_shizhen.jpg" width="200" alt="公众号二维码"/>

*扫码关注公众号*

</div>

---

## License

MIT
