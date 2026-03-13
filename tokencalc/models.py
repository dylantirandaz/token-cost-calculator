"""model definitions and pricing data."""

# pricing per 1M tokens (USD)
# source: https://docs.anthropic.com/en/docs/about-claude/models
# cache_write = cost to create prompt cache, cache_read = cost to read from cache
MODELS = {
    "opus-4": {
        "name": "Claude Opus 4",
        "input": 15.00,
        "output": 75.00,
        "cache_write": 18.75,
        "cache_read": 1.50,
        "context": 200_000,
    },
    "sonnet-4": {
        "name": "Claude Sonnet 4",
        "input": 3.00,
        "output": 15.00,
        "cache_write": 3.75,
        "cache_read": 0.30,
        "context": 200_000,
    },
    "haiku-4.5": {
        "name": "Claude 4.5 Haiku",
        "input": 0.80,
        "output": 4.00,
        "cache_write": 1.00,
        "cache_read": 0.08,
        "context": 200_000,
    },
    "haiku-3.5": {
        "name": "Claude 3.5 Haiku",
        "input": 0.80,
        "output": 4.00,
        "cache_write": 1.00,
        "cache_read": 0.08,
        "context": 200_000,
    },
    "opus-3": {
        "name": "Claude 3 Opus",
        "input": 15.00,
        "output": 75.00,
        "cache_write": 18.75,
        "cache_read": 1.50,
        "context": 200_000,
    },
    "sonnet-3.5": {
        "name": "Claude 3.5 Sonnet",
        "input": 3.00,
        "output": 15.00,
        "cache_write": 3.75,
        "cache_read": 0.30,
        "context": 200_000,
    },
    "sonnet-3.5v2": {
        "name": "Claude 3.5 Sonnet v2",
        "input": 3.00,
        "output": 15.00,
        "cache_write": 3.75,
        "cache_read": 0.30,
        "context": 200_000,
    },
}

# map API model IDs to our short keys
MODEL_ALIASES = {
    "claude-opus-4-6": "opus-4",
    "claude-opus-4-20250514": "opus-4",
    "claude-sonnet-4-6": "sonnet-4",
    "claude-sonnet-4-20250514": "sonnet-4",
    "claude-haiku-4-5-20251001": "haiku-4.5",
    "claude-3-5-haiku-20241022": "haiku-3.5",
    "claude-3-opus-20240229": "opus-3",
    "claude-3-5-sonnet-20240620": "sonnet-3.5",
    "claude-3-5-sonnet-20241022": "sonnet-3.5v2",
    "claude-3-5-sonnet-v2-20241022": "sonnet-3.5v2",
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


def resolve_api_model(api_model: str) -> str | None:
    """map an API model ID like 'claude-opus-4-6' to our short key."""
    if api_model in MODEL_ALIASES:
        return MODEL_ALIASES[api_model]
    # try partial match
    lower = api_model.lower()
    for alias, key in MODEL_ALIASES.items():
        if alias in lower or lower in alias:
            return key
    return None


def calc_cost(input_tokens: int, output_tokens: int, model: str,
              cache_write_tokens: int = 0, cache_read_tokens: int = 0) -> dict:
    """calculate cost with optional cache token breakdown.

    returns dict with: total, input_cost, output_cost, cache_write_cost, cache_read_cost
    """
    pricing = MODELS[model]
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    cache_write_cost = (cache_write_tokens / 1_000_000) * pricing["cache_write"]
    cache_read_cost = (cache_read_tokens / 1_000_000) * pricing["cache_read"]
    total = input_cost + output_cost + cache_write_cost + cache_read_cost
    return {
        "total": total,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "cache_write_cost": cache_write_cost,
        "cache_read_cost": cache_read_cost,
    }


def calc_cost_simple(input_tokens: int, output_tokens: int, model: str) -> tuple[float, float, float]:
    """simple version: returns (total_cost, input_cost, output_cost). no cache."""
    pricing = MODELS[model]
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost, input_cost, output_cost


def estimate_tokens(text: str) -> int:
    """rough char-based token estimate."""
    return max(1, len(text) // CHARS_PER_TOKEN)
