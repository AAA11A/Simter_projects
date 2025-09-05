from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple
from time import perf_counter
from openai import OpenAI
from src.pricing import estimate_cost_usd
from src.currency import usd_to_rub_rate

@dataclass
class Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

@dataclass
class StageResult:
    stage: str
    model: str
    usage: Usage
    cost_usd: float
    elapsed_sec: float

@dataclass
class RouterResult:
    difficulty: str
    answer_text: str
    stages: Tuple[StageResult, StageResult]
    total_usd: float
    usd_to_rub: float
    rate_time: str
    total_rub: float

def _usage_from_resp(resp) -> Usage:
    u = resp.usage or {}
    return Usage(
        prompt_tokens=int(getattr(u, "prompt_tokens", 0) or 0),
        completion_tokens=int(getattr(u, "completion_tokens", 0) or 0),
        total_tokens=int(getattr(u, "total_tokens", 0) or 0),
    )

def classify_query(client: OpenAI, text: str) -> Tuple[str, StageResult]:
    sys_prompt = (
        "Ты — краткий классификатор. Ответь РОВНО одним словом: "
        "'easy' если запрос прост для малой модели, иначе 'hard'. "
        "Без пояснений и знаков препинания."
    )
    t0 = perf_counter()
    resp = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": text},
        ],
    )
    elapsed = perf_counter() - t0
    label_raw = (resp.choices[0].message.content or "").strip().lower()
    difficulty = "easy" if "easy" in label_raw or "лег" in label_raw else "hard"

    usage = _usage_from_resp(resp)
    cost = estimate_cost_usd("gpt-5-nano", usage.prompt_tokens, usage.completion_tokens)
    stage = StageResult(stage="classifier", model="gpt-5-nano", usage=usage, cost_usd=cost, elapsed_sec=elapsed)
    return difficulty, stage

def _trim_to_400_chars(text: str) -> str:
    if len(text) <= 400:
        return text
    cut = text[:400]
    last_space = cut.rfind(" ")
    if last_space > 300:
        cut = cut[:last_space]
    return cut.rstrip() + "…"

def generate_answer(client: OpenAI, model: str, text: str) -> Tuple[str, StageResult]:
    system_rules = (
        "Отвечай чётко и по делу. "
        "Дай связный ответ длиной от 300 до 400 символов на русском языке. "
        "Не добавляй преамбулы и заключения, сразу по сути."
    )
    t0 = perf_counter()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_rules},
            {"role": "user", "content": text},
        ],
    )
    elapsed = perf_counter() - t0

    raw_answer = resp.choices[0].message.content or ""
    answer = _trim_to_400_chars(raw_answer)

    usage = _usage_from_resp(resp)
    cost = estimate_cost_usd(model, usage.prompt_tokens, usage.completion_tokens)
    stage = StageResult(stage="answer", model=model, usage=usage, cost_usd=cost, elapsed_sec=elapsed)
    return answer, stage

def run_router(user_query: str, secrets: Dict[str, str]) -> RouterResult:
    client = OpenAI(api_key=secrets['OPENAI_API_KEY'])
    difficulty, stage_cls = classify_query(client, user_query)
    model = "gpt-5-nano" if difficulty == "easy" else "gpt-5"
    answer_text, stage_ans = generate_answer(client, model, user_query)
    rate, rate_time = usd_to_rub_rate(secrets["EXCHANGERATE_API_KEY"])
    total_usd = round(stage_cls.cost_usd + stage_ans.cost_usd, 8)
    total_rub = round(total_usd * rate, 6)
    return RouterResult(
        difficulty=difficulty,
        answer_text=answer_text,
        stages=(stage_cls, stage_ans),
        total_usd=total_usd,
        usd_to_rub=rate,
        rate_time=rate_time,
        total_rub=total_rub,
    )