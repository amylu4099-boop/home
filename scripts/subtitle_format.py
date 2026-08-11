import os, json, urllib.request, re, sys
from pathlib import Path
from datetime import datetime

repo = Path(__file__).resolve().parent.parent
out_dir = repo / '字幕'
(repo / '字幕' / title).mkdir(parents=True, exist_ok=True)

API_KEY = os.environ.get('MINIMAX_CN_API_KEY', '')
API_BASE = 'https://api.minimaxi.com/anthropic'
MODEL = 'MiniMax-M3'

USER_PROMPT = r"""你是一位专业的短视频字幕排版专家，擅长根据语义和口语节奏，将长文案精准拆分为适合快速阅读的短句。所有输出均为无标点纯文本，可直接导入各类剪辑软件的字幕轨道。

核心约束（必须100%遵守）
每行字数：每行汉字 严格不超过8个字（含数字、英文单词按1个字符计）。遇到长句必须在自然的语义或配音停顿处拆分。
禁止拆分词组：不得在完整词语（如"中华人民共和国"、"互联网"）中间断行。
"的"字不顶行：任何以"的"开头的行均属违规。
一句一行：每条字幕独立成行，严禁将多个分句或完整句子合并到同一行。保留原叙事顺序，不得调换或重组。
纯净文本：输出内容不得包含任何标点符号（逗号、句号、问号、叹号、引号、省略号等），只允许汉字、数字和极少数的必要英文/符号（如"%"）。

处理流程
拆分：按口语停顿和意群，将文案切分为单行<=8字的短句，保持语义连贯。
清洗：删除所有标点符号，检查每行是否满足字数、词组完整、"的"字位置等规则。
终检：逐行核对字数，确认无一遗漏或超限，确保格式统一。

输出格式
所有结果必须使用 代码块（```） 包裹，内部仅包含处理后的纯文本字幕，每行一句，行间无空行。

初始化回复
当用户发送文案后，你首先回复：
"明白，纯净版字幕分行功能已加载。请发送您的文案，我将严格执行每行<=8字、无标点、一句一行的排版规则。"""


def call_llm(system, user, max_tokens=4000):
    body = json.dumps({
        'model': MODEL,
        'max_tokens': max_tokens,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
    }).encode('utf-8')
    req = urllib.request.Request(
        f'{API_BASE}/v1/messages',
        data=body,
        headers={
            'x-api-key': API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read().decode('utf-8'))
        return ''.join(b.get('text', '') for b in data.get('content', []) if b.get('type') == 'text')


def extract_theme(stem):
    if chr(0xff0a) in stem:
        return stem.split(chr(0xff0a))[-1]
    return stem


def safe_filename(s):
    return re.sub(r'[<>:"/\\\\|?*]', '_', s)[:80]


def format_subtitle(trans_md: Path) -> Path:
    (repo / '字幕' / title).mkdir(parents=True, exist_ok=True)
    if not trans_md.exists():
        print(f'[skip] no trans: {trans_md}', flush=True)
        return None
    text = trans_md.read_text(encoding='utf-8')
    # 提取标题
    title_match = re.match(r'^#\s*(.+?)\s*$', text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else trans_md.stem
    body_start = text.find('---\n\n')
    body = text[body_start+5:].strip() if body_start >= 0 else text

    out_name = 'R6.md'
    out_path = (repo / '字幕' / title) / out_name  # 标题子文件夹
    if out_path.exists():
        print(f'[skip] already: {out_path.name}', flush=True)
        return out_path

    user_content = (
        f'主题: {title}\n\n'
        f'以下是需要排版的二创文案。请严格按你的核心约束执行, 输出格式代码块包裹, 每行一句纯文本, 无标点:\n\n'
        f'"""\n{body[:3500]}\n"""'
    )
    print(f'[R6] {trans_md.name[:40]}...', flush=True)
    try:
        raw = call_llm(USER_PROMPT, user_content, max_tokens=3500)
        # 提取代码块内容
        codes = re.findall(r"```\n?(.*?)\n?```", raw, re.DOTALL)
        subtitle = codes[-1].strip() if codes else raw
        # 统计行数
        lines = [l for l in subtitle.splitlines() if l.strip()]
        print(f'  [lines] {len(lines)}', flush=True)
        header = (
            f'# 字幕排版 · {title}\n\n'
            f'- 源文件: `{trans_md.name}`\n'
            f'- 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
            f'- 模型: {MODEL}\n'
            f'- 字幕行数: {len(lines)}\n'
            f'- 规则: 每行 <= 8 字, 无标点, 一句一行, 原顺序保留\n\n'
            f'---\n\n'
            f'```\n{subtitle}\n```\n'
        )
        out_path.write_text(header, encoding='utf-8')
        print(f'  [wrote] {out_path.name} ({out_path.stat().st_size:,} bytes)', flush=True)
    except Exception as e:
        print(f'  [err] {e}', flush=True)
    return out_path


def main():
    targets = sys.argv[1:]
    if not targets:
        # 默认处理 transcriptions/ 所有 .md
        targets = sorted((repo / 'transcriptions').glob('*.md'))
    if not targets:
        print('[no targets]', flush=True)
        return
    for t in targets:
        format_subtitle(Path(t))


if __name__ == '__main__':
    main()