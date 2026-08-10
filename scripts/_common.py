"""scripts/_common.py — 多个脚本共享的工具"""
import os, json, urllib.request, re
from pathlib import Path

API_BASE = "https://api.minimaxi.com/anthropic"
DEFAULT_MODEL = "MiniMax-M3"
REPO = Path(__file__).resolve().parent.parent
TRANS_DIR = REPO / "transcriptions"
SEC_DIR = REPO / "二创短视频文案"


def call_llm(system: str, user: str, max_tokens: int = 4000, model: str = DEFAULT_MODEL) -> str:
    api_key = os.environ.get("MINIMAX_CN_API_KEY", "")
    if not api_key:
        raise SystemExit("MINIMAX_CN_API_KEY not set")
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
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
        return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def generate_r1_title(body: str) -> str:
    """R1 规则：基于内容生成 15-25 字钩子标题"""
    system_prompt = (
        "你是视频文案标题党。基于用户提供的转录正文，生成一句 15-25 字的中文钩子标题。"
        "要求：信息密度高、有冲突/悬念感、不要 emoji、不要引号、不要换行、不要书名号、"
        "不要带【标题】二字本身。只输出标题本身，不要任何解释、不要 markdown 包裹。"
    )
    user_prompt = "转录正文：\n" + body[:1500]
    raw = call_llm(system_prompt, user_prompt, max_tokens=200).strip()
    # 去掉可能的引号包裹
    raw = raw.strip('"').strip("'").strip("「").strip("」").strip()
    # 去掉可能的 markdown 包裹
    raw = re.sub(r"^#+\s*", "", raw)
    # 单行
    raw = raw.split("\n")[0].strip()
    return raw


def safe_filename(title: str) -> str:
    """确保标题作为 Windows 文件名合法（替换非法字符）"""
    illegal = '<>:"/\\|?*'
    for c in illegal:
        title = title.replace(c, "_")
    # 去掉首尾空白和点（Windows 不允许以点结尾）
    title = title.strip().rstrip(".")
    return title[:200] if len(title) > 200 else title


def safe_filename_for_md(title: str) -> str:
    """文件名版本：保留中文逗号等"""
    illegal = '<>:"/\\|?*'
    for c in illegal:
        title = title.replace(c, "_")
    title = title.strip().rstrip(".")
    return title[:200] if len(title) > 200 else title


# === 敏感信息脱敏 ===

_SENSITIVE_KEYS = {
    "FEISHU_APP_SECRET", "MINIMAX_CN_API_KEY", "MINIMAX_API_KEY",
    "GLM_API_KEY", "HERMES_GATEWAY_TOKEN", "WEIXIN_TOKEN",
}


def mask_secret(value: str) -> str:
    """脱敏 secret：保留前 4 + 后 4 字符"""
    if not value or len(value) <= 10:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def mask_env_value(key: str, value: str) -> str:
    """如果是敏感 key，返回脱敏后值；否则原样"""
    return mask_secret(value) if key in _SENSITIVE_KEYS else value


def echo_env(env_path: Path, secrets_only: bool = False) -> str:
    """安全地 echo .env 内容（敏感字段自动脱敏）"""
    if not env_path.exists():
        return ""
    lines = []
    for line in env_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            lines.append(line)
            continue
        if "=" not in s:
            lines.append(line)
            continue
        key, val = s.split("=", 1)
        key = key.strip()
        val = val.strip()
        if secrets_only and key not in _SENSITIVE_KEYS:
            continue
        masked = mask_env_value(key, val)
        lines.append(f"{key}={masked}")
    return "\n".join(lines)
