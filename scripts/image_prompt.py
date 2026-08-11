"""
生图提示词脚本（R4）— 分镜叙事版
输入：转录 .md 文件
输出：<title>/生图提示词.md (含 5-10 个分镜, 每张双语)
第 1 张: 9:16 竖版封面 (含主副标题)
第 2-10 张: 16:9 cinematic 分镜 (无文字)
"""
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import call_llm, REPO

TRANS_DIR = REPO / "transcriptions"

PROMPT = r"""你是顶尖的电影质感短视频视觉设计师。深度解析短视频文案，生成 5-10 张分镜叙事图，每张含中文 + 英文双语 prompt (适配即梦/可灵/通义万相 + Midjourney/DALL-E 3/SD)。

输入：短视频文案 (R1 转录: 标题 + 段落正文)
输出：5-10 个分镜块，每个分镜含完整双语 prompt

【分镜结构 - 必须 5-10 张】
- 分镜 1：钩子 (前 5 秒抓人) = 短视频封面，含主副标题
- 分镜 2 - N-1：主体情节 (按文案自然分 3-8 段)
- 分镜 N：结尾 CTA / 升华

【封面规范 (仅分镜 1)】
- 画面比例：9:16 竖版
- 顶部文字叠加：主标题 6-15 字居中放画面上 3/7 区域；副标题 (主标题的延伸，字体较小) 紧贴主标题下方居中
- 文字区域必须用暗化遮罩 / 投影 / 背景留白处理
- 严禁提及书籍，严禁推销带货词汇

【分镜规范 (分镜 2-N)】
- 无文字，纯画面
- 16:9 横屏 cinematic frame
- 视觉中心：类型一 (主体背影/侧颜/局部) 或 类型二 (无人物，隐喻空间)

【主体判定 - 必选其一，全片统一】
- 类型一【主体聚焦向】(人物/核心物)：
  * 视觉中心：氛围感强的主体。若人物仅展示背影 / 侧颜 / 局部肢体 (握紧的手/行走的脚/肩膀轮廓)，严禁露正脸
  * 服饰质感：匹配职业身份 (西装挺括/工服油污/冲锋衣机能感/皮肤纹理)
  * 场景：与其身份呼应的深度背景 (深夜写字楼/旷野日出/实验室微光)
- 类型二【宏大叙事向】(环境/意象/空间)：
  * 视觉中心：不出现具体人物，隐喻空间或标志性景观
  * 构图：超广角或极度纵深透视 (无限延伸的公路/云端之上的建筑/深邃的海底)
  * 氛围：强调"境"的空间规模感产生视觉压迫或心理震撼

【电影级光影 - 严禁平庸光线】
- 布光：伦勃朗光 / 戏剧化逆光 / 丁达尔效应 / 冷暖色温对比光
- 强明暗对比营造故事感

【高级色调 - 拒绝高饱和高亮度】
- 沉稳电影胶片色：青橙调 / 黑金调 / 莫兰迪色系 / 深邃暗调
- 局部高光点亮：暖金色 / 霓虹光

【纹理细节 - 4K/8K 摄影级】
- 雨水打湿路面的倒影 / 金属的磨损 / 烟雾的流动 / 织物的纤维
- 真实物理质感

【硬性约束】
- 必须输出 5-10 个分镜 (不要 1 张，不要 < 5 张，不要 > 10 张)
- 仅分镜 1 的中文 prompt 含主副标题具体字样
- 严禁露正脸 / 严禁书籍 / 严禁带货 / 严禁高饱和高亮度
- 历史题材优先 cinematic / oil painting style / Chinese ink wash
- 中文 prompt 100-200 词，句号逗号分隔
- English Positive prompt 80-150 词，Negative prompt 10-20 词
- 不得出现 "image of", "picture of" 等冗余词
- 人名/年代/地标用英文拼写 (Tang Dynasty, Li Shimin, 626 AD 等)

【输出格式 - 严格】
## 分镜 1：<中文场景名>
**画面叙事**（中文 1-2 句）：人物/场景/构图/光影
**中文 9:16 竖版封面**（即梦/可灵/通义万相）：
```
[完整中文 prompt, 100-200 词, 必须含主副标题具体字样]
```
**English 16:9 Cinematic**（MJ/DALL-E 3/SD）：
```
Positive prompt: [80-150 词]
Negative prompt: [10-20 词]
Parameters: --ar 16:9 --stylize 600 --v 6.1
```

(分镜 2-N 同上结构, 但中文版无主副标题, 改为分镜画面)

不要任何其他解释 / 标题 / 寒暄. 开头不要寒暄. 严格按上述格式输出 5-10 个 ## 分镜块."""


def read_transcription(md_path: Path) -> tuple:
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


def count_frames(raw: str) -> int:
    return len(re.findall(r"^##\s*分镜\s*\d+", raw, re.MULTILINE))


def image_prompt(trans_md: Path) -> Path:
    title, body = read_transcription(trans_md)
    out_path = (REPO / title) / "生图提示词.md"
    if out_path.exists():
        print(f"[skip] already exists: {title}/生图提示词.md", flush=True)
        return out_path

    user_prompt = (
        f"请为以下短视频文案生成 5-10 张电影质感分镜图, 每张含中文 + 英文双语 prompt。\n\n"
        f"原标题 (R1 一句话总结): {title}\n\n"
        f"文案正文:\n{body[:3500]}\n\n"
        f"请按 5-10 个 ## 分镜 N 块结构输出, 每块含 2 个代码块 (中文 9:16 + English 16:9)。"
        f"仅分镜 1 中文版含主副标题, 其他分镜中文版是纯画面 prompt。"
    )
    print(f"[R4] {trans_md.name} -> {title}/生图提示词.md", flush=True)
    raw = call_llm(PROMPT, user_prompt, max_tokens=8000).strip()
    frames = count_frames(raw)
    print(f"[llm] {len(raw)} chars, {frames} frames", flush=True)

    header = (
        f"# 生图提示词 · {title}\n\n"
        f"- 源文件: `{trans_md.name}`\n"
        f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- 模型: _common.DEFAULT_MODEL\n"
        f"- 风格: 电影质感 (伦勃朗光/戏剧化逆光/丁达尔/冷暖对比)\n"
        f"- 色调: 青橙调/黑金调/莫兰迪/深邃暗调\n"
        f"- 分镜数: {frames} 张 (按 5-10 张范围动态生成)\n"
        f"- 工具: 中文 9:16 -> 即梦/可灵/通义万相 | English 16:9 -> MJ/DALL-E/SD\n\n"
        f"---\n\n"
    )
    out_path.write_text(header + raw + "\n", encoding="utf-8")
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