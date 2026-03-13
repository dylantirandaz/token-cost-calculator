"""read and analyze Claude Code session data."""

import json
import os
import glob
from datetime import datetime, timezone

from .models import MODELS, MODEL_ALIASES, calc_cost, resolve_api_model
from .formatting import (
    BOLD, CYAN, DIM, GREEN, MAGENTA, RED, RESET, YELLOW,
    fmt_cost, fmt_tokens,
)

CLAUDE_DIR = os.path.expanduser("~/.claude")
PROJECTS_DIR = os.path.join(CLAUDE_DIR, "projects")


def find_session_files() -> list[dict]:
    """find all .jsonl session files, sorted by modification time (newest first)."""
    pattern = os.path.join(PROJECTS_DIR, "**", "*.jsonl")
    files = glob.glob(pattern, recursive=True)
    result = []
    for f in files:
        try:
            stat = os.stat(f)
            result.append({
                "path": f,
                "mtime": stat.st_mtime,
                "size": stat.st_size,
            })
        except OSError:
            continue
    result.sort(key=lambda x: x["mtime"], reverse=True)
    return result


def parse_session(filepath: str) -> dict:
    """parse a session jsonl file and extract usage data."""
    messages = []
    total_input = 0
    total_output = 0
    total_cache_write = 0
    total_cache_read = 0
    model_key = None
    api_model = None
    session_id = None
    first_ts = None
    last_ts = None
    msg_count = 0

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not session_id and entry.get("sessionId"):
                session_id = entry["sessionId"]

            ts = entry.get("timestamp")
            if ts:
                if not first_ts:
                    first_ts = ts
                last_ts = ts

            if entry.get("type") != "assistant":
                continue

            msg = entry.get("message", {})
            usage = msg.get("usage")
            if not usage:
                continue

            msg_count += 1

            if not api_model and msg.get("model"):
                api_model = msg["model"]
                model_key = resolve_api_model(api_model)

            inp = usage.get("input_tokens", 0)
            out = usage.get("output_tokens", 0)
            cw = usage.get("cache_creation_input_tokens", 0)
            cr = usage.get("cache_read_input_tokens", 0)

            total_input += inp
            total_output += out
            total_cache_write += cw
            total_cache_read += cr

            messages.append({
                "timestamp": ts,
                "input_tokens": inp,
                "output_tokens": out,
                "cache_write_tokens": cw,
                "cache_read_tokens": cr,
            })

    cost_info = {"total": 0, "input_cost": 0, "output_cost": 0,
                 "cache_write_cost": 0, "cache_read_cost": 0}
    if model_key and model_key in MODELS:
        cost_info = calc_cost(total_input, total_output, model_key,
                              total_cache_write, total_cache_read)

    return {
        "filepath": filepath,
        "session_id": session_id,
        "api_model": api_model,
        "model_key": model_key,
        "model_name": MODELS[model_key]["name"] if model_key and model_key in MODELS else (api_model or "unknown"),
        "message_count": msg_count,
        "total_input": total_input,
        "total_output": total_output,
        "total_cache_write": total_cache_write,
        "total_cache_read": total_cache_read,
        "cost": cost_info,
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
        "messages": messages,
    }


def format_session_report(s: dict) -> str:
    """format a parsed session into a readable report."""
    lines = []
    cost = s["cost"]
    total_all_tokens = s["total_input"] + s["total_output"] + s["total_cache_write"] + s["total_cache_read"]

    # header
    ts_display = ""
    if s["first_timestamp"]:
        ts_display = s["first_timestamp"][:16].replace("T", " ")
    lines.append(f"  {BOLD}{s['model_name']}{RESET}  {DIM}{ts_display}{RESET}")
    lines.append(f"  {DIM}{s['message_count']} API calls{RESET}")
    lines.append("")

    # token breakdown
    lines.append(f"  {CYAN}Input:{RESET}        {fmt_tokens(s['total_input']):>12} tokens  ->  {GREEN}{fmt_cost(cost['input_cost'])}{RESET}")
    lines.append(f"  {CYAN}Output:{RESET}       {fmt_tokens(s['total_output']):>12} tokens  ->  {GREEN}{fmt_cost(cost['output_cost'])}{RESET}")
    lines.append(f"  {CYAN}Cache write:{RESET}  {fmt_tokens(s['total_cache_write']):>12} tokens  ->  {GREEN}{fmt_cost(cost['cache_write_cost'])}{RESET}")
    lines.append(f"  {CYAN}Cache read:{RESET}   {fmt_tokens(s['total_cache_read']):>12} tokens  ->  {GREEN}{fmt_cost(cost['cache_read_cost'])}{RESET}")
    lines.append(f"  {'-' * 50}")
    lines.append(f"  {BOLD}Total:{RESET}        {fmt_tokens(total_all_tokens):>12} tokens  ->  {BOLD}{YELLOW}{fmt_cost(cost['total'])}{RESET}")

    # show how much caching saved
    if s["model_key"] and s["total_cache_read"] > 0:
        pricing = MODELS[s["model_key"]]
        would_have_cost = (s["total_cache_read"] / 1_000_000) * pricing["input"]
        actually_cost = cost["cache_read_cost"]
        saved = would_have_cost - actually_cost
        if saved > 0:
            lines.append(f"\n  {GREEN}Cache saved you {fmt_cost(saved)}{RESET} {DIM}(vs no caching){RESET}")

    return "\n".join(lines)


def cmd_watch_latest(n: int = 1):
    """show cost breakdown for the N most recent Claude Code sessions."""
    files = find_session_files()
    if not files:
        print(f"  {RED}No Claude Code sessions found in {PROJECTS_DIR}{RESET}")
        print(f"  {DIM}Make sure Claude Code has been used on this machine.{RESET}")
        return

    grand_total = 0.0
    for i, f in enumerate(files[:n]):
        if i > 0:
            print()
        s = parse_session(f["path"])
        if s["message_count"] == 0:
            continue
        print(format_session_report(s))
        grand_total += s["cost"]["total"]
        print()

    if n > 1:
        print(f"  {BOLD}Grand total across {n} sessions: {YELLOW}{fmt_cost(grand_total)}{RESET}\n")


def cmd_watch_list(n: int = 10):
    """list recent Claude Code sessions with their costs."""
    files = find_session_files()
    if not files:
        print(f"  {RED}No Claude Code sessions found.{RESET}")
        return

    print(f"\n  {BOLD}Recent Claude Code Sessions:{RESET}\n")
    print(f"  {'#':<4} {'Date':>16}  {'Model':<24} {'Messages':>8} {'Cost':>12}")
    print(f"  {'-' * 4} {'-' * 16}  {'-' * 24} {'-' * 8} {'-' * 12}")

    grand_total = 0.0
    for i, f in enumerate(files[:n], 1):
        s = parse_session(f["path"])
        if s["message_count"] == 0:
            continue
        ts = s["first_timestamp"][:16].replace("T", " ") if s["first_timestamp"] else "?"
        cost = s["cost"]["total"]
        grand_total += cost
        print(f"  {i:<4} {ts:>16}  {s['model_name']:<24} {s['message_count']:>8} {GREEN}{fmt_cost(cost):>12}{RESET}")

    print(f"\n  {BOLD}Total: {YELLOW}{fmt_cost(grand_total)}{RESET}\n")


def cmd_watch_all():
    """total cost across all Claude Code sessions ever."""
    files = find_session_files()
    if not files:
        print(f"  {RED}No Claude Code sessions found.{RESET}")
        return

    grand_total = 0.0
    total_messages = 0
    total_input = 0
    total_output = 0
    total_cache_write = 0
    total_cache_read = 0
    session_count = 0

    for f in files:
        s = parse_session(f["path"])
        if s["message_count"] == 0:
            continue
        session_count += 1
        grand_total += s["cost"]["total"]
        total_messages += s["message_count"]
        total_input += s["total_input"]
        total_output += s["total_output"]
        total_cache_write += s["total_cache_write"]
        total_cache_read += s["total_cache_read"]

    total_all = total_input + total_output + total_cache_write + total_cache_read

    print(f"\n  {BOLD}All-time Claude Code Usage:{RESET}\n")
    print(f"  Sessions:     {session_count:>8}")
    print(f"  API calls:    {total_messages:>8}")
    print(f"  Total tokens: {fmt_tokens(total_all):>8}")
    print(f"    Input:        {fmt_tokens(total_input):>8}")
    print(f"    Output:       {fmt_tokens(total_output):>8}")
    print(f"    Cache write:  {fmt_tokens(total_cache_write):>8}")
    print(f"    Cache read:   {fmt_tokens(total_cache_read):>8}")
    print(f"\n  {BOLD}Total cost: {YELLOW}{fmt_cost(grand_total)}{RESET}\n")
