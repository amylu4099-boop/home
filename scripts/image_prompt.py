"""
生图提示词脚本（R4）
输入：R3 通用二创 .md 文件（包含 D 视频脚本部分，画面+节奏+旁白）
输出：生图提示词/YYYYMMDD-生图提示词＊<title>.md
提示词见下方 PROMPT，输出 Midjourney / DALL-E / SD 三家通用格式
"""
import re, sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import call_llm, safe_filename_for_md, REPO

GENERAL_DIR = REPO / "二创通用"
OUT_DIR = REPO / "生图提示词"

PROMPT = """你是短视频生图提示词专家，精通 Midjourney / DALL-E 3 / Stable Diffusion 三家通用语法。

输入：R3 通用二创里"版本 D：视频脚本大纲"的全文（含 0-5 秒钩子 + 3-5 个分段）。
任务：把每个分段的"画面"描述扩展成可直接喂给 AI 生图模型的英文提示词。

输出要求（按分段依次，每个分段一个 ## 块）：
## 场景 N：<简短中文名>
**画面叙事**（中文，1-2 句）：补充原画面描述缺的人物/构图/光影细节。
**正面提示词**（英文，30-80 词，逗号分隔）：主体 + 动作 + 场景 + 风格 + 光影 + 镜头 + 渲染参数（aspect 16:9, --ar 16:9 等）。
**反向提示词**（英文，10-20 词）：lowres, bad anatomy, blurry, watermark, text 之类。
**风格后缀**（英文）：cinematic, photorealistic, anime, ink wash painting 之一。
**参数建议**：aspect ratio, stylize, quality 等。

硬性规则：
- 提示词必须英文（Midjourney/DALL-E 不吃中文）
- 不得编造原脚本没有的人物/场景
- 人物描述用历史服饰/朝代特征（汉服、宋制、唐制、明制 等）
- 比例统一 16:9（横屏视频封面/分镜）
- 风格优先 cinematic / oil painting style / Chinese ink wash（与历史主题契合）
- 不得在提示词里出现 "image of", "picture of" 等冗余词
- 数字、人名、地名、年代用原文拼写（如 Tang Dynasty, Li Shimin, 626 AD）

Step 0：列原脚本里每个分段的"画面"原文
Step 1：每段的画面叙事补充
Step 2：依次输出 N 个 ## 场景（用代码块包裹每个完整场景）"""


def read_d_section(general_md: Path) -> tuple[str, str]:
    """从 R3 .md 里抽出 ## 版本 D 部分 + 原始转录 title
    R3 文件名格式: YYYYMMDD-转录结果＊通用二创＊<原标题>.md
    """
    text = general_md.read_text(encoding="utf-8")
    # 优先从 R3 文件名抽原标题 (避免 R3 头部 "通用二创 · " 前缀污染)
    parts = general_md.stem.split("＊")
    if len(parts) >= 3:
        title = parts[-1].strip()
    else:
        title_match = re.match(r"^#\s*(.+?)\s*$", text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else general_md.stem
    m = re.search(r"##\s*版本 D.*?(?=\n##\s|\Z)", text, re.DOTALL)
    if not m:
        return title, ""
    return title, m.group(0).strip()


def image_prompt(general_md: Path) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    title, d_section = read_d_section(general_md)
    if not d_section:
        print(f"[skip] {general_md.name} 没有版本 D", flush=True)
        return None
    safe_title = safe_filename_for_md(title)
    date_prefix = datetime.now().strftime("%Y%m%d")
    out_name = f"{date_prefix}-生图提示词＊{safe_title}.md"
    out_path = OUT_DIR / out_name
    if out_path.exists():
        print(f"[skip] already exists: {out_path.name}", flush=True)
        return out_path

    user_prompt = (
        f"请把以下 R3 D 视频脚本转换成生图提示词。\n\n"
        f"原标题：{title}\n\n"
        f"D 段原文：\n{d_section}\n\n"
        f"按你的 Step 0 → Step 1 → Step 2 流程输出完整结果。"
    )
    print(f"[R4] {general_md.name} -> {out_name}", flush=True)
    raw = call_llm(PROMPT, user_prompt, max_tokens=4000)
    print(f"[llm] {len(raw)} chars", flush=True)

    header = (
        f"# 生图提示词 · {title}\n\n"
        f"- 原文件：`{general_md.name}`\n"
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- 模型：_common.DEFAULT_MODEL\n"
        f"- 风格：Midjourney / DALL-E 3 / Stable Diffusion 通用\n"
        f"- 比例：16:9 (横屏)\n\n"
        f"---\n\n"
    )
    out_path.write_text(header + raw, encoding="utf-8")
    print(f"[wrote] {out_path} ({out_path.stat().st_size:,} bytes)", flush=True)
    return out_path


def main():
    if len(sys.argv) < 2:
        # 默认处理 二创通用/ 目录里所有 .md
        targets = sorted(GENERAL_DIR.glob("*.md")) if GENERAL_DIR.is_dir() else []
    else:
        targets = [Path(sys.argv[1])]
    if not targets:
        print(f"[no targets] {GENERAL_DIR} 空", flush=True)
        return
    for t in targets:
        try:
            image_prompt(t)
        except Exception as e:
            print(f"[err] {t.name}: {e}", flush=True)


if __name__ == "__main__":
    main()