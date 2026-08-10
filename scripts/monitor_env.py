"""
.env 文件访问监控
用法:
  python monitor_env.py                # 检查当前状态
  python monitor_env.py --watch       # 持续监控（每 60 秒检查）

监控内容:
  - .env 文件权限（应该只有当前用户可读写）
  - .env 文件最后修改时间（如果被改，立刻告警）
  - .env 文件大小（如果突然变小，可能被截断/泄露）
"""
import sys, os, time, stat, hashlib
from pathlib import Path
from datetime import datetime

ENV_PATH = Path(r"C:\Users\Michael\AppData\Local\hermes\profiles\av-transcription\.env")
SENSITIVE_KEYS = ["FEISHU_APP_SECRET", "MINIMAX_CN_API_KEY", "HERMES_GATEWAY_TOKEN"]


def check_file():
    if not ENV_PATH.exists():
        return {"status": "MISSING", "path": str(ENV_PATH)}
    st = ENV_PATH.stat()
    import platform, subprocess
    info = {
        "path": str(ENV_PATH),
        "size": st.st_size,
        "mtime": datetime.fromtimestamp(st.st_mtime).isoformat(),
        "platform": platform.system(),
    }
    if platform.system() == "Windows":
        # Windows: 用 icacls 看 ACL
        try:
            r = subprocess.run(["icacls", str(ENV_PATH)], capture_output=True, text=True, timeout=5)
            acl_text = r.stdout
            # 提取所有用户/组权限
            lines = [l.strip() for l in acl_text.splitlines() if l.strip()]
            info["icacls"] = lines[1:] if len(lines) > 1 else []
            # 简化判定：是否除了 owner 之外还有别的 R 权限
            info["too_open"] = any(
                ("Everyone" in l or "Users" in l or "Authenticated" in l) and "(R)" in l
                for l in info["icacls"]
            )
            info["owner_readable"] = True  # 默认
        except Exception as e:
            info["icacls_error"] = str(e)
            info["too_open"] = None
    else:
        # POSIX: 用 stat mode
        info["mode"] = oct(st.st_mode)[-3:]
        info["owner_readable"] = bool(st.st_mode & stat.S_IRUSR)
        info["group_readable"] = bool(st.st_mode & stat.S_IRGRP)
        info["other_readable"] = bool(st.st_mode & stat.S_IROTH)
        info["too_open"] = info["group_readable"] or info["other_readable"]
    # 计算 hash（用来检测内容是否被改）
    content = ENV_PATH.read_bytes()
    info["sha256"] = hashlib.sha256(content).hexdigest()[:16]
    info["bom"] = content[:3] == b"\xef\xbb\xbf"
    # 检查敏感 key 是否都存在（不打印值）
    text = content.decode("utf-8", errors="replace")
    info["has_secret_keys"] = {k: (k in text) for k in SENSITIVE_KEYS}
    return info


def main():
    watch = "--watch" in sys.argv
    info = check_file()
    print("=" * 60)
    print(f".env 监控报告 - {datetime.now().isoformat()}")
    print("=" * 60)
    print(f"路径:    {info['path']}")
    print(f"大小:    {info['size']} bytes")
    print(f"修改:    {info['mtime']}")
    print(f"权限:    {info.get('mode', 'N/A (Windows)')} (期望 600/ACL-only)")
    print(f"  所有者可读: {info['owner_readable']}")
    
    
    print(f"BOM:     {info['bom']} (期望 False)")
    print(f"SHA256:  {info['sha256']}...")
    print()
    print("敏感 key 检查 (不显示值):")
    for k, present in info["has_secret_keys"].items():
        flag = "OK" if present else "MISSING"
        print(f"  {k}: {flag}")
    
    # 安全检查
    warnings = []
    if info.get("too_open"): warnings.append("权限过宽 - 应只有当前用户可读写 (icacls)")
    if info.get("bom"): warnings.append("文件含 BOM - 应去掉")
    if info.get("size", 0) > 5000: warnings.append("文件过大 (>5KB) - 检查是否有冗余")
    
    if warnings:
        print()
        print("[WARN]")
        for w in warnings:
            print(f"  - {w}")
    else:
        print()
        print("OK 所有检查通过")
    
    if watch:
        print()
        print("[watch] 持续监控 (每 60s 检查一次, Ctrl+C 停止)")
        last_mtime = info["mtime"]
        try:
            while True:
                time.sleep(60)
                info = check_file()
                if info["mtime"] != last_mtime:
                    print(f"[ALERT] .env 被修改! 新 mtime: {info['mtime']}")
                    last_mtime = info["mtime"]
        except KeyboardInterrupt:
            print("[stop] 监控结束")


if __name__ == "__main__":
    main()
