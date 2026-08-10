"""
转录脚本（基于 faster-whisper，CPU）
用法：python transcribe.py <input.mp3> [output.md]
"""
import sys, time, re
from pathlib import Path

def transcribe(audio_path: Path, out_md: Path | None = None, model_size: str = "base"):
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

    if out_md is None:
        out_md = audio_path.with_suffix(".md")
    out_md.parent.mkdir(parents=True, exist_ok=True)

    text_clean = re.sub(r"\s+", " ", text)
    period = chr(0x3002) + chr(0xFF01) + chr(0xFF1F) + "!?"
    text_clean = re.sub(rf"([{period}])\s*", "\n", text_clean)
    paragraphs = [p.strip() for p in text_clean.split("\n") if p.strip()]

    header = (
        f"# 转录结果\n\n"
        f"- 源文件: {audio_path.name}\n"
        f"- 模型: faster-whisper {model_size} (CPU, int8)\n"
        f"- 语言: {info.language} (自动检测, 置信度 {info.language_probability:.2f})\n"
        f"- 字数: 约 {len(text)} 字\n"
        f"- 转录时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
    )
    out_md.write_text(header + "\n\n".join(paragraphs), encoding="utf-8")
    print(f"[wrote] {out_md} ({out_md.stat().st_size:,} bytes)", flush=True)
    print(f"[total elapsed] {time.time()-t0:.1f}s", flush=True)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <input.mp3> [output.md] [model_size]", flush=True)
        sys.exit(1)
    audio = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) >= 3 else None
    size = sys.argv[3] if len(sys.argv) >= 4 else "base"
    transcribe(audio, out, size)


# === 自动二创（链式调用） ===
try:
    import subprocess
    print("[auto] triggering secondary_create...", flush=True)
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "secondary_create.py"), str(out_md)],
        capture_output=True, text=True, timeout=600,
    )
    print(result.stdout, flush=True)
    if result.returncode != 0:
        print(f"[auto] secondary_create failed: {result.stderr}", flush=True)
except Exception as e:
    print(f"[auto] secondary_create error: {e}", flush=True)
