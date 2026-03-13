"""model definitions and pricing data."""

# pricing per 1M tokens (USD)
# source: https://docs.anthropic.com/en/docs/about-claude/models
MODELS = {
    "opus-4": {
        "name": "Claude Opus 4",
        "input": 15.00,
        "output": 75.00,
        "context": 200_000,
    },
    "sonnet-4": {
        "name": "Claude Sonnet 4",
        "input": 3.00,
        "output": 15.00,
        "context": 200_000,
    },
    "haiku-3.5": {
        "name": "Claude 3.5 Haiku",
        "input": 0.80,
        "output": 4.00,
        "context": 200_000,
    },
    "opus-3": {
        "name": "Claude 3 Opus",
        "input": 15.00,
        "output": 75.00,
        "context": 200_000,
    },
    "sonnet-3.5": {
        "name": "Claude 3.5 Sonnet",
        "input": 3.00,
        "output": 15.00,
        "context": 200_000,
    },
    "sonnet-3.5v2": {
        "name": "Claude 3.5 Sonnet v2",
        "input": 3.00,
        "output": 15.00,
        "context": 200_000,
    },
}

DEFAULT_MODEL = "sonnet-4"

# rough heuristic, works well enough for english text
CHARS_PER_TOKEN = 4


def resolve_model(query: str) -> str | None:
    """find a model key from a partial name or alias."""
    q = query.lower().strip()
    if q in MODELS:
        return q
    for key, m in MODELS.items():
        if q in key or q in m["name"].lower():
            return key
    return None


def calc_cost(input_tokens: int, output_tokens: int, model: str) -> tuple[float, float, float]:
    """returns (total_cost, input_cost, output_cost)."""
    pricing = MODELS[model]
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost, input_cost, output_cost


def estimate_tokens(text: str) -> int:
    """rough char-based token estimate."""
    return max(1, len(text) // CHARS_PER_TOKEN)
