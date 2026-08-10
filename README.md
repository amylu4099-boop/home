# 音视频转录 Agent

Hermes 平台的独立 profile，代号 `av-transcription`，通过飞书 bot **音视频转录agent** 对外服务。
私聊 / 群聊均可触发；群里默认 @bot 才响应。

## 仓库结构

```
.
├── README.md                  # 本文件
├── .gitignore                 # 排除敏感 + Hermes 运行时文件
├── .env.example               # 凭据模板（变量名 + 占位）
├── hermes-profile/            # Hermes profile 关键文件（不含敏感）
│   ├── SOUL.md                # 角色定义 / 已采纳规则
│   ├── config.yaml            # 模型 / 平台配置
│   ├── profile.yaml           # profile 元数据
│   ├── .no-bundled-skills     # 标记文件（创建时 --no-skills）
│   └── restore.bat            # 一键恢复脚本（Windows）
├── transcriptions/
│   └── 转录结果.md            # 已转录的样例
└── scripts/
    └── transcribe.py          # faster-whisper 转录脚本（CPU）
```

## 出错时怎么回退

### 场景 A：SOUL.md / config.yaml 写坏了（agent 行为跑偏）

```cmd
cd C:\Users\Michael\Desktop\音视频转录
git checkout HEAD -- hermes-profile/
hermes-profile\restore.bat
```

### 场景 B：整个 hermes profile 目录被删 / 损坏

1. `git clone <repo-url>` 把仓库拉回来
2. `cd 音视频转录`
3. `hermes-profile\restore.bat` ← 自动把文件复制到 `%LOCALAPPDATA%\hermes\profiles\av-transcription\`
4. 编辑 `%LOCALAPPDATA%\hermes\profiles\av-transcription\.env` 填入真实凭据
5. 重启 gateway：
   ```cmd
   taskkill /F /IM python.exe /FI "WINDOWTITLE eq *av-transcription*" 2>nul
   cd /d "%LOCALAPPDATA%\hermes\profiles\av-transcription"
   start /B cmd /c "hermes -p av-transcription gateway run -v"
   ```

## 凭据管理（重要）

`.env` 永远不进 git（被 `.gitignore` 排除）。仓库里只有 `.env.example` 模板。

需要保存的真实凭据（务必**单独**安全保存，不要写在任何文档里）：

- `FEISHU_APP_ID` / `FEISHU_APP_SECRET` —— 飞书开放平台 → 应用 → 凭证页
- `MINIMAX_CN_API_KEY` —— MiniMax 控制台 → API Keys
- `HERMES_GATEWAY_TOKEN` —— 每次运行 `setup` 时自动生成，恢复时也会自动生成新值

> 之前对话里贴过的 `EfnlN1CiMtUZZgET3CncMcAAKr6zxvDo`（APP_SECRET）已经留在对话历史里，
> 建议去飞书开放平台重置一次。

## 已采纳的规则（来自 SOUL.md）

| 编号 | 规则 | 采纳日期 |
|---|---|---|
| R1 | 转录完成后保存的 .md 文件，第一行（# 标题）必须是一句话总结（agent 调 LLM 生成 15-25 字钩子标题）；文件名也用一句话标题 | 2026-08-10 |
| R2 | 每次转录完成后，自动生成一份"视频号配文"风格的二创文案，保存到 `二创短视频文案/YYYYMMDD-转录结果＊二创＊<一句话标题>.md`（图书带货二创，提示词见 `scripts/secondary_create.py`） | 2026-08-10 |
| R3 | 每次转录完成后，再生成一份"通用二创"（4 版本：摘要/文章化/新媒体/视频脚本），保存到 `二创通用/YYYYMMDD-转录结果＊通用二创＊<一句话标题>.md`（提示词见 `scripts/general_create.py`） | 2026-08-10 |

更多规则见 `hermes-profile/SOUL.md`。

## 历史搭建记录

- 2026-08-09：创建 `av-transcription` profile，飞书 bot 接通（私聊 + 群聊）
- 2026-08-09：修复 `base_url`（`/v1` → `/anthropic`）和 `FEISHU_GROUP_POLICY=open`
- 2026-08-10：用 `faster-whisper base` (CPU) 转录首个 mp3，1877 字 / 76 秒
- 2026-08-10：采纳 R1 规则（标题一句话总结）
- 2026-08-10：仓库初始化
