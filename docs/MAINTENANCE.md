# 音视频转录 Agent 维护手册

> 最后更新: 2026-08-11 (813a024)

## 概述

Hermes 独立 profile (`av-transcription`), 通过飞书 bot **音视频转录agent** 对外服务.
私聊/群聊可触发. 用户发 mp3/mp4, agent 自动跑完整流水线 (R1+R2+R3+R4+R6).

## 已采纳规则 (R1-R6)

| 编号 | 规则 | 实现 | 产物命名 |
|---|---|---|---|
| R1 | 转录后一句话作标题 + 文件名 | `scripts/transcribe.py: generate_r1_title()` | `<title>.md` |
| R2 | 视频号配文二创 (默认 A=视频号图书带货) | `scripts/secondary_create.py` | `R2-视频号-<title>.md` |
| R2.B | 小红书风 (干货清单 + emoji) | 同上, 加 [style] B | `R2-小红书-<title>.md` |
| R2.C | 抖音风 (短句节奏 + 钩子) | 同上, 加 [style] C | `R2-抖音-<title>.md` |
| R2.D | 公众号风 (深度长文) | 同上, 加 [style] D | `R2-公众号-<title>.md` |
| R3 | 通用二创 (4 版本: 摘要/文章/短文/脚本) | `scripts/general_create.py` | `R3-<title>.md` |
| R4 | 双语电影质感封面 prompt (中文 9:16 + English 16:9) | `scripts/image_prompt.py` | `R4-<title>.md` |
| R5 | 脚本层 secret 自动脱敏 + .env 监控 + commit 前 secret 扫描 | `scripts/_common.py: mask_secret`, `scripts/monitor_env.py`, `scripts/check_secrets.py` | - |
| R6 | 二创后字幕排版 (每行 <=8 字, 无标点) | `scripts/subtitle_format.py` | `R6-<title>.md` |

**R4 完整说明**:
- 输入: 转录 .md (R1 输出)
- 输出: 单条完整中文 9:16 竖版封面 prompt + 完整 English 16:9 cinematic prompt (含 negative + parameters)
- 智能判定:
  - 类型一【主体聚焦向】(人物/核心物): 背影/侧颜/局部肢体, 严禁露正脸
  - 类型二【宏大叙事向】(环境/意象/空间): 无人物, 超广角/纵深透视
- 适配工具:
  - 中文版 → 即梦 / 可灵 / 通义万相 (国内, 适合图上写中文主副标题)
  - 英文版 → Midjourney / DALL-E 3 / Stable Diffusion (国际, 5 frames cinematic)

**R2 风格映射** (新增, 用于 _SHORT_NAME):
```
A → 视频号 (图书带货)
B → 小红书 (干货清单 + emoji)
C → 抖音 (短句节奏 + 钩子)
D → 公众号 (深度长文)
```

## 产物命名规则 (R813a024 后)

```
transcriptions/<title>.md                  R1  (一句话标题)
二创短视频文案/R2-<风格>-<title>.md       R2  (4 风格可选, A 视频号 12 个)
二创通用/R3-<title>.md                    R3  (4 版本: 摘要/文章/短文/脚本)
生图提示词/R4-<title>.md                  R4  (双语电影质感封面)
字幕/R6-<title>.md                        R6  (每行 <=8 字, 无标点)
```

**注意**:
- R3 末尾会自动整合 R4 完整内容 (用 `## R4 生图提示词（双语）` 区块)
- title 来自 R1 一句话标题, 经 `safe_filename` 过滤 Windows 非法字符
- 12 个转录 = 12 个 R1 + 12 个 R3 + 12 个 R4 + 12 个 R6 = 48 个核心产物
- R2 因 4 风格可选, 实际数量 = 12~48 个 (默认仅跑 A 风格)

## 项目结构

```
音视频转录/
├── README.md                          # 用户视角快速上手
├── docs/MAINTENANCE.md                # 本文件 (维护者视角)
├── .env.example                       # 凭据模板 (真 .env 不入 git)
├── hermes-profile/                    # Hermes profile 关键文件
│   ├── SOUL.md                        # 角色定义 + 已采纳规则
│   ├── config.yaml                    # 模型/平台配置
│   ├── profile.yaml                   # profile 元数据
│   ├── .no-bundled-skills             # 标记
│   └── restore.bat                    # 一键恢复
├── scripts/                           # 核心脚本
│   ├── _common.py                     # 共享: call_llm / safe_filename / mask_secret / echo_env
│   ├── transcribe.py                  # R1: whisper base CPU + 自动 R2 + R6 链式 (R6 实际有 bug, 需手动)
│   ├── batch_transcribe.py            # 批量转录
│   ├── secondary_create.py            # R2: 视频号配文二创 (A/B/C/D 4 风格, [style] 第二参数)
│   ├── general_create.py              # R3: 通用二创 4 版本
│   ├── image_prompt.py                # R4: 双语电影质感封面 prompt
│   ├── subtitle_format.py             # R6: 字幕排版
│   ├── integrate_r4.py                # 把 R4 整合到 R3 末尾 (已内置在 R3 处理)
│   ├── monitor_env.py                 # .env 访问监控
│   └── check_secrets.py               # commit 前手动 secret 扫描 (Windows 上替代 Git hook)
├── transcriptions/                    # R1 输出 (12)
├── 二创短视频文案/                    # R2 输出 (12 A 风格)
├── 二创通用/                          # R3 输出 (12, 末尾含 R4 整合)
├── 生图提示词/                        # R4 输出 (12, 独立副本)
├── 字幕/                              # R6 输出 (12)
└── transcribe_work/                   # 临时工作目录 (git ignored, 含原 mp3)
```

## 完整链路 (transcribe.py 自动调用)

```
mp3/mp4 → faster-whisper base (CPU) → R1 一句话标题 → transcriptions/<title>.md
                                       ↓
                                ┌──────┴──────┐
                                ↓             ↓
                          R2 视频号配文    R3 通用二创
                          (default A)     (4 版本)
                                ↓             ↓
                          二创短视频文案/    二创通用/
                                           (末尾整合 R4)
                                               ↓
                                          R4 双语封面
                                             ↓
                                          生图提示词/
                                ↓
                          R6 字幕排版
                                ↓
                              字幕/
```

**注**:
- transcribe.py 只自动链式触发 R2 + R6, R3 + R4 需手动跑
- R3 通过 `scripts/integrate_r4.py` 自动把 R4 追加到 R3 末尾
- R6 自动触发有 bug (transcribe.py 底部 try 块引用 main() 局部 out_md, 永远 NameError), 需手动跑

## 手动工作流

```bash
# === 完整单文件流水线 ===
python scripts/transcribe.py "transcribe_work/<audio>.mp3"            # R1 + 自动 R2 A + R6 (但 R6 失败)
python scripts/secondary_create.py "transcriptions/<x>.md"            # 已自动, skip
python scripts/secondary_create.py "transcriptions/<x>.md" "B"        # R2 B 风格 (可选)
python scripts/general_create.py "transcriptions/<x>.md"              # R3 (4 版本, 末尾自动整合 R4)
python scripts/image_prompt.py "transcriptions/<x>.md"                # R4 双语
python scripts/subtitle_format.py "transcriptions/<x>.md"             # R6 手动 (transcribe.py 自动链有 bug)

# === 批量 ===
python scripts/batch_transcribe.py "D:\音频目录"                       # 批量转录
python scripts/secondary_create.py                                     # 批量 R2 A (用 sys.argv[1] 不传 = 全部 transcriptions)
python scripts/general_create.py                                        # 批量 R3
python scripts/image_prompt.py                                          # 批量 R4
python scripts/subtitle_format.py                                       # 批量 R6

# === 安全 ===
python scripts/check_secrets.py --all         # 扫工作区
python scripts/check_secrets.py --staged-only  # 扫 staged
python scripts/monitor_env.py                  # 检查 .env 状态
python scripts/monitor_env.py --watch          # 持续监控
```

## 添加新规则 (R7+)

1. 在用户对话里确定规则 (R7 描述 + 触发场景 + 实现位置)
2. 加进 `hermes-profile/SOUL.md` 已采纳规则区, 格式:
   ```
   ### Rn. 规则名 (已采纳 YYYY-MM-DD)
   简短描述. 路径 / 文件名 / 触发时机 / 形式 / 核心要求.
   ```
3. 需要代码 → 写到 `scripts/`, 命名规范 `scripts/<rule>.py`
4. 改 `scripts/transcribe.py` 加链式调用 (修复 R6 那个 bug 也算 R7 工作)
5. 同步更新 `docs/MAINTENANCE.md` 规则表 + 项目结构
6. 同步更新 `README.md` 规则表
7. check_secrets + commit + push

## 升级模型

- **faster-whisper**: 改 `scripts/transcribe.py` 里 `model_size = "base"` 为 `small` / `medium` / `large-v3`
- **LLM**: 改 `scripts/_common.py` 的 `DEFAULT_MODEL = "MiniMax-M3"`
- **双 R4 prompt 模板**: 改 `scripts/image_prompt.py` 的 `PROMPT` 常量

## 常见故障

- **bot 不回复**: `tail -f logs/agent.log`, 看 Lark connected / 404 / 401
- **模型 404**: `config.yaml` 的 `base_url` 应该是 `https://api.minimaxi.com/anthropic`
- **API key 错**: `cat %LOCALAPPDATA%\hermes\profiles\av-transcription\.env` 检查 `MINIMAX_CN_API_KEY`
- **Secret 误 commit**: `git log --all` 找 + `git reset --hard HEAD~1` + force push + 立刻去平台重置
- **R6 自动链失败**: transcribe.py 底部 R6 块有 bug, 用 `subtitle_format.py` 手动跑
- **R4 mark 符被 LLM 拆换行**: 已用 `[CN_BLOCK_START]...[CN_BLOCK_END]` 长标记符, 不会断行
- **R2 跑默认风格**: 不传 [style] 默认 A (视频号), 输出 `R2-视频号-X.md`

## 修改 SOUL.md

1. 改 hermes profile 实例: `%LOCALAPPDATA%\hermes\profiles\av-transcription\SOUL.md`
2. 同步到 git: `音视频转录/hermes-profile/SOUL.md`
3. `git add . && git commit -m "..." && git push origin main`
4. 重启 gateway 让 agent 重读 SOUL:
   ```cmd
   taskkill /F /IM python.exe /FI "WINDOWTITLE eq *av-transcription*" 2>nul
   cd /d "%LOCALAPPDATA%\hermes\profiles\av-transcription"
   set HERMES_HOME=%LOCALAPPDATA%\hermes\profiles\av-transcription
   start /B cmd /c "hermes -p av-transcription gateway run -v"
   ```

## 备份

- **git 仓库本身** = SOUL.md + scripts + 部分产物 (66 个 .md)
- **不入 git**: 真实 `.env` (在 `%LOCALAPPDATA%\hermes\profiles\av-transcription\.env`), 单独安全存储
- **本地工作目录**: `transcribe_work/` (原 mp3 大文件, git ignored)

## 安全

- `.env` 权限 0600 (Windows: `icacls .env /inheritance:r /grant:r "%USERNAME%":(R,W)`)
- SSH key: 600
- Secret 不贴对话, 贴了就当泄露, 立即重置
- commit 前必跑 `python scripts/check_secrets.py --staged-only`

## 最近重要 commit

- `813a024` refactor: 重命名 4 个产物目录 + 删旧 R2
- `7a1a2ef` cleanup: 删 6 个 8/10 旧 R3
- `e3ce26b` feat(integrate): R4 整合到 R3 末尾
- `360a854` feat(R4): 双语版 (中文 9:16 + English 16:9)
- `75aa58d` feat(R4): 升级电影质感短视频封面视觉设计师