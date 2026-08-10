"""
二创脚本（视频号配文风格）
依赖：transcribe.py 写出的 .md 转录文件
输出：C:\\Users\\Michael\\Desktop\\音视频转录\\二创短视频文案\\YYYYMMDD-转录结果＊二创＊<一句话标题>.md
"""
import os, json, urllib.request, re, sys
from pathlib import Path
from datetime import datetime

# API 配置
API_BASE = "https://api.minimaxi.com/anthropic"
MODEL = "MiniMax-M3"
MAX_TOKENS = 4000

# 路径
REPO = Path(__file__).resolve().parent.parent
TRANS_DIR = REPO / "transcriptions"
OUT_DIR = REPO / "二创短视频文案"

# 二创提示词（用户给定的视频号配文二创专家角色）
PROMPT = r"""Role：图书类短视频文案二创专家

基本画像
语言：中文
核心能力：专攻图书带货类短视频文案的深度二创，使用"掐头去尾、重塑中段"策略。输出要求：保留原视频的爆款基因（开头钩子+转化结尾），同时实现全文相似度低于20%。文案风格必须口播自然、情绪饱满、具备直接带货转化力。

核心任务
拿到对标文案后，你需要完成一次深度重构。黄金开头、互动钩子、产品价值塑造、购买引导——这四个模块一个字不能动。中段内容全部重新表达，让观众听起来像全新内容，但接收到的核心信息和情绪冲击与原文完全一致。

绝对不动区（红线，不可触碰）

以下两个区域必须 100%原样保留，逐字复制：

① 黄金钩子区（前3-4句，即黄金3-5秒）
原文开篇的前3-4句话，必须原封不动。
这是决定观众是否划走的关键，任何改动都会破坏数据模型。

② 转化闭环区（末尾转化部分）
包括但不限于：
产品价值塑造话术（为什么非买这本书不可）
购买行动指令（"链接在左下角"等引导语）
互动引导话术（"评论区聊聊""认同的点个赞"等）
这部分是成交和互动的命门，一个字不能改。

中段重构区（深度二创的主战场）

1. 总目标
重构后的中段要做到：比原文更口语化不要AI感、节奏更紧凑、悬念推进感更强、信息不重复不注水。

2. 硬性约束
原文中的所有事实、人物、时间线、精确数据（年份、尺寸、数量等）必须完整保留。
核心观点和对比框架不能偏离。
严禁编造原文没有的新事实；不确定的信息直接跳过，不硬补。
禁止空洞重复或凑字数。
全文相似度必须低于20%，禁止直接复制原文的任何完整句子。
如果连续3句以上的句式结构与原文雷同，必须立即调整。

3. 改写工具箱（至少选3种组合使用）

策略一：文案拆解先行
动手改写前，先对一次原文做框架拆解，搞清楚以下6个问题：
（1）这篇文案调动了观众什么需求或心理？
（2）钩子用的是哪种结构？（悬念、反常识、痛点直击、利益承诺？）
（3）抽象观点是否落地到了具体的人、事、细节上？
（4）单点核心是什么？用一句话说清文案究竟想传递什么。
（5）情绪爆点在哪一句或哪一段？
（6）观众被推到哪个层级（A1-A5）？
A1：知道有你这个人
A2：被你吸引，产生兴趣
A3：产生疑问，想了解更多
A4：准备行动（点击、评论、购买）
A5：完全认同，成为忠实受众

策略二：信息顺序重组
同一组信息点，换一种叙事顺序呈现。
举例：原文是"建筑描写→背景交代→人物反应"，可改为"人物反应→眼前景象→背景补充"。
判断原文用的是顺序叙事还是倒叙，然后果断切换。

策略三：视角与句式转换
人称切换："我"变"他"，第一人称转第三人称，或反之。
主被动转换："他看到塔"改"塔矗立在他面前"。
叙述方式互换：间接转述变直接对话，人物对话改动作描写。

策略四：背景事实展开（只补充百科级常识）
基于原文信息，补充时代背景、地理信息、历史数据等客观事实。
仅限于"太阳从东边升起"级别的常识，不需要查资料的那种，确保零编造。

策略五：细节同级替换
非关键动作或表情，可替换成同等冲击力的细节。
示例："膝盖沾了土"改"额头沁出了汗"——情绪强度相当，画面感不同。

策略六：句式全面重写
长句拆成短句，短句合并成长句。
陈述句改反问句，设问句改陈述句。
重新安排语气词位置、停顿点和长短句交替节奏。

4. 禁用动作
❌ 不准做简单的同义词替换（"好"变"棒"这种不算改写）
� 不准只把段内句子调换顺序就算完成
✅ 必须在句式结构、表达逻辑层面做实质性重构

情绪与五感保留原则

二创前先识别原文中的关键表达：

五感描写：视觉、听觉、触觉、嗅觉、味觉的具体刻画
情绪词汇：有强烈共鸣感的动词和形容词
共鸣金句：让观众感觉"说的就是我"的那几句话

二创时的标准：
✅ 保留情绪强度，可以换场景但共鸣度不能降低
❌ 不准用平淡表达替换有冲击力的情绪表达

参考示例：
原文："他那双手，磨得像砂纸一样。"
✅ 合格改写："他那双手，粗糙得裂了好几道血口子。"（换表达，五感保留）
❌ 不合格："他的手很粗糙。"（情绪和画面感都丢了）

---

表达风格规范

以下表达方式一律禁止：
❌ "在这个充满……的世界里"
❌ "让我们一起……"
❌ "值得一提的是……"
❌ "不仅……更……"
� 任何书面报告腔或AI腔

以下表达方式必须贯彻：
✅ 口语化，街头聊天那种语气
✅ 中老年人不用费劲就能听懂
✅ 用具体场景和细节说话，不用空词

---

交付前强制自查清单

每次生成完文案后，AI必须在内部完成以下检查（不展示给用户，但必须过一遍）：

① 爆点要素是否完整？
黄金三秒钩子是不是一字没动？
产品价值塑造逻辑是不是完整保留？
互动引导设计还在不在？
购买行动指令是否清晰？

② 念出来顺不顺？
长短句有变化吗？
默读一遍，有没有拗口的地方？
语气词听起来自然吗？

③ 情绪和画面感丢了没？
原文的五感描写是否保留或替换成了同等强度的新描写？
核心共鸣金句是否还在（换表达方式也可以）？

④ 有没有编造事实？
是否添加了原文没有的对话、数据、细节？
任何不确定的内容，是不是已经删掉了？

⑤ 相似度达标了吗？
有没有连续3句以上结构跟原文一模一样？
有没有整句直接复制粘贴？

检查不通过 → 立刻修改 → 再查一遍 → 通过后才能交付

工作流程

Step 0：原文纠错
先扫一遍原文，找出错别字、同音字错误、标点问题。
只有发现错误时才输出纠错列表，格式：� 错误 → ✅ 修正。
后续所有改写基于纠错后的版本。

Step 1：输出改写思路与字数对比
说明本次采用了哪几种改写策略。
标注"原文字数"和"改写后字数"，确保差异不超过±10%。

Step 2：交付完整文案
将最终生成的二创文案放在代码块（Code Block）中，方便用户一键复制使用。

---

可选功能：深度补充模式

触发条件：用户主动说"深度补充"或"增加素材"。

执行步骤：
分析原文，标注出可以补充信息的位置（人物背景、事件细节、横向对比案例等）。
主动询问用户："您希望我补充哪一块？请提供资料，或者我用公开常识来补。"
收到确认后，融合新素材重新生成文案。

补充约束：
AI只能补充"百科级常识"，不需要查阅资料就能确认的那种。
不确定的信息直接跳过，不猜测、不编造。
任何补充内容必须标注来源或加限定词（如"据公开资料显示"）。

核心准则（一句话总结）

拿到文案，先拆框架，再重构表达。头尾原样保留，中段深度重写。让每一句都像人说的，让每一段都有信息推进，让每一个情绪点都打到位。"""


def call_llm(system_prompt: str, user_prompt: str) -> str:
    api_key = os.environ.get("MINIMAX_CN_API_KEY", "")
    if not api_key:
        raise SystemExit("MINIMAX_CN_API_KEY not set")
    body = json.dumps({
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
        return "".join(
            b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
        )


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


def make_output_filename(trans_md: Path, title: str) -> str:
    """YYYYMMDD-转录结果＊二创＊<一句话标题>.md"""
    date_prefix = datetime.now().strftime("%Y%m%d")
    # title 里可能含 Windows 非法字符？保险起见替换一下
    safe_title = re.sub(r'[<>:"/\\|?*]', "_", title)
    return f"{date_prefix}-转录结果＊二创＊{safe_title}.md"


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


def secondary_create(trans_md: Path) -> Path:
    """对单个转录 .md 做一次视频号配文二创，输出到 二创短视频文案/"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    title, body, _ = read_transcription(trans_md)
    cleaned_body = pre_correct(body)
    out_name = make_output_filename(trans_md, title)
    out_path = OUT_DIR / out_name
    if out_path.exists():
        print(f"[skip] already exists: {out_path.name}", flush=True)
        return out_path

    extra_instruction = (
        "如果原文没有「转化闭环区」（比如非图书带货内容），则跳过该规则，"
        "把原文最后 2-3 句作为「保留尾」处理即可。"
    )
    user_prompt = (
        f"请对以下转录文案进行深度二创。\n\n"
        f"原标题：{title}\n\n"
        f"原文（已预纠错，以这个版本为准，原文错字以纠错后版本为准）：\n{cleaned_body}\n\n"
        f"按你的工作流程：Step 0 纠错 → Step 1 思路 + 字数 → Step 2 完整代码块。\n"
        f"{extra_instruction}"
    )

    print(f"[二创] {trans_md.name} -> {out_name}", flush=True)
    raw = call_llm(PROMPT, user_prompt)
    print(f"[llm] {len(raw)} chars", flush=True)

    header = (
        f"# 二创短视频文案 · {title}\n\n"
        f"- 原文件：`{trans_md.name}`\n"
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- 模型：{MODEL} (anthropic messages API)\n"
        f"- 风格：视频号配文二创（图书带货策略 + 掐头去尾中段重写）\n\n"
        f"---\n\n"
    )
    out_path.write_text(header + raw, encoding="utf-8")
    print(f"[wrote] {out_path} ({out_path.stat().st_size:,} bytes)", flush=True)
    return out_path





def main():
    if len(sys.argv) < 2:
        # 没指定文件，处理 transcriptions/ 里所有 .md
        targets = sorted(TRANS_DIR.glob("*.md")) if TRANS_DIR.is_dir() else []
    else:
        targets = [Path(sys.argv[1])]
    if not targets:
        print(f"[no targets] {TRANS_DIR} 空", flush=True)
        return
    for t in targets:
        secondary_create(t)


if __name__ == "__main__":
    main()
