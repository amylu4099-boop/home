"""
通用二创脚本（R3）
输入：转录 .md 文件（默认处理 transcriptions/ 目录里所有）
输出：二创通用/ 目录里的 .md 文件，命名同 R2
依赖：_common.py
"""
import sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import call_llm, safe_filename_for_md, REPO, TRANS_DIR

GENERAL_DIR = REPO / "二创通用"
PROMPT = r"""你是内容编辑，擅长把音频/视频转录文字改写成多版本结构化文本。

输入：一份转录 .md 文件（标题 + 元信息 + 正文段落）。
输出：4 个版本，按顺序输出，用清晰的 ## 标题分隔：

## 版本 A：核心摘要（150-250 字）
一句话点出核心信息 → 2-3 句展开关键事实 → 一句话点出为什么值得关心。

## 版本 B：结构化文章（800-1200 字）
标题（一句钩子，不与 R1 标题重复）→ 引言（背景/冲突/悬念）→ 主体（按逻辑分 3-5 段）→ 结语（升华或呼应开头）。
风格：书面但不学术，像公众号深度长文。

## 版本 C：新媒体短文（150-300 字）
钩子开头 + 3-5 个 emoji bullet 要点 + 互动收尾（提问/求赞/求关注）。
风格：适合朋友圈/小红书/视频号分发。

## 版本 D：视频脚本大纲（5-8 行）
开场 5 秒钩子（视觉+听觉+字幕）→ 3-5 个分段（每段一句话点出主题+节奏提示）→ 结尾 5 秒 CTA。

硬性规则（贯穿所有版本）：
- 不得编造原文没有的事实；不确定的信息直接跳过
- 保留所有精确数据（年份、尺寸、数量、人名、地名）
- 不得使用"在这个充满...的世界里"、"让我们一起"、"值得一提的是"、"不仅...更..." 等书面腔
- 不得使用 AI 套话（"总而言之"、"综上所述"、"值得注意的是"）
- 口语化优先，中老年人不费劲能听懂
- 原文专有名词的常见错字（刘秀/流秀、阴丽华/阴里华 等）必须使用正确版本
- 每个版本字数严格在标注区间内

Step 0：原文纠错（列出修正项）
Step 1：分别说明每个版本的字数与策略
Step 2：依次输出 A / B / C / D 完整内容（每个用 markdown ## + 代码块包裹）
"""


def read_transcription(md_path: Path) -> tuple[str, str]:
    text = md_path.read_text(encoding="utf-8")
    title_match = re.match(r"^#\s*(.+?)\s*$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else md_path.stem
    body_start = text.find("---\n\n")
    if body_start >= 0:
        body_start += len("---\n\n")
        body = text[body_start:].strip()
    else:
        body = text
    return title, body


def make_filename(trans_md: Path, title: str) -> str:
    from datetime import datetime
    date_prefix = datetime.now().strftime("%Y%m%d")
    return "R3.md"


import re
import subprocess


def general_create(trans_md: Path) -> Path:
    title, body = read_transcription(trans_md)
    (GENERAL_DIR / title).mkdir(parents=True, exist_ok=True)
    out_name = make_filename(trans_md, title)
    out_path = (GENERAL_DIR / title) / out_name
    if out_path.exists():
        print(f"[skip] already exists: {out_path.name}", flush=True)
        return out_path

    from datetime import datetime
    user_prompt = (
        f"原标题：{title}\n\n"
        f"原文（已预纠错，以这个版本为准）：\n{body}\n\n"
        f"请按你的工作流输出 Step 0 / Step 1 / Step 2 四个版本。"
    )
    print(f"[R3] {trans_md.name} -> {out_name}", flush=True)
    raw = call_llm(PROMPT, user_prompt, max_tokens=4000)
    print(f"[llm] {len(raw)} chars", flush=True)

    header = (
        f"# 通用二创 · {title}\n\n"
        f"- 原文件：`{trans_md.name}`\n"
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- 模型：_common.DEFAULT_MODEL\n"
        f"- 风格：R3 通用二创（摘要 + 文章化 + 新媒体 + 视频脚本）\n\n"
        f"---\n\n"
    )
    out_path.write_text(header + raw, encoding="utf-8")
    print(f"[wrote] {out_path} ({out_path.stat().st_size:,} bytes)", flush=True)
    return out_path


def main():
    import subprocess
    if len(sys.argv) < 2:
        targets = sorted(TRANS_DIR.glob("*.md")) if TRANS_DIR.is_dir() else []
    else:
        targets = [Path(sys.argv[1])]
    if not targets:
        print(f"[no targets] {TRANS_DIR} 空", flush=True)
        return
    for t in targets:
        try:
            general_create(t)
        except Exception as e:
            print(f"[err] {t.name}: {e}", flush=True)


if __name__ == "__main__":
    main()
