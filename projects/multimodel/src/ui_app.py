# ui_app.py — Colab-stable: статичные слоты под контролы и ответ
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict

from IPython.display import display, HTML
import ipywidgets as W

# Colab widgets
try:
    from google.colab import output as colab_output  # type: ignore
    colab_output.enable_custom_widget_manager()
except Exception:
    pass

from src.config import load_secrets
from src.gpt_router import run_router

_HISTORY: List[Dict] = []

def _style_css() -> str:
    return """
    <style>
      .gptr-wrap { font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; line-height:1.35; }
      .gptr-title { font-weight: 700; color:#e5e7eb; margin: 6px 0 10px; font-size: 20px; } /* светлый */
      .gptr-answer { border:1px solid #22c55e; background:#ecfdf5; color:#064e3b; padding:12px; border-radius:12px; }
      .gptr-info { border:1px solid #3b82f6; background:#eff6ff; color:#1e40af; padding:10px; border-radius:12px; margin-top:10px; }
      .gptr-table { width:100%; border-collapse:collapse; margin-top:10px; }
      .gptr-table th { background:#0ea5e9; color:white; padding:6px 8px; text-align:right; }
      .gptr-table td { border-top:1px solid #e5e7eb; padding:6px 8px; text-align:right; color:#e5e7eb; }
      .gptr-table td:first-child, .gptr-table th:first-child { text-align:left; }
      .badge { display:inline-block; padding:2px 8px; border-radius:999px; font-weight:600; font-size:12px; }
      .badge-easy { background:#dcfce7; color:#16a34a; border:1px solid #16a34a; }
      .badge-hard { background:#fee2e2; color:#dc2626; border:1px solid #dc2626; }
      .muted { color:#9ca3af; font-size:12px; }
      .row { margin-top:6px; }
      .qtitle { margin-top:12px; font-weight:600; color:#e5e7eb; } /* светлый */
    </style>
    """

def _metrics_table_html(result) -> str:
    s0, s1 = result.stages
    total_in = s0.usage.prompt_tokens + s1.usage.prompt_tokens
    total_out = s0.usage.completion_tokens + s1.usage.completion_tokens
    return f"""
    <table class="gptr-table">
      <thead>
        <tr>
          <th>Stage</th><th>Model</th><th>In Tokens</th><th>Out Tokens</th><th>Time, s</th><th>Cost USD</th><th>Cost RUB</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>classifier</td><td>{s0.model}</td><td>{s0.usage.prompt_tokens}</td><td>{s0.usage.completion_tokens}</td>
          <td>{s0.elapsed_sec:.2f}</td><td>{s0.cost_usd:.6f}</td><td>{s0.cost_usd * result.usd_to_rub:.6f}</td>
        </tr>
        <tr>
          <td>answer</td><td>{s1.model}</td><td>{s1.usage.prompt_tokens}</td><td>{s1.usage.completion_tokens}</td>
          <td>{s1.elapsed_sec:.2f}</td><td>{s1.cost_usd:.6f}</td><td>{s1.cost_usd * result.usd_to_rub:.6f}</td>
        </tr>
        <tr style="font-weight:700;">
          <td>TOTAL</td><td>-</td><td>{total_in}</td><td>{total_out}</td>
          <td>-</td><td>{result.total_usd:.6f}</td><td>{result.total_rub:.6f}</td>
        </tr>
      </tbody>
    </table>
    """

def _render_result_html(result, user_text: str) -> str:
    badge_class = "easy" if result.difficulty == "лёгкий" else "hard"
    badge = f'<span class="badge badge-{badge_class}">{result.difficulty}</span>'
    dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    table = _metrics_table_html(result)
    return _style_css() + f"""
    <div class="gptr-wrap">
      <div class="gptr-title">Ответ модели</div>
      <div class="gptr-answer">{result.answer_text.strip()}</div>
      <div class="gptr-title">Метрики и стоимость</div>
      {table}
      <div class="gptr-title">Информация</div>
      <div class="gptr-info">
        <div class="row">Классификация: {badge}</div>
        <div class="row">Курс USD→RUB: <b>{result.usd_to_rub}</b> <span class="muted">(обновлено {result.rate_time})</span></div>
        <div class="row">Итог: <b>{result.total_usd:.6f} $</b> | <b>{result.total_rub:.6f} ₽</b></div>
        <div class="row muted">Время и дата запроса: {dt_str}</div>
      </div>
    </div>
    """

def _render_history_html(history: List[Dict]) -> str:
    if not history:
        return _style_css() + '<div class="gptr-wrap"><div class="gptr-title">Архив пуст</div></div>'
    parts = [_style_css(), '<div class="gptr-wrap"><div class="gptr-title">Архив запросов</div>']
    for i, item in enumerate(history, 1):
        parts.append(f'<div class="qtitle">#{i}. Вопрос:</div>')
        parts.append(f'<div class="gptr-answer" style="border-color:#94a3b8;background:#f8fafc;color:#0f172a;">{item["question"]}</div>')
        parts.append(item["html"])
        parts.append('<hr style="margin:14px 0;border:none;border-top:1px solid #e5e7eb;">')
    parts.append('</div>')
    return "".join(parts)

def launch_ui():
    """Домашний экран → пароль → постоянные СЛОТЫ: controls_slot (VBox) и html_slot (HTML)."""
    host_box = W.VBox([])
    display(host_box)

    def show_home():
        start_btn = W.Button(description="Запустить программу", button_style="success", icon="play")
        history_btn = W.Button(description="Архив запросов", button_style="info", icon="list")
        out = W.Output()
        host_box.children = (W.HBox([start_btn, history_btn]), out)

        def on_start(_b):
            run_session()

        def on_hist(_b):
            with out:
                out.clear_output()
                display(HTML(_render_history_html(_HISTORY)))

        start_btn.on_click(on_start)
        history_btn.on_click(on_hist)

    def run_session():
        secrets: Optional[dict] = None
        alive = True

        # Статичные слоты
        controls_slot = W.VBox([])  # сюда будем класть [h3, textarea, buttons]
        html_slot = W.HTML(value=_style_css() + "<div class='gptr-wrap'><div class='gptr-title'>Готов к работе.</div></div>")

        # Шаг 1: пароль
        title = W.HTML("<h3>🔐 Введите пароль для расшифровки секретов</h3>")
        pwd = W.Password(description="Пароль:", placeholder="Введите пароль…", layout=W.Layout(width="50%"))
        unlock_btn = W.Button(description="Разблокировать", button_style="success", icon="unlock")
        exit_btn_top = W.Button(description="Выйти из программы", button_style="danger", icon="sign-out")
        msg = W.Output()
        step1_box = W.VBox([title, W.HBox([pwd, unlock_btn, exit_btn_top]), msg])
        host_box.children = (step1_box,)

        def go_home():
            nonlocal alive
            alive = False
            host_box.children = ()
            show_home()

        def do_exit(_b=None):
            html_slot.value = _style_css() + "<div class='gptr-wrap'><div class='gptr-title'>🚪 Сессия завершена.</div></div>"
            controls_slot.children = ()
            go_home()

        def make_controls():
            q = W.Textarea(placeholder="Введите ваш запрос…",
                           layout=W.Layout(width="100%", height="100px"))
            send = W.Button(description="Отправить", button_style="success", icon="paper-plane")
            exit_btn = W.Button(description="Выйти из программы", button_style="danger", icon="sign-out")

            def on_send(_b):
                _handle_question(q.value)

            send.on_click(on_send)
            exit_btn.on_click(do_exit)

            controls_slot.children = [
                W.HTML("<h3 class='qtitle'>💬 Введите запрос</h3>"),
                q,
                W.HBox([send, exit_btn])
            ]

        def _handle_question(text: str):
            if not alive:
                return
            if not secrets:
                html_slot.value = _style_css() + "<div class='gptr-wrap'><div class='gptr-title'>❌ Секреты не разблокированы.</div></div>"
                return
            text = (text or '').strip()
            if not text:
                html_slot.value = _style_css() + "<div class='gptr-wrap'><div class='gptr-title'>⚠️ Введите запрос.</div></div>"
                return

            html_slot.value = _style_css() + "<div class='gptr-wrap'><div class='gptr-title'>⏳ Выполняю запрос…</div></div>"
            try:
                result = run_router(text, secrets)
            except Exception as e:
                html_slot.value = _style_css() + f"<div class='gptr-wrap'><div class='gptr-title'>❌ Ошибка: {e}</div></div>"
                return

            html = _render_result_html(result, text)
            _HISTORY.append({"question": text, "html": html})
            html_slot.value = html

            # просто пересобираем контролы в том же слоте
            make_controls()

        def on_unlock(_b):
            nonlocal secrets
            with msg:
                msg.clear_output()
                print("⏳ Проверяем пароль…")
            try:
                secrets = load_secrets(passphrase=pwd.value)
            except Exception as e:
                with msg:
                    msg.clear_output()
                    print(f"❌ Ошибка: {e}")
                return

            session_box = W.VBox([
                controls_slot,  # всегда сверху
                html_slot       # всегда снизу
            ])
            host_box.children = (session_box,)

            with msg:
                msg.clear_output()

            make_controls()  # первый показ полей

        unlock_btn.on_click(on_unlock)
        exit_btn_top.on_click(do_exit)

    show_home()
