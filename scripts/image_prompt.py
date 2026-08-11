"""
生图提示词脚本（R4）— 短视频封面版
输入：转录 .md 文件
输出：生图提示词/YYYYMMDD-生图提示词＊<title>.md
基于 R4 升级:
- 9:16 竖版短视频封面（适配即梦/可灵/通义万相）
- 智能判定 类型一（主体聚焦）or 类型二（宏大叙事）
- 顶部 3/7 区域主副标题（主 6-15 字, 副作延伸, 暗化遮罩保证可读）
- 电影级光影（伦勃朗/逆光/丁达尔/冷暖对比）
- 高级色调（青橙/黑金/莫兰迪/深邃暗调）
- 4K/8K 摄影级纹理（雨水/金属/烟雾/织物）
- 严禁露正脸/严禁书籍字眼/严禁带货词汇
- 输出 1 段完整中文提示词
"""
import re, sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import call_llm, safe_filename_for_md, REPO

TRANS_DIR = REPO / "transcriptions"
OUT_DIR = REPO / "生图提示词"

PROMPT = """你是顶尖的电影质感短视频封面视觉设计师。深度解析用户提供的短视频文案，生成 1 段完整中文 AI 绘图提示词（适配即梦 / 可灵 / 通义万相等国内工具）。

输入：短视频文案（标题 + 段落正文）
输出：1 段完整中文提示词（300-500 字）。仅输出提示词本身，不要任何解释、标题、分段标签、JSON。

【封面排版规范 - 严格强制】
- 画面比例：9:16 竖版
- 顶部文字叠加：主标题 6-15 字居中放画面上 3/7 区域；副标题（主标题的延伸补充，内容不重复，字体较小）紧贴主标题下方居中
- 文字区域必须用暗化遮罩 / 投影 / 背景留白处理，确保复杂背景下依然清晰
- 严禁提及书籍，严禁推销带货词汇

【主体判定 - 必选其一】

类型一【主体聚焦向】：文案核心是个人成长、职业身份、情感共鸣、单体产品、动植物
- 视觉中心：氛围感强的主体。若人物，仅展示背影 / 侧颜 / 局部肢体（握紧的手、行走的脚、肩膀轮廓），严禁露正脸
- 服饰质感：匹配职业身份（西装挺括 / 工服油污 / 冲锋衣机能感 / 皮肤纹理）
- 场景：与其身份呼应的深度背景（深夜写字楼、旷野日出、实验室微光）

类型二【宏大叙事向】：文案核心是社会现象、科技趋势、自然风光、城市变迁、哲学思考
- 视觉中心：不出现具体人物，以隐喻空间或标志性景观为视觉重心
- 构图：超广角或极度纵深透视（无限延伸的公路、云端建筑、深邃海底、错综电路森林）
- 氛围：强调"境"的空间规模感，视觉压迫或心理震撼

【电影级光影 - 严禁平庸】
- 布光：伦勃朗光 / 戏剧化逆光 / 丁达尔效应 / 冷暖色温对比光
- 色调：沉稳电影胶片色（青橙调 / 黑金调 / 莫兰迪色系 / 深邃暗调）
- 局部高光点亮：暖金色 / 霓虹光
- 拒绝高饱和高亮度

【纹理细节 - 4K/8K 摄影级】
- 雨水打湿路面的倒影
- 金属磨损
- 烟雾流动
- 织物纤维
- 真实物理质感

【执行流程 - 思考但不输出】
1. 通读文案，理解核心受众与情感内核
2. 判定类型（类型一 or 类型二）
3. 创作主副标题（主标题 6-15 字，爆款潜质一眼抓人；副标题作延伸）
4. 整合所有指令输出 1 段中文提示词

【硬性约束】
- 仅输出 1 段连贯中文提示词（约 300-500 字）
- 内部用逗号 / 句号分隔，逻辑流畅
- 必须包含：比例 9:16、顶部 3/7 标题区 + 主副标题具体字样、主体描述、光影、色调、纹理细节
- 严禁露正脸 / 严禁平庸光线 / 严禁高饱和高亮度 / 严禁书籍 / 严禁带货词汇
- 历史题材优先 cinematic / oil painting / Chinese ink wash 风格
"""


def read_transcription(md_path: Path) -> tuple[str, str]:
    """从转录 .md 抽 (title, body)"""
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
        f"请为以下短视频文案生成 1 段完整的电影质感封面中文提示词。\n\n"
        f"原标题（R1 一句话总结）：{title}\n\n"
        f"文案正文：\n{body[:3000]}\n\n"
        f"请严格按你的人物判定逻辑 + 9:16 竖版封面规范 + 电影级光影 + 摄影级纹理整合输出。"
    )
    print(f"[R4] {trans_md.name} -> {out_name}", flush=True)
    raw = call_llm(PROMPT, user_prompt, max_tokens=2000).strip()
    print(f"[llm] {len(raw)} chars", flush=True)

    header = (
        f"# 生图提示词 · {title}\n\n"
        f"- 源文件：`{trans_md.name}`\n"
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- 模型：_common.DEFAULT_MODEL\n"
        f"- 工具：即梦 / 可灵 / 通义万相（国内 AI 绘图）\n"
        f"- 比例：9:16 竖版（短视频封面）\n"
        f"- 风格：电影质感（伦勃朗光 / 戏剧化逆光 / 丁达尔 / 冷暖对比）\n"
        f"- 色调：青橙调 / 黑金调 / 莫兰迪 / 深邃暗调\n\n"
        f"---\n\n"
    )
    out_path.write_text(header + raw + "\n", encoding="utf-8")
    print(f"[wrote] {out_path} ({out_path.stat().st_size:,} bytes)", flush=True)
    return out_path


def main():
    if len(sys.argv) < 2:
        # 默认处理 transcriptions/ 目录里所有 .md
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