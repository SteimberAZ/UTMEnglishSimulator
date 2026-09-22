import json
import os
import urllib3
import requests

urllib3.disable_warnings()

API_BASE = "https://aulaslenguas.utm.edu.ec:7000/api"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOjYzMzcsIm1haWwiOiJyYXJ0ZWFnYTYxNjFAdXRtLmVkdS5lYyIsInJvbCI6WyJFc3R1ZGlhbnRlIl0sImlkcGVyc29uYWwiOjE3Njk3OCwic2NvcGUiOiJTVFVERU5UX1BPUlRBTCIsIm1mYV92ZXJpZmllZCI6ZmFsc2UsImlhdCI6MTc5MDA1MjkyNywiZXhwIjoxNzkwMDYwMTI3fQ.15EvaN78tG2MSXhIlke61e2p6DU3esqCRgG2aWnNcu4"

def get_session():
    session = requests.Session()
    session.verify = False
    session.cookies.set("token", TOKEN, domain="aulaslenguas.utm.edu.ec")
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://aulaslenguas.utm.edu.ec:8443",
        "Referer": "https://aulaslenguas.utm.edu.ec:8443/",
    })
    return session

def format_question(q, idx):
    q_type = q.get("type", "")
    q_text = (q.get("question") or "").strip()
    q_desc = (q.get("description") or "").strip()

    md = []
    html = []

    header_title = f"Pregunta {idx}: {q_text}"
    md.append(f"#### {idx}. {q_text}")
    if q_desc:
        md.append(f"> ℹ️ *{q_desc}*\n")

    html_content = [f'<div class="question-card"><div class="q-header"><span class="q-badge">{q_type}</span> <span class="q-num">#{idx}</span> {q_text}</div>']
    if q_desc:
        html_content.append(f'<div class="q-desc">{q_desc}</div>')

    if q_type in ("opcion_correcta_1", "opcion_correcta_n"):
        options = q.get("options") or []
        html_content.append('<ul class="options-list">')
        for opt in options:
            if isinstance(opt, dict):
                item = opt.get("item", "")
                is_correct = opt.get("answer") is True
                if is_correct:
                    md.append(f"- [x] **{item}** ✅ *(Respuesta Correcta)*")
                    html_content.append(f'<li class="opt correct"><strong>{item}</strong> <span class="badge-correct">CORRECTA</span></li>')
                else:
                    md.append(f"- [ ] {item}")
                    html_content.append(f'<li class="opt">{item}</li>')
        html_content.append('</ul>')

    elif q_type == "true_false":
        body = q.get("body") or []
        html_content.append('<div class="tf-block">')
        for b in body:
            prompt = b.get("item", [""])[0] if isinstance(b.get("item"), list) else str(b.get("item"))
            ans_data = b.get("answer") or []
            correct_val = "T"
            for opt in ans_data:
                if len(opt) >= 2 and opt[1] is True:
                    correct_val = "Verdadero (True)" if opt[0] == "T" else "Falso (False)"
            md.append(f"- *\"{prompt}\"* ➔ **{correct_val}** ✅")
            html_content.append(f'<p><strong>• {prompt}</strong> ➔ <span class="badge-correct">{correct_val}</span></p>')
        html_content.append('</div>')

    elif q_type in ("emparejar", "emparejar_img"):
        body = q.get("body") or []
        html_content.append('<table class="match-table"><thead><tr><th>Elemento / Pista</th><th>Respuesta Correcta</th></tr></thead><tbody>')
        md.append("| Elemento / Pista | Respuesta Correcta |")
        md.append("| :--- | :--- |")
        for b in body:
            prompt = b.get("item", [""])[0] if isinstance(b.get("item"), list) else str(b.get("item"))
            ans = b.get("answer", "")
            # Limpiar hashes de imágenes si los hay
            if len(prompt) > 25 and not " " in prompt:
                prompt = "*(Imagen de referencia)*"
            md.append(f"| {prompt} | **{ans}** ✅ |")
            html_content.append(f'<tr><td>{prompt}</td><td class="match-ans"><strong>{ans}</strong> ✅</td></tr>')
        html_content.append('</tbody></table>')

    elif q_type == "ordenar":
        options = q.get("options") or []
        for row in options:
            if isinstance(row, list):
                sorted_words = sorted(row, key=lambda x: x.get("answer", 0) if isinstance(x, dict) else 0)
                sentence = " ".join(x.get("item", "") for x in sorted_words if isinstance(x, dict))
                md.append(f"- 🔤 **Oración ordenada:** *\"{sentence}\"* ✅")
                html_content.append(f'<div class="order-box">🔤 <strong>Oración ordenada:</strong> <em>"{sentence}"</em> ✅</div>')

    elif q_type == "completar_texto":
        body = q.get("body") or []
        html_content.append('<ul class="fill-list">')
        for b in body:
            item = b.get("item", [""])[0] if isinstance(b.get("item"), list) else str(b.get("item"))
            ans = b.get("answer", "")
            md.append(f"- Pista: `{item}` ➔ **{ans}** ✅")
            html_content.append(f'<li><code>{item}</code> ➔ <strong>{ans}</strong> <span class="badge-correct">COMPLETO</span></li>')
        html_content.append('</ul>')

    html_content.append('</div>')
    return "\n".join(md) + "\n", "\n".join(html_content)

def build_guide_unit_1():
    session = get_session()
    print("Descargando preguntas de Book 1...")
    b1_questions = session.get(f"{API_BASE}/simulador/book/books/1").json()

    # Mapeo oficial de tareas Unidad 1
    tasks_u1 = [
        (1, "writing", "WHAT'S YOUR PHONE NUMBER?"),
        (2, "writing", "I'M FROM ECUADOR"),
        (3, "writing", "MY FAMILY"),
        (4, "vocabulary", "TIME FLIES"),
        (5, "vocabulary", "ECUADOR MY COUNTRY"),
        (6, "vocabulary", "My style"),
        (7, "vocabulary", "Family"),
        (8, "reading", "MEETING OTHER PEOPLE"),
        (9, "reading", "GETTING TO KNOW MY FAMILY"),
        (10, "grammar", "It is seven o'clock"),
        (11, "grammar", "I am 25 years old"),
        (12, "grammar", "She is my friend"),
        (13, "grammar", "I love them"),
        (309, "listening", "In the Hotel"),
        (310, "listening", "This is my family"),
        (313, "listening", "Weather Report"),
        (314, "listening", "Buying Things"),
    ]

    skill_names = {
        "writing": "✍️ Writing (Expresión Escrita)",
        "vocabulary": "📖 Vocabulary (Vocabulario)",
        "reading": "📚 Reading (Comprensión Lectora)",
        "grammar": "🧠 Grammar (Estructuras Gramaticales)",
        "listening": "🎧 Listening (Comprensión Auditiva)",
    }

    md_output = [
        "# 📘 Guía de Estudio Oficial: UTM Simulador de Inglés",
        "## Unidad 1: Basic Personal Information & Everyday Life\n",
        "> [!IMPORTANT]",
        "> Esta guía contiene todas las preguntas, explicaciones gramaticales y respuestas correctas verificadas del simulador institucional de la UTM para repasar y dominar los contenidos de la **Unidad 1**.\n",
        "---",
    ]

    html_body = []

    # Agrupar por habilidad
    from collections import defaultdict
    by_skill = defaultdict(list)
    for tid, stype, top in tasks_u1:
        by_skill[stype].append((tid, top))

    for stype in ["grammar", "vocabulary", "reading", "listening", "writing"]:
        stasks = by_skill.get(stype, [])
        if not stasks:
            continue

        skill_title = skill_names.get(stype, stype.capitalize())
        md_output.append(f"\n## {skill_title}\n")
        html_body.append(f'<div class="skill-section"><h2>{skill_title}</h2>')

        for tid, top in stasks:
            # Obtener detalles pedagógicos de la tarea
            info_resp = session.get(f"{API_BASE}/simulador/task/info/{tid}")
            info = info_resp.json() if info_resp.status_code == 200 else {}
            topic_str = info.get("topic", {}).get("top", top) if isinstance(info.get("topic"), dict) else top
            obj_str = info.get("objetive", {}).get("text", "") if isinstance(info.get("objetive"), dict) else ""
            expl_str = info.get("explanation", "") or ""

            md_output.append(f"\n### 📌 Tarea #{tid}: {topic_str}")
            if obj_str:
                md_output.append(f"🎯 **Objetivo:** {obj_str}")
            if expl_str and expl_str.lower() != "none":
                md_output.append(f"💡 **Explicación:** {expl_str}\n")

            html_body.append(f'<div class="task-card"><h3>📌 Tarea #{tid}: {topic_str}</h3>')
            if obj_str:
                html_body.append(f'<p class="task-obj">🎯 <strong>Objetivo:</strong> {obj_str}</p>')
            if expl_str and expl_str.lower() != "none":
                html_body.append(f'<div class="task-expl">💡 <strong>Explicación:</strong> {expl_str}</div>')

            # Preguntas de esta tarea
            t_questions = [q for q in b1_questions if q.get("task_id") == tid]
            for i, q in enumerate(t_questions, 1):
                q_md, q_html = format_question(q, i)
                md_output.append(q_md)
                html_body.append(q_html)

            html_body.append('</div>')
        html_body.append('</div>')

    # Guardar Markdown
    md_file = r"c:\Users\randy\Documents\NoWork\MyAplications\ingles\Guia_Estudio_Ingles_Unidad_1.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_output))
    print(f"[OK] Guia Markdown guardada: {md_file}")

    # Generar HTML estilizado e imprimible a PDF
    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Guía de Estudio - Inglés UTM Unidad 1</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            margin: 0;
            padding: 30px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 24px;
            margin-bottom: 32px;
        }}
        .header h1 {{
            color: #0f172a;
            font-size: 28px;
            margin: 0 0 8px 0;
        }}
        .header p {{
            color: #64748b;
            margin: 0;
            font-size: 16px;
        }}
        .skill-section {{
            margin-top: 40px;
        }}
        .skill-section h2 {{
            background: #f1f5f9;
            color: #0f172a;
            padding: 12px 18px;
            border-radius: 8px;
            border-left: 6px solid #2563eb;
            font-size: 20px;
        }}
        .task-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 28px;
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
        }}
        .task-expl {{
            font-size: 14px;
            color: #0369a1;
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
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
        }}
        .q-badge {{
            font-size: 11px;
            text-transform: uppercase;
            background: #e2e8f0;
            color: #475569;
            padding: 2px 6px;
            border-radius: 4px;
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
            padding: 6px 12px;
            margin-bottom: 4px;
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
        }}
        .match-ans {{
            color: #065f46;
            background: #ecfdf5;
        }}
        .order-box {{
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            padding: 10px 14px;
            border-radius: 6px;
            color: #1e40af;
            font-size: 14px;
        }}
        @media print {{
            body {{ background: #ffffff; padding: 0; }}
            .container {{ box-shadow: none; max-width: 100%; padding: 0; }}
            .task-card {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📘 Universidad Técnica de Manabí</h1>
            <p>Guía de Estudio Oficial • Simulador de Inglés (Aulas Lenguas) • Unidad 1</p>
        </div>
        {''.join(html_body)}
    </div>
</body>
</html>"""

    html_file = r"c:\Users\randy\Documents\NoWork\MyAplications\ingles\Guia_Estudio_Ingles_Unidad_1.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"[OK] Guia HTML/PDF guardada: {html_file}")

if __name__ == "__main__":
    build_guide_unit_1()
