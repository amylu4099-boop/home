"""
转录脚本（基于 faster-whisper，CPU）
输出：transcriptions/<R1 一句话标题>.md
依赖：_common.py（提供 R1 标题生成、API 调用、路径常量）
"""
import sys, time, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (
    call_llm, generate_r1_title, safe_filename_for_md,
    TRANS_DIR, DEFAULT_MODEL,
)


def transcribe(audio_path: Path, out_md: Path | None = None, model_size: str = "base"):
    """转录一个音频文件，返回最终输出 .md 路径"""
    print(f"[start] {audio_path.name}", flush=True)
    t0 = time.time()
    from faster_whisper import WhisperModel
    print(f"[import faster_whisper {time.time()-t0:.1f}s]", flush=True)

    print(f"[audio] {audio_path.stat().st_size:,} bytes", flush=True)
    t1 = time.time()
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    print(f"[load model {model_size} {time.time()-t1:.1f}s]", flush=True)

    t2 = time.time()
    segments, info = model.transcribe(str(audio_path), language="zh", beam_size=5, vad_filter=True)
    print(f"[detect lang={info.language} prob={info.language_probability:.2f}]", flush=True)
    lines = [seg.text.strip() for seg in segments if seg.text.strip()]
    print(f"[transcribe {time.time()-t2:.1f}s, {len(lines)} segments]", flush=True)

    text = "".join(lines).strip()
    print(f"[total chars: {len(text)}]", flush=True)

    # 段落整理
    text_clean = re.sub(r"\s+", " ", text)
    period = chr(0x3002) + chr(0xFF01) + chr(0xFF1F) + "!?"
    text_clean = re.sub(rf"([{period}])\s*", "\n", text_clean)
    paragraphs = [p.strip() for p in text_clean.split("\n") if p.strip()]

    # R1: 生成一句话标题
    body_for_llm = "\n".join(paragraphs[:30])  # 限制长度避免超 token
    title = generate_r1_title(body_for_llm)
    print(f"[R1 title] {title}", flush=True)

    # 决定输出文件路径
    if out_md is None:
        TRANS_DIR.mkdir(parents=True, exist_ok=True)
        out_md = TRANS_DIR / f"{safe_filename_for_md(title)}.md"

    header = (
        f"# {title}\n\n"
        f"- 源文件: {audio_path.name}\n"
        f"- 模型: faster-whisper {model_size} (CPU, int8)\n"
        f"- 语言: {info.language} (自动检测, 置信度 {info.language_probability:.2f})\n"
        f"- 字数: 约 {len(text)} 字\n"
        f"- 转录时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
    )
    out_md.write_text(header + "\n\n".join(paragraphs), encoding="utf-8")
    print(f"[wrote] {out_md} ({out_md.stat().st_size:,} bytes)", flush=True)
    print(f"[total elapsed] {time.time()-t0:.1f}s", flush=True)
    return out_md


def auto_secondary(trans_md: Path):
    """链式触发二创"""
    sc = Path(__file__).resolve().parent / "secondary_create.py"
    if not sc.exists():
        print(f"[auto] secondary_create.py not found, skip", flush=True)
        return
    try:
        r = subprocess.run(
            [sys.executable, str(sc), str(trans_md)],
            capture_output=True, text=True, timeout=900,
        )
        print(r.stdout, flush=True)
        if r.returncode != 0:
            print(f"[auto] failed: {r.stderr[:500]}", flush=True)
    except subprocess.TimeoutExpired:
        print(f"[auto] secondary_create timeout", flush=True)
    except Exception as e:
        print(f"[auto] error: {e}", flush=True)


if __name__ == "__main__":
    import subprocess
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <input.mp3> [output.md] [model_size]", flush=True)
        sys.exit(1)
    audio = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) >= 3 else None
    size = sys.argv[3] if len(sys.argv) >= 4 else "base"
    trans_md = transcribe(audio, out, size)
    auto_secondary(trans_md)
