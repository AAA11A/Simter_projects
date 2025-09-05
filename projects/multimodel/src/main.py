from __future__ import annotations
import argparse
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.config import load_secrets
from src.gpt_router import run_router, StageResult

console = Console()

def _build_metrics_table(stages: tuple[StageResult, StageResult], usd_to_rub: float, total_usd: float, total_rub: float) -> Table:
    table = Table(title="Метрики и стоимость", style="cyan")
    table.add_column("Stage", style="bold magenta")
    table.add_column("Model", style="green")
    table.add_column("In Tokens", justify="right")
    table.add_column("Out Tokens", justify="right")
    table.add_column("Time, s", justify="right")
    table.add_column("Cost USD", justify="right")
    table.add_column("Cost RUB", justify="right")

    total_in = total_out = 0
    for s in stages:
        total_in += s.usage.prompt_tokens
        total_out += s.usage.completion_tokens
        table.add_row(
            s.stage,
            s.model,
            str(s.usage.prompt_tokens),
            str(s.usage.completion_tokens),
            f"{s.elapsed_sec:.2f}",
            f"{s.cost_usd:.6f}",
            f"{s.cost_usd * usd_to_rub:.6f}",
        )

    table.add_row(
        "TOTAL",
        "-",
        str(total_in),
        str(total_out),
        "-",
        f"{total_usd:.6f}",
        f"{total_rub:.6f}",
        style="bold yellow"
    )
    return table

def main():
    parser = argparse.ArgumentParser(description="GPT Router (Colab)")
    parser.add_argument("--file", type=str, default="", help="Путь к файлу с запросом")
    parser.add_argument("--text", type=str, default="", help="Запрос напрямую")
    parser.add_argument("--passphrase", type=str, default=None, help="Пароль для secrets.enc")
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        text = args.text or input("Вставьте ваш запрос и нажмите Enter: ").strip()

    secrets = load_secrets(passphrase=args.passphrase)
    result = run_router(text, secrets)

    # === Ответ модели ===
    console.print(Panel(Text(result.answer_text.strip(), style="bold white"), title="[green]Ответ модели[/green]", border_style="green"))

    # === Метрики ===
    metrics_table = _build_metrics_table(result.stages, result.usd_to_rub, result.total_usd, result.total_rub)
    console.print(metrics_table)

    # === Информация ===
    dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_text = Text()
    info_text.append(f"Сложность запроса: {result.difficulty}\n", style="bold cyan")
    info_text.append(f"Курс USD→RUB: {result.usd_to_rub} (обновлено {result.rate_time})\n", style="yellow")
    info_text.append(f"Итоговая стоимость: {result.total_usd:.6f} $ | {result.total_rub:.6f} ₽\n", style="bold magenta")
    info_text.append(f"Время и дата запроса: {dt_str}", style="italic white")

    console.print(Panel(info_text, title="[blue]Информация[/blue]", border_style="blue"))

if __name__ == "__main__":
    main()
