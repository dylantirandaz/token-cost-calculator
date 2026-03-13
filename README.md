# tokencalc

CLI tool and Python library for calculating Claude API token costs. Supports all current Claude models, session tracking, model comparison, budget planning, and CSV export.

## Install

```bash
pip install git+https://github.com/dylantirandaz/token-cost-calculator.git
```

Or clone and install locally:

```bash
git clone https://github.com/dylantirandaz/token-cost-calculator.git
cd token-cost-calculator
pip install .
```

## Quick start

**One-liner from the terminal:**

```bash
tokencalc 50000 10000
```

```
  Claude Sonnet 4
  Input:     50.0k  tokens  ->  $0.1500
  Output:    10.0k  tokens  ->  $0.1500
  Total:     60.0k  tokens  ->  $0.3000
```

**Specify a model:**

```bash
tokencalc 50000 10000 opus-4
```

**Compare across all models:**

```bash
tokencalc --compare 100k 20k
```

```
  Cost comparison for 100.0k input + 20.0k output:

  Model                      Input Cost   Output Cost        Total
  --------------------------  ------------ ------------ ------------
  Claude 3.5 Haiku             $0.0800       $0.0800     $0.1600   <- cheapest
  Claude Sonnet 4              $0.3000       $0.3000     $0.6000   (3.8x)
  Claude 3.5 Sonnet            $0.3000       $0.3000     $0.6000   (3.8x)
  Claude Opus 4                $1.5000       $1.5000     $3.0000   (18.8x)
  Claude 3 Opus                $1.5000       $1.5000     $3.0000   (18.8x)
```

**Interactive mode:**

```bash
tokencalc
```

This drops you into a REPL where you can run multiple calculations, switch models, track session costs, and more.

## Interactive commands

| Command | Description |
|---|---|
| `calc <in> <out>` | Calculate cost for given token counts |
| `estimate` | Paste text to estimate its token count |
| `compare <in> <out>` | Side-by-side cost across all models |
| `budget <amount>` | See how many tokens fit in a dollar budget |
| `model <name>` | Switch the active model |
| `pricing` | Show the pricing table |
| `session` | View running session totals |
| `export` | Export session to CSV |
| `history` | Show past sessions |
| `reset` | Reset the current session |
| `help` | Show all commands |

You can also just type two numbers directly (e.g. `50000 10000`) and it'll calculate.

Token counts accept shorthand: `10k`, `1.5M`, `10,000`.

## Use as a library

```python
from tokencalc import calc_cost, estimate_tokens, MODELS

# calculate cost
total, input_cost, output_cost = calc_cost(
    input_tokens=50_000,
    output_tokens=10_000,
    model="sonnet-4"
)
print(f"Total: ${total:.4f}")

# estimate tokens from text
tokens = estimate_tokens("some long prompt text here...")

# list available models
for key, info in MODELS.items():
    print(f"{info['name']}: ${info['input']}/M in, ${info['output']}/M out")
```

## Session tracking

Each interactive session is saved to `~/.tokencalc_history.json` when you exit. Use `history` to review past sessions and `clear-history` to wipe the file.

## Supported models

| Model | Input (per 1M) | Output (per 1M) |
|---|---|---|
| Claude Opus 4 | $15.00 | $75.00 |
| Claude Sonnet 4 | $3.00 | $15.00 |
| Claude 3.5 Haiku | $0.80 | $4.00 |
| Claude 3 Opus | $15.00 | $75.00 |
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3.5 Sonnet v2 | $3.00 | $15.00 |

Pricing pulled from the [Anthropic docs](https://docs.anthropic.com/en/docs/about-claude/models). Open an issue or PR if anything's out of date.

## License

MIT
