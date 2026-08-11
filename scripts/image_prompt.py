"""
生图提示词脚本（R4）— 双语电影质感版
输入：转录 .md 文件
输出：生图提示词/YYYYMMDD-生图提示词＊<title>.md
每份产物包含两个独立完整 prompt:
  - 中文 9:16 竖版封面 (即梦/可灵/通义万相)
  - English 16:9 cinematic frames (MJ/DALL-E 3/SD)
"""
import re, sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import call_llm, safe_filename_for_md, REPO

TRANS_DIR = REPO / "transcriptions"
OUT_DIR = REPO / "生图提示词"

PROMPT = """你是顶尖的电影质感视觉设计师 + 跨平台 AI 绘图专家。深度解析用户提供的短视频文案，同时生成 2 段独立完整的 AI 绘图提示词（一中文一英文，分别适配国内 / 国际工具）。

输入：短视频文案（标题 + 段落正文）

【中文 9:16 竖版封面 — 适配即梦 / 可灵 / 通义万相】

封面排版规范：
- 画面比例 9:16 竖版
- 顶部文字叠加：主标题 6-15 字居中放画面上 3/7 区域；副标题（主标题的延伸补充，内容不重复，字体较小）紧贴主标题下方居中
- 文字区域必须用暗化遮罩 / 投影 / 背景留白处理，确保复杂背景下依然清晰
- 严禁提及书籍，严禁推销带货词汇

主体判定（必选其一）：
- 类型一【主体聚焦向】：人物仅展示背影 / 侧颜 / 局部肢体，严禁露正脸。服饰质感匹配职业身份。场景：与其身份呼应的深度背景
- 类型二【宏大叙事向】：不出现具体人物，超广角或极度纵深透视，强调"境"的空间规模感

电影级光影（严禁平庸光线）：伦勃朗光 / 戏剧化逆光 / 丁达尔效应 / 冷暖色温对比
高级色调（拒绝高饱和高亮度）：青橙调 / 黑金调 / 莫兰迪色系 / 深邃暗调
纹理细节（4K/8K 摄影级）：雨水打湿路面 / 金属磨损 / 烟雾流动 / 织物纤维
- 历史题材优先 cinematic / oil painting style / Chinese ink wash

中文版硬性约束：
- 必须包含：比例 9:16、顶部 3/7 标题区 + 主副标题具体字样、主体描述、光影、色调、纹理细节
- 严禁露正脸 / 严禁书籍 / 严禁带货 / 严禁高饱和高亮度
- 中文文字必须直接出现（如「血缘越近，越要算清」）

【English 16:9 Cinematic — 适配 Midjourney / DALL-E 3 / Stable Diffusion】

构图与排版：
- 16:9 横屏，cinematic frame
- 5 个分镜叙事：钩子 (0-5s) + 3 分段 + 结尾 CTA
- 主标题 / 副标题在画面顶部用衬线 / 黑体（用软件后期加，不在 prompt 里强调文字渲染）

主体判定（与中文版一致）：
- 类型一：人物仅背影 / 侧颜 / 局部（hands, shoulders, walking feet, no frontal face）
- 类型二：ultra wide angle / extreme perspective / metaphor space, no human figure

光影（cinematic lighting）：Rembrandt light / dramatic backlight / Tyndall effect / cool-warm contrast
色调（refined palette，no high saturation）：teal-orange / black-gold / Morandi / deep dark mood
纹理（4K/8K photo-grade）：rain on asphalt reflections / metal wear / smoke flow / fabric texture
- 历史题材用：cinematic, oil painting style, Chinese ink wash, Tang Dynasty Hanfu, Song Dynasty robes 等

英文版硬性约束：
- 全部英文，无任何中文字符
- 必须包含 positive prompt（80-150 词）+ negative prompt（10-20 词）+ parameters（--ar 16:9, --stylize 600 --v 6.1）
- 不得出现 "image of", "picture of" 等冗余词
- 人名/年代/地标用英文拼写（Tang Dynasty, Li Shimin, 626 AD, Han Dynasty, etc.）
- 历史服饰用朝代英文（Tang hanfu, Song dynasty robe, Ming changshan 等）

【执行流程】
1. 通读文案，理解核心受众与情感内核
2. 判定类型（类型一 or 类型二，两版一致）
3. 创作主副标题（中文 6-15 字 / 英文短标题）
4. 分别按中文版和英文版规范输出

【输出格式 - 严格】
你的输出必须是 2 个代码块，用以下标记符**完整不换行地**包裹（不要在 <<< 之间插入换行 / 空格）：

[CN_BLOCK_START]9:16 竖版构图。[中文 prompt 全文 300-500 字, 句号逗号分隔, 直接包含主副标题具体字样][CN_BLOCK_END]

[EN_BLOCK_START]Positive prompt: [...80-150 词英文...]\nNegative prompt: [...10-20 词...]\nParameters: --ar 16:9 --stylize 600 --v 6.1[EN_BLOCK_END]

硬性输出约束：
- 只输出 2 个代码块，不要任何其他内容（不要解释、不要标题、不要段落）
- [CN_BLOCK_START] / [CN_BLOCK_END] / [EN_BLOCK_START] / [EN_BLOCK_END] 标记符必须**完整且不换行**
- 标记符之间不要空行
- 不要输出 markdown ## 标题
- 不要寒暄
- 即使 prompt 内容很长，也必须用 2 个代码块包裹，不能拆成多个"""


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


def parse_bilingual(raw: str) -> tuple[str, str]:
    """用更鲁棒的方式 split CN 和 EN 块"""
    # 优先: [CN_BLOCK_START]...[CN_BLOCK_END] / [EN_BLOCK_START]...[EN_BLOCK_END]
    cn = re.search(r"\[CN_BLOCK_START\](.+?)\[CN_BLOCK_END\]", raw, re.DOTALL)
    en = re.search(r"\[EN_BLOCK_START\](.+?)\[EN_BLOCK_END\]", raw, re.DOTALL)
    if cn and en:
        return cn.group(1).strip(), en.group(1).strip()
    # fallback: 老格式 <<<CN>>> / <<<EN>>> 容忍换行
    cn = re.search(r"<<<[\s\n]*CN[\s\n]*>>>(.+?)(?=<<<[\s\n]*EN[\s\n]*>>>|$)", raw, re.DOTALL)
    en = re.search(r"<<<[\s\n]*EN[\s\n]*>>>(.+)$", raw, re.DOTALL)
    if cn and en:
        return cn.group(1).strip(), en.group(1).strip()
    # 极端 fallback: 整个 raw 当 CN
    return raw.strip(), "(English variant not generated)"


def image_prompt(trans_md: Path) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    title, body = read_transcription(trans_md)
    safe_title = safe_filename_for_md(title)
    date_prefix = datetime.now().strftime("%Y%m%d")
    out_name = f"{date_prefix}-生图提示词＊{safe_title}.md"
    out_path = OUT_DIR / out_name
    if out_path.exists():
        print(f"[skip] already exists: {out_path.name}", flush=True)
        return out_path

    user_prompt = (
        f"请为以下短视频文案同时生成中文 9:16 竖版封面 + English 16:9 cinematic 双语 prompt。\n\n"
        f"原标题（R1 一句话总结）：{title}\n\n"
        f"文案正文：\n{body[:3000]}\n\n"
        f"严格按 [CN_BLOCK_START]...[CN_BLOCK_END] / [EN_BLOCK_START]...[EN_BLOCK_END] 格式输出, 不要 markdown 标题, 不要解释, 不要寒暄。"
    )
    print(f"[R4] {trans_md.name} -> {out_name}", flush=True)
    raw = call_llm(PROMPT, user_prompt, max_tokens=3000).strip()
    print(f"[llm] {len(raw)} chars", flush=True)

    cn_prompt, en_prompt = parse_bilingual(raw)

    header = (
        f"# 生图提示词 · {title}\n\n"
        f"- 源文件：`{trans_md.name}`\n"
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- 模型：_common.DEFAULT_MODEL\n"
        f"- 风格：电影质感（伦勃朗光 / 戏剧化逆光 / 丁达尔 / 冷暖对比）\n"
        f"- 色调：青橙调 / 黑金调 / 莫兰迪 / 深邃暗调\n\n"
        f"---\n\n"
        f"## 中文 9:16 竖版封面（即梦 / 可灵 / 通义万相）\n\n"
        f"> 顶部 3/7 区域主副标题（主 6-15 字 / 副作延伸），暗化遮罩保证可读\n\n"
        f"```\n{cn_prompt}\n```\n\n"
        f"---\n\n"
        f"## English 16:9 Cinematic（Midjourney / DALL-E 3 / Stable Diffusion）\n\n"
        f"> 5 frames cinematic narrative (hook + 3 segments + CTA)\n\n"
        f"```\n{en_prompt}\n```\n"
    )
    out_path.write_text(header, encoding="utf-8")
    print(f"[wrote] {out_path} ({out_path.stat().st_size:,} bytes)", flush=True)
    return out_path


def main():
    if len(sys.argv) < 2:
        targets = sorted(TRANS_DIR.glob("*.md")) if TRANS_DIR.is_dir() else []
    else:
        targets = [Path(sys.argv[1])]
    if not targets:
        print(f"[no targets] {TRANS_DIR} 空", flush=True)
        return
    for t in targets:
        try:
            image_prompt(t)
        except Exception as e:
            print(f"[err] {t.name}: {e}", flush=True)


if __name__ == "__main__":
    main()