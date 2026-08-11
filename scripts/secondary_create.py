"""
二创脚本（视频号配文风格）
依赖：transcribe.py 写出的 .md 转录文件
输出：C:\\Users\\Michael\\Desktop\\音视频转录\\二创短视频文案\\YYYYMMDD-转录结果＊二创＊<一句话标题>.md
"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import call_llm, safe_filename_for_md
from datetime import datetime

# 模型名（仅在 header 里展示用，真实 API 走 _common）
MODEL = "MiniMax-M3"

# 路径
REPO = Path(__file__).resolve().parent.parent
TRANS_DIR = REPO / "transcriptions"

# 二创提示词（用户给定的视频号配文二创专家角色）
"""
四种风格的视频文案二创专家。用户输入时会说"二创风格 A/B/C/D"或默认 A (视频号图书带货)。
所有版本都要"掐头去尾、重塑中段", 头尾一字不动, 中段深度重写。
"""


PROMPT_A = """你是图书带货类短视频文案二创专家（视频号风格）。拿到对标文案后深度重构：保留开头 3-4 句钩子 + 末尾转化闭环 (产品价值塑造 + 购买引导), 中段按 6 种策略重写。全文相似度 < 20%, 口语自然, 直接带货转化力。"""

PROMPT_B = """你是小红书种草文案二创专家。开头钩子保留原风格, 末尾"求互动"区 (求赞、求收藏、求评论、@好友) 一字不动, 中段改成"干货清单 + emoji"形式 (5-7 个要点, 每个 1-2 行, 配 1-2 个 emoji, 不能 emoji 堆砌)。风格: 亲切闺蜜口吻、第一人称、有"姐妹们/家人们"等口语词。"""

PROMPT_C = """你是抖音短视频文案二创专家。开头 3 秒强钩子必须原样保留 (否则划走), 中段改写成"短句节奏 + 反转/悬念/冲突点", 句式尽量短 (5-10 字一句), 末尾"互动引导" (评论引导 + 关注 + 点赞) 保留。风格: 快节奏、口语、情绪化、有"你猜怎么着/结果令人震惊"等钩子词。"""

PROMPT_D = """你是公众号深度长文二创专家。开头"故事化引子" 保留 (通常有具体场景/人物), 中段改成"金句 + 论据 + 案例"结构 (3-5 个论点, 每个 100-200 字), 末尾"互动 + 转发引导" 保留。风格: 理性深度、有思考、有数据/案例支撑、像一篇专栏。"""

STYLES = {
    "A": ("视频号配文 (图书带货)", PROMPT_A),
    "B": ("小红书风 (干货清单 + emoji)", PROMPT_B),
    "C": ("抖音风 (短句节奏 + 钩子)", PROMPT_C),
    "D": ("公众号风 (深度长文)", PROMPT_D),
}

_SHORT_NAME = {"A": "视频号", "B": "小红书", "C": "抖音", "D": "公众号"}




def read_transcription(md_path: Path) -> tuple[str, str, str]:
    """返回 (title, body, 元信息块)"""
    text = md_path.read_text(encoding="utf-8")
    # 提取 # 标题
    title_match = re.match(r"^#\s*(.+?)\s*$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else md_path.stem
    # 去掉标题 + header + --- 分隔
    body_start = text.find("---\n\n")
    if body_start >= 0:
        body_start += len("---\n\n")
        body = text[body_start:].strip()
    else:
        body = text
    return title, body, ""



# 转录常见错字 / 同音字纠错表（faster-whisper base 中文高频错）
_CORRECTIONS = [
    # 通用
    (r"流秀", "刘秀"),
    (r"流秀", "刘秀"),
    (r"郭盛通", "郭圣通"),
    (r"阴里华", "阴丽华"),
    (r"阴力华", "阴丽华"),
    (r"阴曆华", "阴丽华"),
    (r"军林天下", "君临天下"),
    (r"皇掌子", "皇长子"),
    (r"母一天下", "母仪天下"),
    (r"亡狼", "王郎"),
    (r"仇马", "筹码"),
    (r"百给", "白给"),
    (r"外生女", "外甥女"),
    (r"方华正盛", "芳华正茂"),
    (r"军联天下", "君临天下"),
    (r"登基称地", "登基称帝"),
    (r"清飘飘", "轻飘飘"),
    (r"心良了", "心凉了"),
    (r"加官进决", "加官进爵"),
    (r"邮化", "优化"),
    (r"刺骨的寒梁", "刺骨的寒凉"),
    (r"齐局", "棋局"),
    (r"楚军之位", "储君之位"),
    (r"善忠", "善终"),
    (r"安安冷冷", "安安稳稳"),
    (r"仅仅有条", "井井有条"),
]


def pre_correct(text: str) -> str:
    """把 faster-whisper 中文常见错字改成正确的（仅在送 LLM 前用，不动原文件）"""
    out = text
    for bad, good in _CORRECTIONS:
        out = re.sub(bad, good, out)
    return out


def secondary_create(trans_md: Path, style: str = "A") -> Path:
    """对单个转录 .md 做一次二创, 风格 A=视频号图书带货 B=小红书 C=抖音 D=公众号, 输出到 二创短视频文案/"""
    if style not in STYLES:
        raise ValueError(f"Unknown style: {style}. Use one of: {list(STYLES.keys())}")
    style_name, style_prompt = STYLES[style]

    title, body, _ = read_transcription(trans_md)
    (REPO / title).mkdir(parents=True, exist_ok=True)
    cleaned_body = pre_correct(body)
    # 文件名加风格后缀避免覆盖
    safe_title = safe_filename_for_md(title)
    date_prefix = datetime.now().strftime("%Y%m%d")
    out_name = f"{_SHORT_NAME[style]}.md"
    out_path = (REPO / title) / out_name
    if out_path.exists():
        print(f"[skip] already exists: {out_path.name}", flush=True)
        return out_path

    extra_instruction = (
        "如果原文没有「转化闭环区」（比如非图书带货内容），则跳过该规则，"
        "把原文最后 2-3 句作为「保留尾」处理即可。"
        if style == "A" else
        "请严格按你的风格执行: 中段深度重写, 但开头钩子 + 末尾互动区必须一字不动。"
    )
    user_prompt = (
        f"请对以下转录文案进行深度二创 (风格 {style}: {style_name})。\n\n"
        f"原标题：{title}\n\n"
        f"原文（已预纠错，以这个版本为准）：\n{cleaned_body}\n\n"
        f"按你的工作流程：Step 0 纠错 → Step 1 思路 + 字数 → Step 2 完整代码块。\n"
        f"{extra_instruction}"
    )

    print(f"[二创 {style}: {style_name}] {trans_md.name} -> {out_name}", flush=True)
    raw = call_llm(style_prompt, user_prompt)
    print(f"[llm] {len(raw)} chars", flush=True)

    header = (
        f"# 二创短视频文案 · {title}\n\n"
        f"- 风格: {style} ({style_name})\n"
        f"- 原文件：`{trans_md.name}`\n"
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- 模型：{MODEL} (anthropic messages API)\n\n"
        f"---\n\n"
    )
    out_path.write_text(header + raw, encoding="utf-8")
    print(f"[wrote] {out_path} ({out_path.stat().st_size:,} bytes)", flush=True)
    return out_path





def main():
    # usage: secondary_create.py [trans.md] [style]
    #   trans.md 留空 = 批量处理 transcriptions/ 里所有 .md
    #   style    留空 = A (视频号图书带货); 可选 A/B/C/D
    if len(sys.argv) < 2:
        targets = sorted(TRANS_DIR.glob("*.md")) if TRANS_DIR.is_dir() else []
        style = "A"
    else:
        targets = [Path(sys.argv[1])]
        style = sys.argv[2] if len(sys.argv) > 2 else "A"
    if style not in STYLES:
        raise SystemExit(f"[err] unknown style: {style}. valid: {list(STYLES.keys())}")
    if not targets:
        print(f"[no targets] {TRANS_DIR} 空", flush=True)
        return
    for t in targets:
        secondary_create(t, style=style)


if __name__ == "__main__":
    main()
