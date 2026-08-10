"""
批量转录脚本
用法：
  python batch_transcribe.py <音频目录>           # 默认 medium 模型
  python batch_transcribe.py <音频目录> small     # 用 small 模型
行为：
  1. 扫描目录里所有 mp3/wav/m4a/flac/opus/ogg
  2. 跳过已经在 transcriptions/ 里有过对应输出的（按音频 basename）
  3. 逐个跑 transcribe.py（自动 R1 标题 + 链式 R2 二创）
  4. 全部跑完后批量 git add + commit
"""
import sys, subprocess, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import REPO, TRANS_DIR

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".opus", ".ogg"}
TP_SCRIPT = Path(__file__).resolve().parent / "transcribe.py"


def find_audio(audio_dir: Path) -> list[Path]:
    files = []
    for ext in AUDIO_EXTS:
        files.extend(audio_dir.glob(f"*{ext}"))
        files.extend(audio_dir.glob(f"*{ext.upper()}"))
    return sorted(set(files))


def already_processed(audio: Path) -> bool:
    """如果 transcriptions/ 里有过对应 basename 的 .md（不含 _ 后缀），认为已处理"""
    stem = audio.stem
    for p in TRANS_DIR.glob("*.md"):
        if p.stem == stem or stem in p.stem:
            return True
    return False


def git_commit_batch(notes: str) -> int:
    """全部跑完后批量 commit"""
    r = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True, text=True, cwd=str(REPO),
    )
    if not r.stdout.strip():
        print("[git] nothing to commit", flush=True)
        return 0
    r2 = subprocess.run(
        ["git", "add", "."],
        capture_output=True, text=True, cwd=str(REPO),
    )
    msg = f"batch: 转录 + 二创 {len(audio_files)} 个音频\n\n{notes}"
    r3 = subprocess.run(
        ["git", "commit", "-m", msg],
        capture_output=True, text=True, cwd=str(REPO),
    )
    print(r3.stdout, flush=True)
    if r3.returncode != 0:
        print(f"[git] commit failed: {r3.stderr[:500]}", flush=True)
        return r3.returncode
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_transcribe.py <音频目录> [model_size]", flush=True)
        sys.exit(1)
    audio_dir = Path(sys.argv[1])
    if not audio_dir.is_dir():
        print(f"[err] not a directory: {audio_dir}", flush=True)
        sys.exit(1)
    model_size = sys.argv[2] if len(sys.argv) >= 3 else "base"

    all_audio = find_audio(audio_dir)
    if not all_audio:
        print(f"[no audio] {audio_dir} 里没有 mp3/wav/m4a/flac/opus/ogg 文件", flush=True)
        return

    pending = [a for a in all_audio if not already_processed(a)]
    skipped = [a for a in all_audio if a not in pending]
    print(f"[scan] {len(all_audio)} audio files, {len(pending)} 待处理, {len(skipped)} 跳过（已处理）", flush=True)
    if not pending:
        print("[done] 所有音频都已处理过，跳过", flush=True)
        return

    failures = []
    for i, audio in enumerate(pending, 1):
        print(f"\n========== [{i}/{len(pending)}] {audio.name} ==========", flush=True)
        try:
            r = subprocess.run(
                [sys.executable, str(TP_SCRIPT), str(audio), "--", model_size],
                capture_output=True, text=True, timeout=1800,
            )
            print(r.stdout, flush=True)
            if r.returncode != 0:
                print(f"[err] failed: {r.stderr[:500]}", flush=True)
                failures.append(audio.name)
        except subprocess.TimeoutExpired:
            print(f"[err] timeout: {audio.name}", flush=True)
            failures.append(audio.name)

    print(f"\n========== 完成 ==========", flush=True)
    print(f"成功: {len(pending) - len(failures)}, 失败: {len(failures)}", flush=True)
    if failures:
        for f in failures:
            print(f"  - {f}")

    notes = f"音频目录: {audio_dir}\n模型: {model_size}\n失败: {failures if failures else '无'}"
    git_commit_batch(notes)


if __name__ == "__main__":
    main()
