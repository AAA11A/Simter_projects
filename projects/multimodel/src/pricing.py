PRICING = {
    "gpt-5": {"input_per_million": 1.25, "output_per_million": 10.00},
    "gpt-5-nano": {"input_per_million": 0.05, "output_per_million": 0.40},
    "gpt-5-mini": {"input_per_million": 0.25, "output_per_million": 2.00},
}

def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Считает стоимость запроса в $ по usage токенов и модели.
    Формула: input_toks/1e6*input_price + output_toks/1e6*output_price
    """
    p = PRICING[model]
    return (prompt_tokens / 1_000_000) * p["input_per_million"] +            (completion_tokens / 1_000_000) * p["output_per_million"]