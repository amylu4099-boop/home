"""
R3+R4 整合脚本
作用：把 生图提示词/<R4>.md 的内容追加到对应 R3 通用二创/<R3>.md 末尾
原因：R4 是 R3 D 视频脚本的产物，把两者放一起方便查阅
"""
import re, sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import REPO

GENERAL_DIR = REPO / "二创通用"
IMG_DIR = REPO / "生图提示词"

# R3 文件名格式: YYYYMMDD-转录结果＊通用二创＊<title>.md
# R4 文件名格式: YYYYMMDD-生图提示词＊<title>.md
# 提取 <title> 用作 match key

def extract_title(stem: str) -> str:
    # split by ＊, 取最后一段
    parts = stem.split("＊")
    return parts[-1].strip() if len(parts) >= 2 else stem


def integrate_one(r3_path: Path, r4_path: Path) -> bool:
    r3_text = r3_path.read_text(encoding="utf-8")
    if "## R4 生图提示词（双语）" in r3_text:
        print(f"[skip] already integrated: {r3_path.name}", flush=True)
        return False
    r4_text = r4_path.read_text(encoding="utf-8")
    # 抽 R4 主体 (从 ## 中文 9:16 竖版封面 开始)
    r4_match = re.search(r"## 中文 9:16 竖版封面.*?```$", r4_text, re.DOTALL | re.MULTILINE)
    if not r4_match:
        print(f"[warn] no R4 body found in {r4_path.name}", flush=True)
        return False
    r4_body = r4_match.group(0)
    # R4 .md 里包含两个 ```代码块: 中文 + 英文, 我们的正则只抓到中文块; 重新取全文
    # 直接用整段 R4 body
    r4_body = r4_text.split("---\n\n", 2)[-1] if "---\n\n" in r4_text else r4_text
    # 拼接到 R3 末尾
    append = (
        f"\n\n---\n\n"
        f"## R4 生图提示词（双语）— 整合自 `{r4_path.name}`\n\n"
        f"- 整合时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- 原始 R4 文件：`生图提示词/{r4_path.name}`\n"
        f"- 类型判定 + 双语 prompt 一并保留\n\n"
        f"{r4_body}"
    )
    r3_path.write_text(r3_text + append, encoding="utf-8")
    print(f"[ok] integrated: {r3_path.name}  (+{len(append):,} chars)", flush=True)
    return True


def main():
    r3_files = sorted(GENERAL_DIR.glob("*.md"))
    if not r3_files:
        print(f"[no r3] {GENERAL_DIR} 空", flush=True)
        return
    paired = 0
    skipped = 0
    missing = 0
    for r3 in r3_files:
        title = extract_title(r3.stem)
        # 在 R4 目录里找匹配
        candidates = list(IMG_DIR.glob(f"*{title}.md"))
        if not candidates:
            print(f"[no r4] {r3.name}  -> no matching R4", flush=True)
            missing += 1
            continue
        r4 = candidates[0]  # 取第一个
        if integrate_one(r3, r4):
            paired += 1
        else:
            skipped += 1
    print(f"\n[summary] paired={paired} skipped={skipped} missing={missing}", flush=True)


if __name__ == "__main__":
    main()