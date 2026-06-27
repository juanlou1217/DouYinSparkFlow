# 抖音自动续火花工具

![cover](docs/images/cover.png)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Playwright](https://img.shields.io/badge/Playwright-%E2%9C%94-green?logo=playwright)
![chrome-headless-shell](https://img.shields.io/badge/chrome--headless--shell-%E2%9C%94-brightgreen?logo=googlechrome)

一个面向个人用户的抖音自动续火花工具。  
它会登录抖音创作者中心，按你配置的账号、目标好友和文案策略，自动发送消息，并在单好友发送失败时自动重试。

当前仓库已经整理为两层阅读方式：

- 如果你是使用者，优先看“快速开始 / Action 部署 / 配置说明 / 常见问题”
- 如果你是维护者，继续看“项目结构 / 运行链路 / 维护建议”

## 项目概览

这个项目适合这类场景：

- 通过 GitHub Actions 定时执行续火花任务
- 管理一个或多个抖音账号的目标好友列表
- 使用固定文案、每日一言或本地 JSON 文案池发送消息
- 在发送失败时按“单个好友”粒度重试，而不是整轮任务直接退出
- 通过运行日志确认“找到谁、发给谁、谁没找到、谁发送失败”

### 这个版本的优势

- 直连抖音创作者中心，无需额外服务端
- 支持 GitHub Actions 部署，复制到自己的 GitHub 仓库后即可配置使用
- 支持文案池随机发送，避免每天固定一句
- 支持单好友发送失败自动重试，降低偶发失败带来的漏发
- 支持逐好友日志审计，方便排查到底发给了谁
- 支持多账号、多目标好友配置，适合持续维护关系链路

当前正式工作流文件是 `.github/workflows/schedule.yml`，默认配置为：

```yaml
on:
  workflow_dispatch:
  schedule:
    - cron: "17 16 * * *"
```

这表示目标时间是北京时间次日 `00:17`，但要注意：GitHub Actions 的 `schedule` 不保证绝对准点，实际触发可能延后。

## 核心能力

- 支持 GitHub Actions 自动运行
- 支持手动触发工作流
- 支持多账号、多目标好友配置
- 支持按昵称和抖音号模式匹配好友
- 支持本地 JSON 文案池随机选择每日消息
- 支持 `[API]` 占位符动态插入一言内容
- 支持好友级别的发送重试
- 支持输出逐好友发送日志，便于排查漏发

## 快速开始

如果你只想尽快跑起来，按这个顺序就够了：

1. 将本仓库复制到你自己的 GitHub 账号
2. 按 [Action 部署说明](docs/Action部署说明.md) 创建 `user-data` Environment
3. 按 [配置生成器使用](docs/配置生成器使用.md) 生成 Variables / Secrets
4. 在 `user-data` 环境里配置好 `TASKS`、Cookies 和其他参数
5. 先手动触发一次 Actions 里的正式工作流
6. 去 Actions 日志确认好友命中和发送记录是否正常

如果你不走 GitHub Actions，而是本地运行或放到自己的服务器上，直接看 [源代码部署说明](docs/源代码部署说明.md)。

## GitHub Actions 部署

仓库已经自带正式工作流，不需要你自己从零写 Action。

### 你需要做的事

1. 将仓库复制到自己的 GitHub 账号
2. 启用 `Actions`
3. 创建名为 `user-data` 的 Environment
4. 填入配置生成器生成的 Variables 和 Secrets
5. 手动运行一次验证配置

详细步骤见：

- [Action 部署说明](docs/Action部署说明.md)
- [配置生成器使用](docs/配置生成器使用.md)

### 工作流说明

正式工作流：`.github/workflows/schedule.yml`

主要步骤如下：

1. `actions/checkout`
2. `actions/setup-python`
3. 连通性检查：`curl -I https://creator.douyin.com/`
4. 安装依赖：`pip install -r requirements.txt`
5. 安装浏览器：`playwright install chromium --with-deps --only-shell`
6. 导出环境变量和密钥到 `.env`
7. 执行 `python main.py`
8. 上传运行日志 `logs/`

## 配置说明

运行配置主要来自 GitHub Environment Variables / Secrets。

### 关键 Variables

| 变量名 | 说明 |
| --- | --- |
| `TASKS` | 核心任务配置，定义账号、`unique_id` 和目标好友列表 |
| `MATCH_MODE` | 好友匹配模式，常用值：`nickname`、`short_id` |
| `MESSAGE_TEMPLATE` | 固定消息模板，未启用文案库时使用 |
| `MESSAGE_LIBRARY_PATH` | 文案库路径，当前默认使用 `data/雷人文案.json` |
| `HITOKOTO_TYPES` | 一言分类 |
| `BROWSER_TIMEOUT` | 浏览器操作超时，毫秒 |
| `FRIEND_LIST_WAIT_TIME` | 好友列表加载等待时间，毫秒 |
| `TASK_RETRY_TIMES` | 重试次数，当前既用于页面级重试，也用于单好友发送重试 |
| `LOG_LEVEL` | 日志级别，建议线上用 `Debug` 方便排查 |

### 关键 Secrets

| 变量名 | 说明 |
| --- | --- |
| `COOKIES_<UNIQUE_ID>` | 对应账号的抖音 Cookies |
| `github_token` | GitHub Token |

### `TASKS` 示例

```json
[
  {
    "username": "卷娄",
    "unique_id": "pan33308",
    "targets": ["好友A", "好友B", "好友C"]
  }
]
```

### 文案发送逻辑

发送内容优先级如下：

1. 如果 `MESSAGE_LIBRARY_PATH` 有效且文案库非空，按日期 + 账号 + 好友名选择一条文案
2. 否则使用 `MESSAGE_TEMPLATE`
3. 如果模板中包含 `[API]`，会请求一言接口替换占位符

当前仓库内置文案池：

- [data/雷人文案.json](data/雷人文案.json)

## 常见问题与排障

### 1. 为什么我设置的是北京时间 `00:17`，但不是准点发送？

因为 GitHub Actions 的 `schedule` 使用 UTC，并且即使 cron 正确，GitHub 也不保证准点触发。  
这个项目目前能做到“目标时间配置正确”，但不能保证 GitHub 在该分钟绝对启动。

如果你要严格北京时间准点触发，建议迁移到你自己的服务器或其他更稳定的定时平台。

### 2. 怎么确认到底发给了谁？

现在日志已经支持逐好友记录，关注这些关键日志：

- `命中目标好友 XXX`
- `开始给好友 XXX 发送消息`
- `已向好友 XXX 发送消息`
- `搜索结束，仍有以下好友未找到`
- `给好友 XXX 连续 N 次发送失败，已跳过`

工作流完成后，可以在 Actions 的 `run-logs` artifact 或控制台日志里查看。

### 3. 单个好友发送失败会怎么样？

当前实现是“单好友完整发送动作重试”：

- 失败时只重试这个好友
- 不会把整轮任务直接中断
- 连续失败达到上限后，记录错误并跳过该好友
- 后续好友继续执行

### 4. 为什么有时日志显示成功，但聊天记录里看起来不对？

重点看是否出现以下情况：

- 好友根本没匹配到
- 页面结构变化，导致输入框或好友列表定位失效
- Cookies 过期
- GitHub Actions 定时延迟，实际发送时间和你预期不一致

优先检查：

1. `run-logs`
2. `TASKS` 配置
3. Cookies 是否仍然有效
4. 目标好友昵称或抖音号是否改名

### 5. 我想排查 Cookie 是否还能访问点赞/收藏页，怎么做？

仓库里有一个独立检查脚本：

- [tools/check_douyin_access.py](tools/check_douyin_access.py)

它会尝试打开：

- 抖音首页
- 个人主页
- 点赞页
- 收藏页

并输出截图、HTML 和抓到的 URL，用于判断当前 Cookies 的可访问范围。

## 项目结构

这是当前仓库的主结构：

```text
.
├── .github/workflows/
│   ├── schedule.yml
│   └── schedule_dev.yml
├── core/
│   ├── browser.py
│   ├── msg_builder.py
│   └── tasks.py
├── data/
│   └── 雷人文案.json
├── docs/
│   ├── Action部署说明.md
│   ├── 配置生成器使用.md
│   └── 源代码部署说明.md
├── tools/
│   └── check_douyin_access.py
├── utils/
│   ├── config.py
│   ├── export_github_env.py
│   ├── hitokoto.py
│   ├── logger.py
│   └── message_library.py
├── main.py
└── requirements.txt
```

### 各目录职责

- `main.py`
  - 程序入口，只负责加载环境并调用任务主流程

- `core/browser.py`
  - 浏览器启动和本地 / GitHub Actions 环境差异处理

- `core/msg_builder.py`
  - 构建最终发送文案

- `core/tasks.py`
  - 核心业务逻辑，包含查找好友、发送消息、重试、日志

- `utils/config.py`
  - 解析环境变量，生成运行配置和账号任务列表

- `utils/logger.py`
  - 日志初始化和日志级别控制

- `utils/message_library.py`
  - 读取 JSON 文案库并按日期 / 账号 / 好友选择文案

- `data/`
  - 本地文案数据

- `docs/`
  - 面向使用者的部署和配置文档

- `tools/`
  - 临时或维护向的辅助脚本

## 核心运行链路

主执行流程可以概括为：

1. `main.py` 启动
2. `utils/config.py` 读取环境变量和账号任务
3. `core/browser.py` 启动 Playwright 浏览器
4. `core/tasks.py` 进入抖音创作者中心聊天页
5. 滚动好友列表，匹配目标好友
6. `core/msg_builder.py` 生成当前好友的发送文案
7. 执行单好友发送，并在失败时按好友粒度重试
8. 输出日志到控制台和 `logs/app.log`
9. GitHub Actions 上传日志 artifact

### 发送链路的关键点

- 页面进入使用通用重试
- 好友滚动查找有到底判定和未找到告警
- 发送前会等待聊天输入框出现
- 单个好友发送失败时只重试该好友
- 发送日志已经能落到“具体好友名”粒度

## 维护建议

如果你后续还要继续维护这个仓库，建议优先关注下面几件事。

### 1. 把 README 当成入口，不要把信息散在聊天记录里

这份 README 应该始终覆盖：

- 当前正式工作流是什么
- 现在线上推荐配置是什么
- 文案库使用哪个文件
- 日志应该怎么看
- 已知限制是什么

### 2. 变更好友匹配逻辑时，优先保留日志可观测性

对这个项目来说，“能不能清楚知道发给谁了”比“代码漂亮”更重要。  
改 `core/tasks.py` 时，不要轻易删掉以下日志能力：

- 找到谁
- 命中谁
- 发给谁
- 谁没找到
- 谁重试后仍失败

### 3. GitHub Actions 定时不是强实时方案

如果后续需求升级成：

- 严格北京时间准点发送
- 漏发必须自动补偿
- 要有更高可控性

那就不建议继续只依赖 GitHub Actions，而应该迁移到自有服务器或独立调度平台。

### 4. 文案池建议继续维护 JSON，不要回退到 Markdown

当前项目已经稳定使用：

- [data/雷人文案.json](data/雷人文案.json)

JSON 比 Markdown 更适合自动筛选、去重和程序化维护。

### 5. 辅助文档入口

推荐从这里继续看：

- [Action 部署说明](docs/Action部署说明.md)
- [配置生成器使用](docs/配置生成器使用.md)
- [源代码部署说明](docs/源代码部署说明.md)

## 开源协议

本项目基于 MIT 协议开源，详见 [LICENSE](LICENSE)。

## 免责声明

1. 本项目仅用于技术研究与个人学习，请勿用于违法、违规或商业滥用场景。
2. 使用本项目造成的任何账号风险、平台处罚或其他后果，由使用者自行承担。
3. 请合理控制运行频率，不要对平台造成异常请求压力。
