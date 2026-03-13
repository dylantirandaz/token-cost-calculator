"""interactive REPL and CLI entry point."""

import sys

from .formatting import (
    BOLD, CYAN, DIM, GREEN, MAGENTA, RED, RESET, YELLOW,
    fmt_cost, fmt_tokens, parse_token_str,
)
from .models import MODELS, DEFAULT_MODEL, calc_cost_simple, estimate_tokens, resolve_model
from .session import Session, load_history, clear_history

VERSION = "0.3.0"


def print_banner():
    print(f"""
{BOLD}+------------------------------------------+
|     tokencalc - token cost calculator    |
+------------------------------------------+{RESET}
""")


def print_result(input_tokens, output_tokens, cost, input_cost, output_cost, label=""):
    total_tokens = input_tokens + output_tokens
    if label:
        print(f"\n  {DIM}-- {label} --{RESET}")
    print(f"  {CYAN}Input:{RESET}  {fmt_tokens(input_tokens):>10}  tokens  ->  {GREEN}{fmt_cost(input_cost)}{RESET}")
    print(f"  {CYAN}Output:{RESET} {fmt_tokens(output_tokens):>10}  tokens  ->  {GREEN}{fmt_cost(output_cost)}{RESET}")
    print(f"  {BOLD}Total:{RESET}  {fmt_tokens(total_tokens):>10}  tokens  ->  {BOLD}{GREEN}{fmt_cost(cost)}{RESET}")


def print_session_summary(session: Session):
    if not session.entries:
        return
    total_tokens = session.total_input_tokens + session.total_output_tokens
    print(f"\n  {MAGENTA}{'-' * 42}{RESET}")
    print(f"  {BOLD}{MAGENTA}Session{RESET}  {DIM}({len(session.entries)} call{'s' if len(session.entries) != 1 else ''} · {MODELS[session.model]['name']}){RESET}")
    print(f"  {CYAN}Input:{RESET}  {fmt_tokens(session.total_input_tokens):>10}  tokens")
    print(f"  {CYAN}Output:{RESET} {fmt_tokens(session.total_output_tokens):>10}  tokens")
    print(f"  {BOLD}Total:{RESET}  {fmt_tokens(total_tokens):>10}  tokens  ->  {BOLD}{YELLOW}{fmt_cost(session.total_cost)}{RESET}")


def print_pricing_table(current_model: str):
    print(f"\n  {BOLD}Model Pricing (per 1M tokens):{RESET}\n")
    print(f"  {'Model':<24} {'Input':>10} {'Output':>10}")
    print(f"  {'-' * 24} {'-' * 10} {'-' * 10}")
    for key, m in MODELS.items():
        marker = f" {YELLOW}<{RESET}" if key == current_model else ""
        print(f"  {m['name']:<24} {fmt_cost(m['input']):>10} {fmt_cost(m['output']):>10}{marker}")
    print()


def print_help():
    print(f"""
  {BOLD}Commands:{RESET}

  {CYAN}calc{RESET} [input] [output]   Calculate cost from token counts
  {CYAN}estimate{RESET}                Estimate tokens from pasted text
  {CYAN}compare{RESET} [in] [out]      Compare cost across all models
  {CYAN}budget{RESET} <amount>          How many tokens fit in a dollar budget
  {CYAN}cc{RESET}                      Show latest Claude Code session cost
  {CYAN}cc list{RESET}                 List recent Claude Code sessions
  {CYAN}cc all{RESET}                  All-time Claude Code usage totals
  {CYAN}model{RESET} [name]            Switch model (e.g. model opus-4)
  {CYAN}pricing{RESET}                 Show pricing table
  {CYAN}session{RESET}                 Show session totals
  {CYAN}export{RESET}                  Export session to CSV
  {CYAN}history{RESET}                 Show past session history
  {CYAN}clear-history{RESET}           Clear all saved history
  {CYAN}reset{RESET}                   Reset current session
  {CYAN}help{RESET}                    Show this help
  {CYAN}quit{RESET}                    Exit (saves session)
""")


def print_history():
    history = load_history()
    if not history:
        print(f"\n  {DIM}No history yet.{RESET}\n")
        return

    grand_total = 0.0
    print(f"\n  {BOLD}Past Sessions:{RESET}\n")
    for s in history[-10:]:
        ts = s.get("session_start", "?")[:16].replace("T", " ")
        model_name = MODELS.get(s.get("model", ""), {}).get("name", s.get("model", "?"))
        cost = s.get("total_cost", 0)
        inp = s.get("total_input_tokens", 0)
        out = s.get("total_output_tokens", 0)
        grand_total += cost
        print(f"  {DIM}{ts}{RESET}  {model_name:<24} {fmt_tokens(inp + out):>8} tok  {GREEN}{fmt_cost(cost)}{RESET}")

    print(f"\n  {BOLD}Grand total: {YELLOW}{fmt_cost(grand_total)}{RESET}\n")


def cmd_calc(args: list[str], session: Session):
    if len(args) >= 2:
        try:
            input_tokens = parse_token_str(args[0])
            output_tokens = parse_token_str(args[1])
        except ValueError:
            print(f"  {RED}Bad numbers. Usage: calc <input_tokens> <output_tokens>{RESET}")
            return
    else:
        try:
            input_tokens = parse_token_str(input(f"  {CYAN}Input tokens:{RESET}  ").strip())
            output_tokens = parse_token_str(input(f"  {CYAN}Output tokens:{RESET} ").strip())
        except (ValueError, EOFError):
            print(f"  {RED}Invalid input.{RESET}")
            return

    label = f"calc {fmt_tokens(input_tokens)} in / {fmt_tokens(output_tokens)} out"
    cost, input_cost, output_cost = session.add(input_tokens, output_tokens, label)
    print_result(input_tokens, output_tokens, cost, input_cost, output_cost)
    print_session_summary(session)


def cmd_estimate(session: Session):
    print(f"  {DIM}Paste text, then enter a blank line to finish:{RESET}")
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
    print(f"  {DIM}(~{len(text)} chars, ~4 chars/token heuristic){RESET}")

    try:
        choice = input(f"\n  Use as {CYAN}[i]{RESET}nput, {CYAN}[o]{RESET}utput, or {CYAN}[s]{RESET}kip? ").strip().lower()
    except EOFError:
        return

    if choice in ("i", "input"):
        try:
            output_tokens = parse_token_str(input(f"  {CYAN}Output tokens:{RESET} ").strip())
        except (ValueError, EOFError):
            print(f"  {RED}Invalid input.{RESET}")
            return
        cost, ic, oc = session.add(tokens, output_tokens, "estimate (as input)")
        print_result(tokens, output_tokens, cost, ic, oc)
        print_session_summary(session)

    elif choice in ("o", "output"):
        try:
            input_tokens = parse_token_str(input(f"  {CYAN}Input tokens:{RESET}  ").strip())
        except (ValueError, EOFError):
            print(f"  {RED}Invalid input.{RESET}")
            return
        cost, ic, oc = session.add(input_tokens, tokens, "estimate (as output)")
        print_result(input_tokens, tokens, cost, ic, oc)
        print_session_summary(session)


def cmd_compare(args: list[str]):
    """show cost for the same usage across every model."""
    if len(args) >= 2:
        try:
            inp = parse_token_str(args[0])
            out = parse_token_str(args[1])
        except ValueError:
            print(f"  {RED}Bad numbers. Usage: compare <input_tokens> <output_tokens>{RESET}")
            return
    else:
        try:
            inp = parse_token_str(input(f"  {CYAN}Input tokens:{RESET}  ").strip())
            out = parse_token_str(input(f"  {CYAN}Output tokens:{RESET} ").strip())
        except (ValueError, EOFError):
            print(f"  {RED}Invalid input.{RESET}")
            return

    print(f"\n  {BOLD}Cost comparison for {fmt_tokens(inp)} input + {fmt_tokens(out)} output:{RESET}\n")
    print(f"  {'Model':<24} {'Input Cost':>12} {'Output Cost':>12} {'Total':>12}")
    print(f"  {'-' * 24} {'-' * 12} {'-' * 12} {'-' * 12}")

    results = []
    for key, m in MODELS.items():
        cost, ic, oc = calc_cost_simple(inp, out, key)
        results.append((key, m["name"], ic, oc, cost))

    results.sort(key=lambda r: r[4])
    cheapest = results[0][4]

    for key, name, ic, oc, cost in results:
        mult = f" {DIM}({cost / cheapest:.1f}x){RESET}" if cost > cheapest else f" {GREEN}<- cheapest{RESET}"
        print(f"  {name:<24} {fmt_cost(ic):>12} {fmt_cost(oc):>12} {BOLD}{fmt_cost(cost):>12}{RESET}{mult}")
    print()


def cmd_budget(args: list[str], model: str):
    """show how many tokens you can get for a given dollar amount."""
    if args:
        try:
            budget = float(args[0].replace("$", ""))
        except ValueError:
            print(f"  {RED}Usage: budget <amount>{RESET}")
            return
    else:
        try:
            budget = float(input(f"  {CYAN}Budget (USD):{RESET} $").strip().replace("$", ""))
        except (ValueError, EOFError):
            print(f"  {RED}Invalid amount.{RESET}")
            return

    pricing = MODELS[model]
    max_input = int(budget / pricing["input"] * 1_000_000)
    max_output = int(budget / pricing["output"] * 1_000_000)

    print(f"\n  {BOLD}Budget: ${budget:.2f}{RESET}  ({MODELS[model]['name']})\n")
    print(f"  If all input:   {fmt_tokens(max_input):>12} tokens")
    print(f"  If all output:  {fmt_tokens(max_output):>12} tokens")

    # show a typical 3:1 input/output split
    if pricing["input"] + pricing["output"] / 3 > 0:
        mixed_calls_tokens = budget / ((pricing["input"] + pricing["output"] / 3) / 1_000_000)
        in_tok = int(mixed_calls_tokens * 0.75)
        out_tok = int(mixed_calls_tokens * 0.25)
        print(f"  Mixed (3:1):    {fmt_tokens(in_tok):>12} in + {fmt_tokens(out_tok):>8} out")
    print()


def cmd_model(args: list[str], session: Session):
    if args:
        key = resolve_model(args[0])
        if key:
            session.model = key
            print(f"  Switched to {BOLD}{MODELS[key]['name']}{RESET}")
            return
        print(f"  {RED}Unknown model '{args[0]}'. Available:{RESET}")

    for key in MODELS:
        marker = f" {YELLOW}< current{RESET}" if key == session.model else ""
        print(f"    {key:<16} {MODELS[key]['name']}{marker}")


def cmd_export(session: Session):
    if not session.entries:
        print(f"  {DIM}Nothing to export.{RESET}")
        return
    csv_data = session.to_csv()
    filename = f"tokencalc_export.csv"
    with open(filename, "w", newline="") as f:
        f.write(csv_data)
    print(f"  {GREEN}Exported {len(session.entries)} entries to {filename}{RESET}")


def run_oneshot(argv: list[str]):
    """handle CLI args for non-interactive usage."""
    from .claudecode import cmd_watch_latest, cmd_watch_list, cmd_watch_all

    if argv[0] == "--version":
        print(f"tokencalc {VERSION}")
        return

    if argv[0] == "--compare":
        cmd_compare(argv[1:])
        return

    if argv[0] == "cc":
        # tokencalc cc          -> latest session
        # tokencalc cc last N   -> last N sessions
        # tokencalc cc list     -> list recent sessions
        # tokencalc cc all      -> all-time totals
        sub = argv[1] if len(argv) > 1 else "last"
        if sub == "list":
            n = int(argv[2]) if len(argv) > 2 else 10
            cmd_watch_list(n)
        elif sub == "all":
            cmd_watch_all()
        else:
            # "last" or a number
            if sub == "last":
                n = int(argv[2]) if len(argv) > 2 else 1
            else:
                try:
                    n = int(sub)
                except ValueError:
                    n = 1
            cmd_watch_latest(n)
        return

    # tokencalc <input> <output> [model]
    model = DEFAULT_MODEL
    if len(argv) >= 3:
        resolved = resolve_model(argv[2])
        if resolved:
            model = resolved

    try:
        inp = parse_token_str(argv[0])
        out = parse_token_str(argv[1])
    except (ValueError, IndexError):
        print(f"Usage: tokencalc <input_tokens> <output_tokens> [model]")
        print(f"       tokencalc --compare <input_tokens> <output_tokens>")
        print(f"       tokencalc cc [last N | list | all]")
        print(f"       tokencalc  (interactive mode)")
        sys.exit(1)

    cost, ic, oc = calc_cost_simple(inp, out, model)
    print(f"  {MODELS[model]['name']}")
    print_result(inp, out, cost, ic, oc)


def repl():
    """main interactive loop."""
    session = Session()
    print_banner()
    print(f"  Model: {BOLD}{MODELS[session.model]['name']}{RESET}")
    print(f"  {DIM}Type 'help' for commands, or 'calc <in> <out>' for quick calc{RESET}\n")

    try:
        while True:
            try:
                raw = input(f"{BOLD}>{RESET} ").strip()
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
            elif cmd in ("compare", "cmp"):
                cmd_compare(args)
            elif cmd in ("budget", "b"):
                cmd_budget(args, session.model)
            elif cmd == "cc":
                from .claudecode import cmd_watch_latest, cmd_watch_list, cmd_watch_all
                sub = args[0] if args else "last"
                if sub == "list":
                    n = int(args[1]) if len(args) > 1 else 10
                    cmd_watch_list(n)
                elif sub == "all":
                    cmd_watch_all()
                else:
                    n = 1
                    if sub != "last":
                        try:
                            n = int(sub)
                        except ValueError:
                            pass
                    elif len(args) > 1:
                        try:
                            n = int(args[1])
                        except ValueError:
                            pass
                    cmd_watch_latest(n)
            elif cmd in ("model", "m"):
                cmd_model(args, session)
            elif cmd in ("pricing", "price", "p"):
                print_pricing_table(session.model)
            elif cmd in ("session", "s"):
                print_session_summary(session)
                if not session.entries:
                    print(f"  {DIM}No calls tracked yet.{RESET}\n")
            elif cmd in ("export",):
                cmd_export(session)
            elif cmd in ("history", "hist"):
                print_history()
            elif cmd in ("clear-history",):
                clear_history()
                print(f"  {DIM}History cleared.{RESET}")
            elif cmd in ("reset", "r"):
                if session.entries:
                    session.save()
                session = Session()
                print(f"  {DIM}Session reset.{RESET}")
            elif cmd == "help":
                print_help()
            elif cmd == "version":
                print(f"  tokencalc {VERSION}")
            else:
                # try implicit calc: two numbers on a line
                if len(parts) == 2:
                    try:
                        parse_token_str(parts[0])
                        cmd_calc(parts, session)
                        continue
                    except ValueError:
                        pass
                print(f"  {DIM}Unknown command. Type 'help' for usage.{RESET}")

    except KeyboardInterrupt:
        if session.entries:
            session.save()
        print(f"\n  {DIM}Bye.{RESET}\n")


def main():
    argv = sys.argv[1:]
    if argv and argv[0] not in ("--help", "-h"):
        run_oneshot(argv)
    elif argv and argv[0] in ("--help", "-h"):
        print(f"tokencalc {VERSION} - Claude API token cost calculator\n")
        print("Usage:")
        print("  tokencalc                            Interactive mode")
        print("  tokencalc <input> <output> [model]   Quick calculation")
        print("  tokencalc --compare <input> <output> Compare across models")
        print("  tokencalc cc                         Latest Claude Code session cost")
        print("  tokencalc cc last 5                  Last 5 sessions")
        print("  tokencalc cc list                    List recent sessions")
        print("  tokencalc cc all                     All-time usage totals")
        print("  tokencalc --version                  Show version")
    else:
        repl()
