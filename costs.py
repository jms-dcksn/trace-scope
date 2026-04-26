"""Hard-coded model pricing in USD per 1k tokens.

Bump entries when pricing changes — rates move slowly enough that fetching
live is overkill. Keys are the OpenAI model IDs without provider prefix.
"""

# (input_per_1k_usd, output_per_1k_usd) — placeholders; update as needed.
MODEL_COSTS: dict[str, tuple[float, float]] = {
    "gpt-5.4": (0.0025, 0.015),
    "gpt-5.4-mini": (0.00075, 0.0045),
    "gpt-5.4-nano": (0.0002, 0.00125),
}


def normalize_model(model: str) -> str:
    """Strip 'openai:' / similar provider prefix used by langchain.create_agent."""
    return model.split(":", 1)[1] if ":" in model else model


def cost_usd(model: str, tokens_in: int | None, tokens_out: int | None) -> float | None:
    if tokens_in is None and tokens_out is None:
        return None
    rates = MODEL_COSTS.get(normalize_model(model))
    if rates is None:
        return None
    in_rate, out_rate = rates
    return (tokens_in or 0) / 1000 * in_rate + (tokens_out or 0) / 1000 * out_rate
