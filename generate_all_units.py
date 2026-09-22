import os
import json
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions_all.json")
TASKS_FILE = os.path.join(BASE_DIR, "tasks_all.json")
HTML_DIR = os.path.join(BASE_DIR, "guias_html")
MD_DIR = os.path.join(BASE_DIR, "guias_md")

os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(MD_DIR, exist_ok=True)

SKILL_CONFIG = {
    "grammar": {"title": "🧠 Grammar (Estructuras Gramaticales)", "badge": "Grammar", "color": "#2563eb"},
    "vocabulary": {"title": "📖 Vocabulary (Vocabulario)", "badge": "Vocabulary", "color": "#059669"},
    "reading": {"title": "📚 Reading (Comprensión Lectora)", "badge": "Reading", "color": "#d97706"},
    "listening": {"title": "🎧 Listening (Comprensión Auditiva)", "badge": "Listening", "color": "#7c3aed"},
    "writing": {"title": "✍️ Writing (Expresión Escrita)", "badge": "Writing", "color": "#db2777"},
}

BOOK_NAMES = {
    1: "📗 Book 1 (A1.1 - Elementary)",
    2: "📘 Book 2 (A1.2 - High Elementary)",
    3: "📙 Book 3 (A2.1 - Pre-Intermediate)",
    4: "📕 Book 4 (A2.2 - Intermediate)",
    5: "📓 Book 5 (B1.1 - Independent)",
}

def format_question_md_html(q, idx):
    q_type = q.get("type", "")
    q_text = (q.get("question") or "").strip()
    q_desc = (q.get("description") or "").strip()

    md = [f"#### {idx}. {q_text}"]
    if q_desc:
        md.append(f"> ℹ️ *{q_desc}*\n")

    html = [
        f'<div class="question-card">',
        f'<div class="q-header"><span class="q-badge">{q_type}</span> <span class="q-num">#{idx}</span> {q_text}</div>'
    ]
    if q_desc:
        html.append(f'<div class="q-desc">{q_desc}</div>')

    if q_type in ("opcion_correcta_1", "opcion_correcta_n"):
        options = q.get("options") or []
        html.append('<ul class="options-list">')
        for opt in options:
            if isinstance(opt, dict):
                item = opt.get("item", "")
                is_correct = opt.get("answer") is True
                if is_correct:
                    md.append(f"- [x] **{item}** ✅ *(Respuesta Correcta)*")
                    html.append(f'<li class="opt correct"><strong>{item}</strong> <span class="badge-correct">CORRECTA</span></li>')
                else:
                    md.append(f"- [ ] {item}")
                    html.append(f'<li class="opt">{item}</li>')
        html.append('</ul>')

    elif q_type == "true_false":
        body = q.get("body") or []
        html.append('<div class="tf-block">')
        for b in body:
            prompt = b.get("item", [""])[0] if isinstance(b.get("item"), list) else str(b.get("item"))
            ans_data = b.get("answer") or []
            correct_val = "Verdadero (True)"
            for opt in ans_data:
                if len(opt) >= 2 and opt[1] is True:
                    correct_val = "Verdadero (True)" if opt[0] == "T" else "Falso (False)"
            md.append(f"- *\"{prompt}\"* ➔ **{correct_val}** ✅")
            html.append(f'<p><strong>• {prompt}</strong> ➔ <span class="badge-correct">{correct_val}</span></p>')
        html.append('</div>')

    elif q_type in ("emparejar", "emparejar_img"):
        body = q.get("body") or []
        html.append('<table class="match-table"><thead><tr><th>Elemento / Pista</th><th>Respuesta Correcta</th></tr></thead><tbody>')
        md.append("| Elemento / Pista | Respuesta Correcta |")
        md.append("| :--- | :--- |")
        for b in body:
            prompt = b.get("item", [""])[0] if isinstance(b.get("item"), list) else str(b.get("item"))
            ans = b.get("answer", "")
            if len(prompt) > 25 and not " " in prompt:
                prompt = "*(Imagen / Código de referencia)*"
            md.append(f"| {prompt} | **{ans}** ✅ |")
            html.append(f'<tr><td>{prompt}</td><td class="match-ans"><strong>{ans}</strong> ✅</td></tr>')
        html.append('</tbody></table>')

    elif q_type == "ordenar":
        options = q.get("options") or []
        for row in options:
            if isinstance(row, list):
                sorted_words = sorted(row, key=lambda x: x.get("answer", 0) if isinstance(x, dict) else 0)
                sentence = " ".join(x.get("item", "") for x in sorted_words if isinstance(x, dict))
                md.append(f"- 🔤 **Oración ordenada:** *\"{sentence}\"* ✅")
                html.append(f'<div class="order-box">🔤 <strong>Oración ordenada:</strong> <em>"{sentence}"</em> ✅</div>')

    elif q_type == "completar_texto":
        body = q.get("body") or []
        html.append('<ul class="fill-list">')
        for b in body:
            item = b.get("item", [""])[0] if isinstance(b.get("item"), list) else str(b.get("item"))
            ans = b.get("answer", "")
            md.append(f"- Pista: `{item}` ➔ **{ans}** ✅")
            html.append(f'<li><code>{item}</code> ➔ <strong>{ans}</strong> <span class="badge-correct">COMPLETO</span></li>')
        html.append('</ul>')

    html.append('</div>')
    return "\n".join(md) + "\n", "\n".join(html)

def generate_all():
    print("[1/4] Cargando base de datos...")
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    # Organizar tareas por unidad
    unit_tasks = {}
    for tid_str, info in tasks.items():
        uid = info.get("unit_id")
        if uid is not None:
            unit_tasks.setdefault(uid, []).append((int(tid_str), info))

    # Mapear preguntas por task_id
    questions_by_task = {}
    for q in questions:
        tid = q.get("task_id")
        if tid:
            questions_by_task.setdefault(tid, []).append(q)

    print(f"[2/4] Generando guías para 20 unidades...")
    units_summary = []

    for uid in range(1, 21):
        t_list = unit_tasks.get(uid, [])
        # Ordenar tareas por habilidad
        skill_order = ["grammar", "vocabulary", "reading", "listening", "writing"]
        t_list.sort(key=lambda x: (
            skill_order.index(x[1].get("type", "other")) if x[1].get("type") in skill_order else 99,
            x[0]
        ))

        # Calcular número de libro (1 a 4: Book 1, 5 a 8: Book 2, etc.)
        book_num = ((uid - 1) // 4) + 1
        book_title = BOOK_NAMES.get(book_num, f"Book {book_num}")

        total_q_unit = sum(len(questions_by_task.get(tid, [])) for tid, _ in t_list)

        units_summary.append({
            "unit": uid,
            "book_num": book_num,
            "book_title": book_title,
            "tasks_count": len(t_list),
            "questions_count": total_q_unit,
            "file_html": f"Unidad_{uid:02d}.html",
            "file_md": f"Unidad_{uid:02d}.md",
        })

        # --- Generar Markdown ---
        md_lines = [
            f"# 📘 Guía de Estudio Oficial: UTM Simulador de Inglés",
            f"## Unidad {uid} • {book_title}",
            f"> Total de Tareas: **{len(t_list)}** | Total de Preguntas: **{total_q_unit}**\n",
            "---\n"
        ]

        # --- Generar HTML ---
        html_sections = []
        current_skill = None

        for tid, tinfo in t_list:
            stype = tinfo.get("type", "general")
            if stype != current_skill:
                if current_skill is not None:
                    html_sections.append('</div>')  # Cerrar skill anterior
                current_skill = stype
                sconf = SKILL_CONFIG.get(stype, {"title": stype.capitalize(), "color": "#334155"})
                md_lines.append(f"\n## {sconf['title']}\n")
                html_sections.append(f'<div class="skill-section"><h2 style="border-left-color: {sconf["color"]}">{sconf["title"]}</h2>')

            topic_data = tinfo.get("topic") or {}
            topic_str = topic_data.get("top", f"Tarea #{tid}") if isinstance(topic_data, dict) else str(topic_data)
            obj_data = tinfo.get("objetive") or {}
            obj_str = obj_data.get("text", "") if isinstance(obj_data, dict) else str(obj_data)
            expl_str = (tinfo.get("explanation") or "").strip()

            md_lines.append(f"\n### 📌 Tarea #{tid}: {topic_str}")
            if obj_str:
                md_lines.append(f"🎯 **Objetivo:** {obj_str}")
            if expl_str and expl_str.lower() != "none":
                md_lines.append(f"💡 **Explicación:** {expl_str}\n")

            html_sections.append(f'<div class="task-card">')
            html_sections.append(f'<h3>📌 Tarea #{tid}: {topic_str}</h3>')
            if obj_str:
                html_sections.append(f'<p class="task-obj">🎯 <strong>Objetivo:</strong> {obj_str}</p>')
            if expl_str and expl_str.lower() != "none":
                html_sections.append(f'<div class="task-expl">💡 <strong>Explicación:</strong> {expl_str}</div>')

            t_questions = questions_by_task.get(tid, [])
            for q_i, q in enumerate(t_questions, 1):
                q_md, q_html = format_question_md_html(q, q_i)
                md_lines.append(q_md)
                html_sections.append(q_html)

            html_sections.append('</div>')

        if current_skill is not None:
            html_sections.append('</div>')

        # Escribir archivo Markdown
        md_path = os.path.join(MD_DIR, f"Unidad_{uid:02d}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        # Escribir archivo HTML
        html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unidad {uid} • {book_title} - Guía de Inglés UTM</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .top-nav {{
            max-width: 900px;
            margin: 0 auto 16px auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .back-btn, .print-btn {{
            text-decoration: none;
            background: #ffffff;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 500;
            font-size: 14px;
            transition: all 0.2s;
            cursor: pointer;
        }}
        .back-btn:hover, .print-btn:hover {{
            background: #f1f5f9;
            border-color: #94a3b8;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 4px 25px rgba(0,0,0,0.06);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 24px;
            margin-bottom: 32px;
        }}
        .header h1 {{
            color: #0f172a;
            font-size: 26px;
            margin: 0 0 6px 0;
        }}
        .header .subtitle {{
            color: #2563eb;
            font-weight: 600;
            font-size: 16px;
            margin-bottom: 8px;
        }}
        .header .stats {{
            display: inline-flex;
            gap: 16px;
            background: #f1f5f9;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 14px;
            color: #475569;
        }}
        .skill-section {{
            margin-top: 40px;
        }}
        .skill-section h2 {{
            background: #f8fafc;
            color: #0f172a;
            padding: 12px 18px;
            border-radius: 8px;
            border-left: 6px solid #2563eb;
            font-size: 20px;
            margin-bottom: 20px;
        }}
        .task-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            transition: box-shadow 0.2s;
        }}
        .task-card:hover {{
            box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        }}
        .task-card h3 {{
            color: #1e293b;
            margin-top: 0;
            font-size: 18px;
        }}
        .task-obj {{
            font-size: 14px;
            color: #475569;
            background: #f8fafc;
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 10px;
        }}
        .task-expl {{
            font-size: 14px;
            color: #0369a1;
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 18px;
        }}
        .question-card {{
            background: #fafafa;
            border-left: 4px solid #3b82f6;
            padding: 14px 18px;
            margin-bottom: 16px;
            border-radius: 0 8px 8px 0;
        }}
        .q-header {{
            font-weight: 600;
            font-size: 15px;
            margin-bottom: 8px;
            color: #0f172a;
        }}
        .q-badge {{
            font-size: 11px;
            text-transform: uppercase;
            background: #e2e8f0;
            color: #475569;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .q-num {{
            color: #3b82f6;
            margin-right: 4px;
        }}
        .q-desc {{
            font-size: 13px;
            color: #64748b;
            font-style: italic;
            margin-bottom: 8px;
        }}
        .options-list {{
            list-style: none;
            padding-left: 0;
            margin: 8px 0 0 0;
        }}
        .opt {{
            padding: 8px 12px;
            margin-bottom: 6px;
            border-radius: 6px;
            font-size: 14px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
        }}
        .opt.correct {{
            background: #ecfdf5;
            border-color: #10b981;
            color: #065f46;
            font-weight: 600;
        }}
        .badge-correct {{
            background: #10b981;
            color: #ffffff;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 12px;
            float: right;
            font-weight: 600;
        }}
        .match-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
            font-size: 14px;
        }}
        .match-table th, .match-table td {{
            border: 1px solid #cbd5e1;
            padding: 8px 12px;
            text-align: left;
        }}
        .match-table th {{
            background: #f1f5f9;
            font-weight: 600;
        }}
        .match-ans {{
            color: #065f46;
            background: #ecfdf5;
            font-weight: 600;
        }}
        .order-box {{
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            padding: 10px 14px;
            border-radius: 6px;
            color: #1e40af;
            font-size: 14px;
            margin-top: 6px;
        }}
        .fill-list {{
            list-style: none;
            padding-left: 0;
            margin: 8px 0 0 0;
        }}
        .fill-list li {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 6px 12px;
            border-radius: 6px;
            margin-bottom: 6px;
            font-size: 14px;
        }}
        @media print {{
            body {{ background: #ffffff; padding: 0; }}
            .top-nav {{ display: none; }}
            .container {{ box-shadow: none; max-width: 100%; padding: 0; }}
            .task-card {{ page-break-inside: avoid; }}
            .question-card {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="top-nav">
        <a href="../index.html" class="back-btn">← Volver al Portal General</a>
        <button onclick="window.print()" class="print-btn">🖨️ Guardar / Imprimir PDF</button>
    </div>
    <div class="container">
        <div class="header">
            <h1>📘 Universidad Técnica de Manabí</h1>
            <div class="subtitle">Simulador de Inglés • Unidad {uid} • {book_title}</div>
            <div class="stats">
                <span>📋 {len(t_list)} Tareas</span>
                <span>❓ {total_q_unit} Preguntas Verificadas</span>
            </div>
        </div>
        {''.join(html_sections)}
    </div>
</body>
</html>"""

        html_path = os.path.join(HTML_DIR, f"Unidad_{uid:02d}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_doc)

    print("[3/4] Generando Portal Principal index.html...")
    generate_portal(units_summary)
    print("[4/4] ¡Proceso completado con éxito!")

def generate_portal(units):
    total_preguntas = sum(u["questions_count"] for u in units)
    total_tareas = sum(u["tasks_count"] for u in units)

    cards_html = []
    for u in units:
        cards_html.append(f"""
        <div class="unit-card" data-book="{u['book_num']}" data-unit="{u['unit']}">
            <div class="card-header">
                <span class="unit-badge">Unidad {u['unit']:02d}</span>
                <span class="book-tag">{u['book_title'].split('(')[0].strip()}</span>
            </div>
            <div class="card-meta">
                <span>📋 {u['tasks_count']} Tareas</span>
                <span>❓ {u['questions_count']} Preguntas</span>
            </div>
            <div class="card-actions">
                <a href="guias_html/{u['file_html']}" class="btn btn-primary">📖 Ver Guía y Respuestas</a>
                <a href="guias_html/{u['file_html']}" onclick="setTimeout(()=>window.open('guias_html/{u['file_html']}'),100)" class="btn btn-secondary">🖨️ PDF</a>
            </div>
        </div>
        """)

    index_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portal de Estudio: Simulador de Inglés UTM</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #f1f5f9;
            color: #0f172a;
            margin: 0;
            padding: 30px 20px;
        }}
        .hero {{
            max-width: 1100px;
            margin: 0 auto 30px auto;
            text-align: center;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: #ffffff;
            padding: 40px 20px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }}
        .hero h1 {{
            font-size: 32px;
            margin: 0 0 10px 0;
            font-weight: 800;
        }}
        .hero p {{
            font-size: 16px;
            color: #94a3b8;
            margin: 0 0 20px 0;
        }}
        .hero-stats {{
            display: inline-flex;
            gap: 20px;
            background: rgba(255,255,255,0.1);
            padding: 10px 24px;
            border-radius: 30px;
            font-size: 15px;
            backdrop-filter: blur(5px);
        }}
        .search-bar {{
            max-width: 600px;
            margin: 20px auto 0 auto;
        }}
        .search-bar input {{
            width: 100%;
            padding: 14px 20px;
            border-radius: 12px;
            border: none;
            font-size: 15px;
            outline: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        .grid {{
            max-width: 1100px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
        }}
        .unit-card {{
            background: #ffffff;
            border-radius: 14px;
            padding: 20px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .unit-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.08);
            border-color: #cbd5e1;
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .unit-badge {{
            background: #2563eb;
            color: #ffffff;
            padding: 4px 10px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 13px;
        }}
        .book-tag {{
            font-size: 12px;
            color: #64748b;
            font-weight: 500;
        }}
        .card-meta {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #475569;
            background: #f8fafc;
            padding: 8px 12px;
            border-radius: 8px;
            margin-bottom: 16px;
        }}
        .card-actions {{
            display: flex;
            gap: 8px;
        }}
        .btn {{
            text-decoration: none;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            text-align: center;
            transition: background 0.2s;
        }}
        .btn-primary {{
            flex: 1;
            background: #0f172a;
            color: #ffffff;
        }}
        .btn-primary:hover {{
            background: #2563eb;
        }}
        .btn-secondary {{
            background: #f1f5f9;
            color: #334155;
            border: 1px solid #cbd5e1;
        }}
        .btn-secondary:hover {{
            background: #e2e8f0;
        }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>📘 Portal de Estudio • Inglés UTM</h1>
        <p>Banco Completo de Preguntas, Explicaciones y Respuestas Verificadas (Aulas Lenguas)</p>
        <div class="hero-stats">
            <span>📚 5 Libros Completos</span>
            <span>🎯 20 Unidades</span>
            <span>📋 {total_tareas} Tareas</span>
            <span>❓ {total_preguntas} Preguntas</span>
        </div>
        <div class="search-bar">
            <input type="text" id="filterInput" placeholder="Buscar por número de unidad o tema..." onkeyup="filterUnits()">
        </div>
    </div>

    <div class="grid" id="unitsGrid">
        {''.join(cards_html)}
    </div>

    <script>
        function filterUnits() {{
            let input = document.getElementById('filterInput').value.toLowerCase();
            let cards = document.getElementsByClassName('unit-card');
            for (let card of cards) {{
                let text = card.innerText.toLowerCase();
                card.style.display = text.includes(input) ? 'flex' : 'none';
            }}
        }}
    </script>
</body>
</html>"""

    index_path = os.path.join(BASE_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"[OK] Portal interactivo guardado en: {index_path}")

if __name__ == "__main__":
    generate_all()
