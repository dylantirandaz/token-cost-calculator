# tokencalc

CLI tool and Python library for calculating Claude API token costs. Track your Claude Code spending, compare models, plan budgets, and export to CSV.

## Install

```bash
pip install tokencalc
```

## Claude Code usage tracking

See how much your Claude Code sessions are costing you:

```bash
# latest session breakdown (tokens, cache, cost)
tokencalc cc

# list recent sessions with costs
tokencalc cc list

# all-time usage totals
tokencalc cc all

# last 5 sessions in detail
tokencalc cc last 5
```

```
  Claude Opus 4  2026-03-13 20:21
  156 API calls

  Input:                 188 tokens  ->  $0.002820
  Output:              32.2k tokens  ->  $2.41
  Cache write:        115.0k tokens  ->  $2.16
  Cache read:          7.44M tokens  ->  $11.16
  --------------------------------------------------
  Total:               7.58M tokens  ->  $15.73

  Cache saved you $100.40 (vs no caching)
```

Reads directly from `~/.claude/projects/` session logs. No setup needed -- just have Claude Code installed.

## Quick calculations

```bash
tokencalc 50000 10000
```

```
  Claude Sonnet 4
  Input:     50.0k  tokens  ->  $0.1500
  Output:    10.0k  tokens  ->  $0.1500
  Total:     60.0k  tokens  ->  $0.3000
```

Specify a model:

```bash
tokencalc 50k 10k opus-4
```

Compare across all models:

```bash
tokencalc --compare 100k 20k
```

## Interactive mode

```bash
tokencalc
```

Drops into a REPL with all commands available:

| Command | Description |
|---|---|
| `calc <in> <out>` | Calculate cost for given token counts |
| `estimate` | Paste text to estimate its token count |
| `compare <in> <out>` | Side-by-side cost across all models |
| `budget <amount>` | See how many tokens fit in a dollar budget |
| `cc` | Latest Claude Code session cost |
| `cc list` | List recent Claude Code sessions |
| `cc all` | All-time Claude Code usage totals |
| `model <name>` | Switch the active model |
| `pricing` | Show the pricing table |
| `session` | View running session totals |
| `export` | Export session to CSV |
| `history` | Show past sessions |
| `reset` | Reset the current session |

Token counts accept shorthand: `10k`, `1.5M`, `10,000`.

## Use as a library

```python
from tokencalc import calc_cost, estimate_tokens, MODELS, parse_session, find_session_files

# calculate cost with cache breakdown
cost = calc_cost(
    input_tokens=50_000,
    output_tokens=10_000,
    model="sonnet-4",
    cache_write_tokens=5_000,
    cache_read_tokens=100_000,
)
print(f"Total: ${cost['total']:.4f}")

# parse a Claude Code session
sessions = find_session_files()
data = parse_session(sessions[0]["path"])
print(f"Session cost: ${data['cost']['total']:.2f}")

# estimate tokens from text
tokens = estimate_tokens("some long prompt text here...")

# list models
for key, info in MODELS.items():
    print(f"{info['name']}: ${info['input']}/M in, ${info['output']}/M out")
```

## Supported models

| Model | Input (per 1M) | Output (per 1M) | Cache Write | Cache Read |
|---|---|---|---|---|
| Claude Opus 4 | $15.00 | $75.00 | $18.75 | $1.50 |
| Claude Sonnet 4 | $3.00 | $15.00 | $3.75 | $0.30 |
| Claude 4.5 Haiku | $0.80 | $4.00 | $1.00 | $0.08 |
| Claude 3.5 Haiku | $0.80 | $4.00 | $1.00 | $0.08 |
| Claude 3 Opus | $15.00 | $75.00 | $18.75 | $1.50 |
| Claude 3.5 Sonnet | $3.00 | $15.00 | $3.75 | $0.30 |

Pricing from the [Anthropic docs](https://docs.anthropic.com/en/docs/about-claude/models). Open an issue or PR if anything's out of date.

## License

MIT
