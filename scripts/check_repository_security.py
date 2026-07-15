from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "AI-AGENT-SYSTEM-FULL-2"
BACKEND = PROJECT / "backend"

IGNORED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "tests",
}

TEXT_SUFFIXES = {
    ".cfg",
    ".env",
    ".example",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

SECRET_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("Telegram bot token", re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{25,}\b")),
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
)

BLOCKED_SOURCE_PATTERNS = (
    ("wildcard Flask CORS", re.compile(r"CORS\s*\([^)]*origins\s*=\s*[\"']\*[\"']", re.DOTALL)),
    (
        "fallback JWT secret",
        re.compile(r"os\.getenv\(\s*[\"']JWT_SECRET_KEY[\"']\s*,\s*[\"'][^\"']+[\"']"),
    ),
)


def iter_text_files():
    for path in PROJECT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        if path.name == ".env" or path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def main() -> int:
    findings: list[str] = []

    committed_env = BACKEND / ".env"
    if committed_env.exists():
        findings.append("backend/.env must not be committed; use backend/.env.example.")

    for path in iter_text_files():
        content = path.read_text(encoding="utf-8", errors="ignore")
        relative = path.relative_to(ROOT)
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(content):
                findings.append(f"{relative}: possible {label}")
        if path.name == "app.py":
            for label, pattern in BLOCKED_SOURCE_PATTERNS:
                if pattern.search(content):
                    findings.append(f"{relative}: {label}")

    if findings:
        print("Repository security checks failed:")
        for finding in sorted(set(findings)):
            print(f"- {finding}")
        return 1

    print("Repository security checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
