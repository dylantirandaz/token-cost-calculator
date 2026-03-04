"""tokencalc - claude token cost calculator"""

import sys
import json
import os
from datetime import datetime

# pricing per 1M tokens
MODELS = {
    "opus-4": {
        "name": "Claude Opus 4",
        "input": 15.00,
        "output": 75.00,
    },
    "sonnet-4": {
        "name": "Claude Sonnet 4",
        "input": 3.00,
        "output": 15.00,
    },
    "haiku-3.5": {
        "name": "Claude 3.5 Haiku",
        "input": 0.80,
        "output": 4.00,
    },
    "opus-3": {
        "name": "Claude 3 Opus",
        "input": 15.00,
        "output": 75.00,
    },
    "sonnet-3.5": {
        "name": "Claude 3.5 Sonnet",
        "input": 3.00,
        "output": 15.00,
    },
}

DEFAULT_MODEL = "sonnet-4"

CHARS_PER_TOKEN = 4

HISTORY_FILE = os.path.expanduser("~/.tokencalc_history.json")


class Session:
    def __init__(self):
        self.model = DEFAULT_MODEL
        self.entries = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    def add(self, input_tokens: int, output_tokens: int, label: str = ""):
        pricing = MODELS[self.model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        cost = input_cost + output_cost

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost

        entry = {
            "label": label,
            "model": self.model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "timestamp": datetime.now().isoformat(),
        }
        self.entries.append(entry)
        return cost, input_cost, output_cost

    def save(self):
        history = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE) as f:
                    history = json.load(f)
            except (json.JSONDecodeError, IOError):
                history = []

        history.append({
            "session_start": self.entries[0]["timestamp"] if self.entries else datetime.now().isoformat(),
            "model": self.model,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost": self.total_cost,
            "entries": self.entries,
        })

        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)


BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
MAGENTA = "\033[35m"
RESET = "\033[0m"


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def fmt_cost(c: float) -> str:
    if c < 0.01:
        return f"${c:.6f}"
    if c < 1.00:
        return f"${c:.4f}"
    return f"${c:.2f}"


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def print_banner():
    print(f"""
{BOLD}╔══════════════════════════════════════════╗
║     Token Cost Calculator  (Claude)      ║
╚══════════════════════════════════════════╝{RESET}
""")


def print_result(input_tokens, output_tokens, cost, input_cost, output_cost, label=""):
    total_tokens = input_tokens + output_tokens
    if label:
        print(f"\n  {DIM}── {label} ──{RESET}")
    print(f"  {CYAN}Input:{RESET}  {fmt_tokens(input_tokens):>10}  tokens  →  {GREEN}{fmt_cost(input_cost)}{RESET}")
    print(f"  {CYAN}Output:{RESET} {fmt_tokens(output_tokens):>10}  tokens  →  {GREEN}{fmt_cost(output_cost)}{RESET}")
    print(f"  {BOLD}Total:{RESET}  {fmt_tokens(total_tokens):>10}  tokens  →  {BOLD}{GREEN}{fmt_cost(cost)}{RESET}")


def print_session(session: Session):
    if not session.entries:
        return
    total_tokens = session.total_input_tokens + session.total_output_tokens
    print(f"\n  {MAGENTA}{'─' * 42}{RESET}")
    print(f"  {BOLD}{MAGENTA}Session{RESET}  {DIM}({len(session.entries)} call{'s' if len(session.entries) != 1 else ''} · {MODELS[session.model]['name']}){RESET}")
    print(f"  {CYAN}Input:{RESET}  {fmt_tokens(session.total_input_tokens):>10}  tokens")
    print(f"  {CYAN}Output:{RESET} {fmt_tokens(session.total_output_tokens):>10}  tokens")
    print(f"  {BOLD}Total:{RESET}  {fmt_tokens(total_tokens):>10}  tokens  →  {BOLD}{YELLOW}{fmt_cost(session.total_cost)}{RESET}")


def print_pricing_table():
    print(f"\n  {BOLD}Model Pricing (per 1M tokens):{RESET}\n")
    print(f"  {'Model':<22} {'Input':>10} {'Output':>10}")
    print(f"  {'─' * 22} {'─' * 10} {'─' * 10}")
    for key, m in MODELS.items():
        marker = f" {YELLOW}◄{RESET}" if key == session.model else ""
        print(f"  {m['name']:<22} {fmt_cost(m['input']):>10} {fmt_cost(m['output']):>10}{marker}")
    print()


def print_help():
    print(f"""
  {BOLD}Commands:{RESET}

  {CYAN}calc{RESET} [input] [output]   Calculate cost from token counts
  {CYAN}estimate{RESET}                Estimate tokens from pasted text
  {CYAN}model{RESET} [name]            Switch model (e.g. model opus-4)
  {CYAN}pricing{RESET}                 Show pricing table
  {CYAN}session{RESET}                 Show session totals
  {CYAN}history{RESET}                 Show past session history
  {CYAN}reset{RESET}                   Reset session
  {CYAN}help{RESET}                    Show this help
  {CYAN}quit{RESET}                    Exit (saves session)
""")


def print_history():
    if not os.path.exists(HISTORY_FILE):
        print(f"\n  {DIM}No history yet.{RESET}\n")
        return

    try:
        with open(HISTORY_FILE) as f:
            history = json.load(f)
    except (json.JSONDecodeError, IOError):
        print(f"\n  {DIM}No history yet.{RESET}\n")
        return

    if not history:
        print(f"\n  {DIM}No history yet.{RESET}\n")
        return

    grand_total = 0.0
    print(f"\n  {BOLD}Past Sessions:{RESET}\n")
    for i, s in enumerate(history[-10:], 1):
        ts = s.get("session_start", "?")[:16].replace("T", " ")
        model = MODELS.get(s.get("model", ""), {}).get("name", s.get("model", "?"))
        cost = s.get("total_cost", 0)
        inp = s.get("total_input_tokens", 0)
        out = s.get("total_output_tokens", 0)
        grand_total += cost
        print(f"  {DIM}{ts}{RESET}  {model:<22} {fmt_tokens(inp + out):>8} tok  {GREEN}{fmt_cost(cost)}{RESET}")

    print(f"\n  {BOLD}Grand total: {YELLOW}{fmt_cost(grand_total)}{RESET}\n")


def cmd_calc(args: list[str], session: Session):
    if len(args) >= 2:
        try:
            input_tokens = int(args[0].replace(",", "").replace("k", "000").replace("K", "000"))
            output_tokens = int(args[1].replace(",", "").replace("k", "000").replace("K", "000"))
        except ValueError:
            print(f"  {RED}Invalid numbers. Usage: calc <input_tokens> <output_tokens>{RESET}")
            return
    else:
        try:
            raw = input(f"  {CYAN}Input tokens:{RESET}  ").strip()
            input_tokens = int(raw.replace(",", "").replace("k", "000").replace("K", "000"))
            raw = input(f"  {CYAN}Output tokens:{RESET} ").strip()
            output_tokens = int(raw.replace(",", "").replace("k", "000").replace("K", "000"))
        except (ValueError, EOFError):
            print(f"  {RED}Invalid input.{RESET}")
            return

    label = f"calc {fmt_tokens(input_tokens)} in / {fmt_tokens(output_tokens)} out"
    cost, input_cost, output_cost = session.add(input_tokens, output_tokens, label)
    print_result(input_tokens, output_tokens, cost, input_cost, output_cost)
    print_session(session)


def cmd_estimate(session: Session):
    print(f"  {DIM}Paste your text (enter a blank line to finish):{RESET}")
    lines = []
    try:
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
    except EOFError:
        pass

    text = "\n".join(lines)
    if not text.strip():
        print(f"  {RED}No text provided.{RESET}")
        return

    tokens = estimate_tokens(text)
    print(f"\n  {BOLD}Estimated tokens:{RESET} {fmt_tokens(tokens)}")
    print(f"  {DIM}(~{len(text)} chars, ~{CHARS_PER_TOKEN} chars/token){RESET}")

    try:
        choice = input(f"\n  Use as {CYAN}[i]{RESET}nput, {CYAN}[o]{RESET}utput, or {CYAN}[s]{RESET}kip? ").strip().lower()
    except EOFError:
        return

    if choice in ("i", "input"):
        try:
            raw = input(f"  {CYAN}Output tokens:{RESET} ").strip()
            output_tokens = int(raw.replace(",", "").replace("k", "000").replace("K", "000"))
        except (ValueError, EOFError):
            print(f"  {RED}Invalid input.{RESET}")
            return
        label = "estimate (as input)"
        cost, input_cost, output_cost = session.add(tokens, output_tokens, label)
        print_result(tokens, output_tokens, cost, input_cost, output_cost)
        print_session(session)

    elif choice in ("o", "output"):
        try:
            raw = input(f"  {CYAN}Input tokens:{RESET}  ").strip()
            input_tokens = int(raw.replace(",", "").replace("k", "000").replace("K", "000"))
        except (ValueError, EOFError):
            print(f"  {RED}Invalid input.{RESET}")
            return
        label = "estimate (as output)"
        cost, input_cost, output_cost = session.add(input_tokens, tokens, label)
        print_result(input_tokens, tokens, cost, input_cost, output_cost)
        print_session(session)


def cmd_model(args: list[str], session: Session):
    if args:
        key = args[0].lower()
        if key in MODELS:
            session.model = key
            print(f"  Switched to {BOLD}{MODELS[key]['name']}{RESET}")
            return
        for k, m in MODELS.items():
            if key in k or key in m["name"].lower():
                session.model = k
                print(f"  Switched to {BOLD}{m['name']}{RESET}")
                return
        print(f"  {RED}Unknown model '{key}'. Available:{RESET}")

    for key in MODELS:
        marker = f" {YELLOW}◄ current{RESET}" if key == session.model else ""
        print(f"    {key:<16} {MODELS[key]['name']}{marker}")


# quick mode
if len(sys.argv) >= 3:
    session = Session()
    if len(sys.argv) >= 4 and sys.argv[3] in MODELS:
        session.model = sys.argv[3]
    try:
        inp = int(sys.argv[1].replace(",", "").replace("k", "000").replace("K", "000"))
        out = int(sys.argv[2].replace(",", "").replace("k", "000").replace("K", "000"))
    except ValueError:
        print(f"Usage: tokencalc <input_tokens> <output_tokens> [model]")
        sys.exit(1)

    pricing = MODELS[session.model]
    input_cost = (inp / 1_000_000) * pricing["input"]
    output_cost = (out / 1_000_000) * pricing["output"]
    cost = input_cost + output_cost

    print(f"  {MODELS[session.model]['name']}")
    print_result(inp, out, cost, input_cost, output_cost)
    sys.exit(0)

session = Session()
print_banner()
print(f"  Model: {BOLD}{MODELS[session.model]['name']}{RESET}")
print(f"  {DIM}Type 'help' for commands, or 'calc <in> <out>' for quick calc{RESET}\n")

try:
    while True:
        try:
            raw = input(f"{BOLD}▸{RESET} ").strip()
        except EOFError:
            break

        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("quit", "exit", "q"):
            if session.entries:
                session.save()
                print(f"\n  {DIM}Session saved. Total cost: {YELLOW}{fmt_cost(session.total_cost)}{RESET}\n")
            break
        elif cmd in ("calc", "c"):
            cmd_calc(args, session)
        elif cmd in ("estimate", "est", "e"):
            cmd_estimate(session)
        elif cmd in ("model", "m"):
            cmd_model(args, session)
        elif cmd in ("pricing", "price", "p"):
            print_pricing_table()
        elif cmd in ("session", "s"):
            print_session(session)
            if not session.entries:
                print(f"  {DIM}No calls tracked yet.{RESET}\n")
        elif cmd in ("history", "h"):
            print_history()
        elif cmd in ("reset", "r"):
            if session.entries:
                session.save()
            session = Session()
            print(f"  {DIM}Session reset.{RESET}")
        elif cmd == "help":
            print_help()
        else:
            if len(parts) == 2:
                try:
                    int(parts[0].replace(",", "").replace("k", "000").replace("K", "000"))
                    cmd_calc(parts, session)
                    continue
                except ValueError:
                    pass
            print(f"  {DIM}Unknown command. Type 'help' for usage.{RESET}")

except KeyboardInterrupt:
    if session.entries:
        session.save()
    print(f"\n  {DIM}Bye.{RESET}\n")
