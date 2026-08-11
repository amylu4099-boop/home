"""
Secret 检查工具（手动版）
不是 Git hook（Windows 上 .bat hook 兼容性差）—— 手动跑即可。

用法:
  python scripts/check_secrets.py                 # 检查 staged 但未提交的内容
  python scripts/check_secrets.py --all           # 检查工作区所有 .md / .py / .yaml 等
  python scripts/check_secrets.py --staged-only   # 只检查即将 commit 的内容（默认）
  python scripts/check_secrets.py file1 file2     # 检查指定文件

检测模式:
- FEISHU_APP_SECRET / MINIMAX_CN_API_KEY / HERMES_GATEWAY_TOKEN
- ghp_* GitHub classic PAT
- github_pat_* GitHub fine-grained PAT
- sk-* / sk-cp-* / sk-ant-* OpenAI / MiniMax / Anthropic API
"""
import re, sys, subprocess
from pathlib import Path

PATTERNS = [
    (r"(?:FEISHU_APP_SECRET|MINIMAX_CN_API_KEY|HERMES_GATEWAY_TOKEN)\s*=\s*([A-Za-z0-9_\-]{16,})", "hermes .env key=value"),
    (r"(ghp_[A-Za-z0-9]{36,})", "GitHub classic PAT"),
    (r"(github_pat_[A-Za-z0-9_]{20,})", "GitHub fine-grained PAT"),
    (r"(sk-[A-Za-z0-9]{20,})", "OpenAI API key"),
    (r"(sk-cp-[A-Za-z0-9\-]{20,})", "MiniMax API key"),
    (r"(sk-ant-[A-Za-z0-9\-]{20,})", "Anthropic API key"),
]

ALLOWLIST_PATTERNS = [
    r"\.env\.example$", r"\.gitignore$", r"\.git/", r"restore\.bat$",
    r"README", r"SOUL\.md$", r"\.md$", r"_common\.py$",
    r"check_secrets\.py$", r"pre_commit_hook\.py$",
    r"transcribe_work/",
]

def is_allowed(filepath):
    for pat in ALLOWLIST_PATTERNS:
        if re.search(pat, filepath, re.IGNORECASE):
            return True
    return False

def scan_content(filepath, content):
    findings = []
    for pat, desc in PATTERNS:
        for m in re.finditer(pat, content):
            findings.append((filepath, desc, m.group(0)[:30] + "..."))
    return findings

def scan_staged():
    repo = Path.cwd()
    r = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, cwd=str(repo))
    if r.returncode != 0: return []
    files = [f.strip() for f in r.stdout.splitlines() if f.strip()]
    findings = []
    for f in files:
        if is_allowed(f): continue
        r2 = subprocess.run(["git", "show", f":{f}"], capture_output=True, text=True, cwd=str(repo), errors="replace")
        if r2.returncode != 0: continue
        findings.extend(scan_content(f, r2.stdout))
    return findings

def scan_files(paths):
    findings = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"[skip] not found: {p}", file=sys.stderr)
            continue
        if is_allowed(str(path)): continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"[warn] cant read {p}: {e}", file=sys.stderr)
            continue
        findings.extend(scan_content(str(path), content))
    return findings

def main():
    args = sys.argv[1:]
    if "--all" in args:
        files = []
        for ext in ("*.md", "*.py", "*.yaml", "*.yml", "*.txt", "*.bat"):
            files.extend(str(p) for p in Path.cwd().rglob(ext) if not is_allowed(str(p)))
        findings = scan_files(files)
        mode = "workspace"
    elif "--staged-only" in args or not args:
        findings = scan_staged()
        mode = "staged"
    else:
        findings = scan_files(args)
        mode = "explicit files"

    if findings:
        print("=" * 60)
        print(f"SECRET SCAN ({mode}): {len(findings)} finding(s)")
        print("=" * 60)
        for f, desc, snippet in findings:
            print(f"  [{desc}]")
            print(f"    file: {f}")
            print(f"    match: {snippet}")
        print()
        print("Refused. If these are example values, add path to ALLOWLIST_PATTERNS in scripts/check_secrets.py")
        sys.exit(1)
    else:
        print(f"SECRET SCAN ({mode}): OK no secrets found")
        sys.exit(0)

if __name__ == "__main__":
    main()
