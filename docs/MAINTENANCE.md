# 音视频转录 Agent 维护手册

## 概述

Hermes 独立 profile (av-transcription), 通过飞书 bot 音视频转录agent 服务. 用户发 mp3/mp4, agent 自动转录 + 二创 + 字幕 + 生图.

## 已采纳规则 (R1-R6)

| 编号 | 规则 | 实现 |
|---|---|---|
| R1 | 转录后一句话作标题 + 文件名 | scripts/transcribe.py: generate_r1_title() |
| R2 | 二创 (视频号图书带货风格, 默认; A/B/C/D 4 风格) | scripts/secondary_create.py |
| R3 | 通用二创 (4 版本: 摘要/文章/短文/脚本) | scripts/general_create.py |
| R4 | 基于 R3 D 脚本生成生图提示词 | scripts/image_prompt.py |
| R5 | 脚本层 secret 自动脱敏 + .env 监控 | scripts/_common.py: mask_secret, scripts/monitor_env.py |
| R6 | 二创后字幕排版 (<=8 字, 无标点) | scripts/subtitle_format.py |

## 项目结构

- hermes-profile/ - Hermes profile 关键配置 (SOUL.md, config.yaml, profile.yaml, restore.bat)
- scripts/ - 核心脚本 (transcribe.py / secondary_create.py / general_create.py / image_prompt.py / subtitle_format.py / _common.py / batch_transcribe.py / monitor_env.py / check_secrets.py)
- transcriptions/ - R1 输出
- 二创短视频文案/ - R2 输出
- 二创通用/ - R3 输出
- 生图提示词/ - R4 输出
- 字幕/ - R6 输出
- docs/MAINTENANCE.md - 本文件

## 完整链路 (transcribe.py 自动调用)

mp3 -> faster-whisper base (CPU, ~50s/8min) -> R1 一句话标题 -> transcriptions/
       -> R2 -> 二创短视频文案/
       -> R3 -> 二创通用/
       -> R6 -> 字幕/

## 手动工作流

```
python scripts/transcribe.py "D:\音频.mp3"
python scripts/batch_transcribe.py "D:\音频目录"        # base
python scripts/batch_transcribe.py "D:\音频目录" medium
python scripts/secondary_create.py transcriptions/<x>.md --style A
python scripts/secondary_create.py transcriptions/<x>.md --style B
python scripts/general_create.py transcriptions/<x>.md
python scripts/image_prompt.py transcriptions/<x>.md
python scripts/subtitle_format.py transcriptions/<x>.md
python scripts/check_secrets.py             # commit 前 secret 扫描
python scripts/check_secrets.py --all
python scripts/monitor_env.py              # 检查 .env 状态
python scripts/monitor_env.py --watch      # 持续监控
```

## 修改 SOUL.md

1. 改 hermes profile 实例: ~/AppData/Local/hermes/profiles/av-transcription/SOUL.md
2. 同步到 git: 音视频转录/hermes-profile/SOUL.md
3. git add . && git commit -m "..."
4. 重启 gateway 让 agent 重读 SOUL:
   ```
   taskkill /F /IM python.exe /FI "WINDOWTITLE eq *av-transcription*" 2>nul
   cd /d "%LOCALAPPDATA%\hermes\profiles\av-transcription"
   set HERMES_HOME=%LOCALAPPDATA%\hermes\profiles\av-transcription
   start /B cmd /c "hermes -p av-transcription gateway run -v"
   ```

## 添加新规则 (R7+)

1. 在用户对话里确定规则
2. 加进 SOUL.md 已采纳规则区, 格式:
   ```
   ### Rn. 规则名 (已采纳 YYYY-MM-DD)
   简短描述. 路径 / 文件名 / 触发时机 / 形式 / 核心要求.
   用户已确认, 永久生效.
   ```
3. 需要代码 -> 写到 scripts/ 加新脚本
4. 改 transcribe.py 加链式调用
5. README + commit + push

## 升级模型

- faster-whisper: 改 scripts/transcribe.py 里 model_size = "base" 为目标值 (medium / large-v3)
- LLM: 改 scripts/_common.py 的 DEFAULT_MODEL = "MiniMax-M3"

## 常见故障

- bot 不回复: tail -f logs/agent.log, 看 Lark connected / 404 / 401
- 模型 404: config.yaml 的 base_url 应该是 https://api.minimaxi.com/anthropic
- API key 错: .env 里 MINIMAX_CN_API_KEY 检查
- Secret 误 commit: git log --all 找 + git reset --hard HEAD~1 + force push + 立刻去平台重置

## 备份

- git 仓库本身 = SOUL.md + scripts + 部分产物备份
- .env 不入 git, 单独安全存储 (1Password / Bitwarden)

## 安全

- .env 权限 0600 (Windows: icacls)
- SSH key: 600
- secret 不贴对话, 贴了就当泄露, 立即重置