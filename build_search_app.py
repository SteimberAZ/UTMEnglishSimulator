import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions_all.json")
TASKS_FILE = os.path.join(BASE_DIR, "tasks_all.json")
OUTPUT_HTML = os.path.join(BASE_DIR, "index.html")
OUTPUT_BUSCADOR = os.path.join(BASE_DIR, "buscador.html")

def build_search_data():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    search_index = []
    
    for q in questions:
        tid = q.get("task_id")
        tinfo = tasks.get(str(tid), {}) if tid else {}
        
        uid = tinfo.get("unit_id", 0)
        stype = tinfo.get("type", "general")
        topic_data = tinfo.get("topic") or {}
        topic_str = topic_data.get("top", "") if isinstance(topic_data, dict) else str(topic_data)
        expl_str = (tinfo.get("explanation") or "").strip()
        if expl_str.lower() == "none":
            expl_str = ""
            
        q_type = q.get("type", "")
        q_text = (q.get("question") or "").strip()
        q_desc = (q.get("description") or "").strip()

        correct_ans = []
        all_options = []

        if q_type in ("opcion_correcta_1", "opcion_correcta_n"):
            for opt in q.get("options") or []:
                if isinstance(opt, dict):
                    item = opt.get("item", "")
                    all_options.append(item)
                    if opt.get("answer") is True:
                        correct_ans.append(item)

        elif q_type == "true_false":
            for b in q.get("body") or []:
                prompt = b.get("item", [""])[0] if isinstance(b.get("item"), list) else str(b.get("item"))
                for opt in b.get("answer") or []:
                    if len(opt) >= 2 and opt[1] is True:
                        val = "Verdadero (True)" if opt[0] == "T" else "Falso (False)"
                        correct_ans.append(f"{prompt} ➔ {val}")

        elif q_type in ("emparejar", "emparejar_img"):
            for b in q.get("body") or []:
                prompt = b.get("item", [""])[0] if isinstance(b.get("item"), list) else str(b.get("item"))
                ans = b.get("answer", "")
                if len(prompt) > 25 and not " " in prompt:
                    prompt = "Imagen/Código"
                correct_ans.append(f"{prompt} ➔ {ans}")

        elif q_type == "ordenar":
            for row in q.get("options") or []:
                if isinstance(row, list):
                    sorted_words = sorted(row, key=lambda x: x.get("answer", 0) if isinstance(x, dict) else 0)
                    sentence = " ".join(x.get("item", "") for x in sorted_words if isinstance(x, dict))
                    correct_ans.append(sentence)

        elif q_type == "completar_texto":
            for b in q.get("body") or []:
                prompt = b.get("item", [""])[0] if isinstance(b.get("item"), list) else str(b.get("item"))
                ans = b.get("answer", "")
                correct_ans.append(f"{prompt} ➔ {ans}")

        u_obj = tinfo.get("unit") or {}
        book_id = u_obj.get("book", 0) if isinstance(u_obj, dict) else 0
        mod_id = u_obj.get("module", 0) if isinstance(u_obj, dict) else 0
        header_tag = f"{stype} book {book_id} mod {mod_id} unit {uid}".lower()

        searchable = f"{header_tag} {q_text} {q_desc} {topic_str} {' '.join(all_options)} {' '.join(correct_ans)}".lower()

        search_index.append({
            "id": q.get("_id"),
            "u": uid,
            "b": book_id,
            "m": mod_id,
            "s": stype,
            "tag": f"{stype.upper()} • B{book_id} M{mod_id} U{uid}",
            "top": topic_str,
            "exp": expl_str,
            "type": q_type,
            "q": q_text,
            "desc": q_desc,
            "opts": all_options,
            "ans": correct_ans,
            "k": searchable
        })

    return search_index

def generate_html_search_app(data):
    json_data = json.dumps(data, ensure_ascii=False)
    
    units_options = "".join([f'<option value="{i}">Unidad {i:02d}</option>' for i in range(1, 21)])

    template = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Buscador Rápido de Inglés • UTM Aulas Lenguas</title>
    <!-- Supabase JS Client -->
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <!-- Tesseract.js OCR en WebAssembly 100% en el navegador -->
    <script src="https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            min-height: 100vh;
            padding: 20px;
        }
        /* Auth Screen */
        .auth-container {
            min-height: 85vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .auth-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 32px 28px;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 20px 45px rgba(0,0,0,0.6);
        }
        .auth-card h2 {
            font-size: 22px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 6px;
            text-align: center;
        }
        .auth-card p {
            font-size: 14px;
            color: #94a3b8;
            text-align: center;
            margin-bottom: 22px;
            line-height: 1.4;
        }
        .form-group {
            margin-bottom: 18px;
        }
        .form-group label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: #cbd5e1;
            margin-bottom: 6px;
        }
        .form-group input {
            width: 100%;
            background: #0f172a;
            border: 1px solid #475569;
            border-radius: 10px;
            padding: 12px 14px;
            color: #f8fafc;
            font-size: 15px;
            outline: none;
            transition: border-color 0.2s;
        }
        .form-group input:focus {
            border-color: #3b82f6;
        }
        .btn-submit {
            width: 100%;
            background: #2563eb;
            color: #ffffff;
            border: none;
            border-radius: 10px;
            padding: 13px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn-submit:hover {
            background: #1d4ed8;
        }
        .auth-error {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.4);
            color: #fca5a5;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 13px;
            margin-bottom: 18px;
            display: none;
        }
        .auth-hint {
            margin-top: 20px;
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.25);
            border-radius: 10px;
            padding: 12px;
            font-size: 12px;
            color: #93c5fd;
            text-align: center;
            cursor: pointer;
            transition: background 0.2s;
        }
        .auth-hint:hover {
            background: rgba(59, 130, 246, 0.18);
        }
        .top-nav {
            max-width: 900px;
            margin: 0 auto 16px auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 16px;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
        }
        .user-badge {
            font-size: 13px;
            color: #94a3b8;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .user-badge strong {
            color: #38bdf8;
        }
        .btn-logout {
            background: #334155;
            border: 1px solid #475569;
            color: #f8fafc;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-logout:hover {
            background: #ef4444;
            border-color: #dc2626;
        }
        .header {
            max-width: 900px;
            margin: 0 auto 16px auto;
            text-align: center;
        }
        .header h1 {
            font-size: 26px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 6px;
        }
        .header p {
            color: #94a3b8;
            font-size: 14px;
        }
        .ocr-hint {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 8px;
            background: rgba(59, 130, 246, 0.12);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #93c5fd;
            padding: 5px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
        }
        .search-container {
            max-width: 900px;
            margin: 0 auto 16px auto;
            position: sticky;
            top: 10px;
            z-index: 100;
        }
        .search-box {
            display: flex;
            background: #1e293b;
            border: 2px solid #3b82f6;
            border-radius: 14px;
            padding: 6px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            gap: 8px;
            align-items: center;
        }
        .search-box input {
            flex: 1;
            background: transparent;
            border: none;
            padding: 12px 16px;
            font-size: 16px;
            color: #ffffff;
            outline: none;
        }
        .search-box input::placeholder {
            color: #64748b;
        }
        .btn-ocr {
            background: #334155;
            color: #f8fafc;
            border: 1px solid #475569;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .btn-ocr:hover {
            background: #2563eb;
            border-color: #3b82f6;
        }
        .filter-select {
            background: #334155;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 14px;
            outline: none;
            cursor: pointer;
        }
        .ocr-banner {
            max-width: 900px;
            margin: 0 auto 16px auto;
            background: #1e1b4b;
            border: 1px solid #6366f1;
            border-radius: 12px;
            padding: 12px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: #c7d2fe;
            font-size: 14px;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.2);
        }
        .ocr-spinner {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid #818cf8;
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 8px;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .stats-bar {
            max-width: 900px;
            margin: 0 auto 16px auto;
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #94a3b8;
            padding: 0 4px;
        }
        .results-container {
            max-width: 900px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        .card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: transform 0.15s, border-color 0.15s;
        }
        .card:hover {
            border-color: #60a5fa;
            transform: translateY(-2px);
        }
        .card-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            font-size: 12px;
        }
        .badges {
            display: flex;
            gap: 6px;
        }
        .badge-unit {
            background: #2563eb;
            color: #ffffff;
            padding: 2px 8px;
            border-radius: 6px;
            font-weight: 700;
        }
        .badge-skill {
            background: #334155;
            color: #cbd5e1;
            padding: 2px 8px;
            border-radius: 6px;
            text-transform: capitalize;
        }
        .card-topic {
            color: #64748b;
            font-weight: 500;
        }
        .card-question {
            font-size: 16px;
            font-weight: 600;
            color: #f1f5f9;
            margin-bottom: 8px;
            line-height: 1.4;
        }
        .card-desc {
            font-size: 13px;
            color: #94a3b8;
            font-style: italic;
            margin-bottom: 12px;
            background: #0f172a;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid #64748b;
        }
        .card-expl {
            font-size: 13px;
            color: #38bdf8;
            background: rgba(56, 189, 248, 0.08);
            border: 1px solid rgba(56, 189, 248, 0.2);
            padding: 10px 14px;
            border-radius: 8px;
            margin-bottom: 12px;
            line-height: 1.4;
        }
        .answer-box {
            background: #064e3b;
            border: 1px solid #059669;
            border-radius: 8px;
            padding: 12px 16px;
            color: #a7f3d0;
        }
        .answer-title {
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #34d399;
            margin-bottom: 6px;
        }
        .answer-text {
            font-size: 15px;
            font-weight: 700;
            color: #ffffff;
            line-height: 1.5;
        }
        .answer-item {
            margin-bottom: 4px;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #64748b;
        }
        .empty-state h3 {
            color: #cbd5e1;
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <!-- SECCIÓN DE LOGIN (SUPABASE AUTH) -->
    <div id="authSection" class="auth-container">
        <div class="auth-card">
            <div style="text-align:center; font-size:40px; margin-bottom:12px;">🔐</div>
            <h2>Acceso al Buscador</h2>
            <p>Ingresá con tu cuenta para acceder a la base de datos de preguntas y OCR</p>

            <div id="loginError" class="auth-error"></div>

            <form id="loginForm" onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label for="loginEmail">Correo Electrónico</label>
                    <input type="email" id="loginEmail" placeholder="estudiante@utm.edu.ec" required autofocus>
                </div>
                <div class="form-group">
                    <label for="loginPassword">Contraseña</label>
                    <input type="password" id="loginPassword" placeholder="••••••••" required>
                </div>
                <button type="submit" id="loginBtn" class="btn-submit">Ingresar al Buscador</button>
            </form>
        </div>
    </div>

    <!-- SECCIÓN PRINCIPAL DEL BUSCADOR (PROTEGIDA) -->
    <div id="appSection" style="display:none;">
        <div class="top-nav">
            <div class="user-badge">
                <span>👤 Conectado: <strong id="userEmailDisplay">...</strong></span>
            </div>
            <div style="display:flex; gap:8px;">
                <a href="portal.html" class="btn-logout" style="text-decoration:none; background:#1e3a8a; border-color:#3b82f6; display:flex; align-items:center; gap:4px;" title="Ver guías y recursos de estudio">📚 Guías</a>
                <button onclick="handleLogout()" class="btn-logout" title="Cerrar Sesión">Cerrar Sesión</button>
            </div>
        </div>

        <div class="header">
            <h1>🔍 Buscador Rápido • Simulador UTM</h1>
            <p>Escribí palabras clave o <strong>pegá una captura de pantalla (Ctrl+V)</strong></p>
            <div class="ocr-hint">
                <span>📋 Podés apretar <strong>Ctrl + V</strong> para pegar una captura en cualquier momento</span>
            </div>
        </div>

        <div id="ocrBanner" class="ocr-banner" style="display:none;">
            <div>
                <span id="ocrSpinner" class="ocr-spinner"></span>
                <span id="ocrStatusText">Leyendo texto de la captura de pantalla...</span>
            </div>
        </div>

        <div class="search-container">
            <div class="search-box">
                <input type="text" id="queryInput" placeholder="Escribí o pegá (Ctrl+V) una captura..." oninput="search()">
                <input type="file" id="imageFileInput" accept="image/*" style="display:none" onchange="if(this.files[0]) processImageFile(this.files[0])">
                <button class="btn-ocr" onclick="document.getElementById('imageFileInput').click()" title="Subir imagen">
                    📷 Subir captura
                </button>
                <select id="unitFilter" class="filter-select" onchange="search()">
                    <option value="0">Todas las Unidades (1-20)</option>
                    {{UNITS_OPTIONS}}
                </select>
            </div>
        </div>

        <div class="stats-bar">
            <span id="resultsCount">Mostrando 20 preguntas iniciales</span>
            <span>Base de datos: 3.367 preguntas</span>
        </div>

        <div class="results-container" id="resultsContainer"></div>
    </div>

    <script>
        const DB = {{JSON_DATA}};

        function renderCard(item) {
            let answersHtml = item.ans.map(a => `<div class="answer-item">✅ ${escapeHtml(a)}</div>`).join('');
            if (!answersHtml) {
                answersHtml = '<div class="answer-item">Ver opciones en guía detallada</div>';
            }

            let descHtml = item.desc ? `<div class="card-desc">ℹ️ ${escapeHtml(item.desc)}</div>` : '';
            let explHtml = item.exp ? `<div class="card-expl">💡 <strong>Regla / Explicación:</strong> ${escapeHtml(item.exp)}</div>` : '';

            return `
            <div class="card">
                <div class="card-top">
                    <div class="badges">
                        <span class="badge-unit">${escapeHtml(item.tag || ('Unidad ' + item.u))}</span>
                    </div>
                    <span class="card-topic">${escapeHtml(item.top || '')}</span>
                </div>
                <div class="card-question">${escapeHtml(item.q)}</div>
                ${descHtml}
                ${explHtml}
                <div class="answer-box">
                    <div class="answer-title">Respuesta Verificada</div>
                    <div class="answer-text">${answersHtml}</div>
                </div>
            </div>`;
        }

        function escapeHtml(str) {
            if (!str) return '';
            return String(str)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        const STOP_WORDS = new Set([
            'the', 'and', 'to', 'is', 'in', 'of', 'it', 'for', 'are', 'at', 'or', 'you', 'with', 'this', 'that', 'from',
            'a', 'an', 'as', 'by', 'on', 'be', 'has', 'have', 'had', 'was', 'were', 'not', 'but',
            'choose', 'correct', 'option', 'sentence', 'sentences', 'read', 'following', 'complete', 'statements', 
            'statement', 'true', 'false', 'match', 'answer', 'best', 'right', 'what', 'which',
            'pregunta', 'puntaje', 'puntua', 'puntúa', 'sin', 'responder', 'aun', 'aún', 'marcar', 'bandera', 'seleccione', 'una', 'como'
        ]);

        function search() {
            const rawQ = document.getElementById('queryInput').value.trim().toLowerCase();
            const unit = parseInt(document.getElementById('unitFilter').value, 10);
            const container = document.getElementById('resultsContainer');
            const countElem = document.getElementById('resultsCount');

            if (!rawQ) {
                let initial = DB.filter(item => unit === 0 || item.u === unit).slice(0, 25);
                countElem.innerText = `Mostrando ${initial.length} preguntas ${unit !== 0 ? '(Unidad ' + unit + ')' : ''}`;
                container.innerHTML = initial.map(renderCard).join('');
                return;
            }

            let words = rawQ.replace(/[^a-zA-Z0-9\\s'’]/g, ' ').split(/\\s+/).filter(w => w.length >= 2);
            let matches = [];

            let ngrams = [];
            for (let i = 0; i < words.length - 1; i++) {
                ngrams.push(words[i] + ' ' + words[i+1]);
                if (i < words.length - 2) {
                    ngrams.push(words[i] + ' ' + words[i+1] + ' ' + words[i+2]);
                }
            }

            for (let item of DB) {
                if (unit !== 0 && item.u !== unit) continue;

                let score = 0;
                let qLower = (item.q || '').toLowerCase();
                let descLower = (item.desc || '').toLowerCase();
                let kLower = item.k;

                if (rawQ.length > 5) {
                    if (qLower.includes(rawQ)) score += 150;
                    else if (descLower.includes(rawQ)) score += 100;
                    else if (kLower.includes(rawQ)) score += 80;
                }

                for (let ng of ngrams) {
                    if (qLower.includes(ng)) score += 25;
                    else if (kLower.includes(ng)) score += 12;
                }

                let matchedContentWords = 0;
                for (let w of words) {
                    let isStop = STOP_WORDS.has(w);
                    let weight = isStop ? 0.3 : (w.length >= 5 ? 4 : 2);

                    let hit = false;
                    if (qLower.includes(w)) {
                        score += weight * 3;
                        hit = true;
                    }
                    if (descLower.includes(w)) {
                        score += weight * 2;
                        hit = true;
                    }
                    if (item.ans && item.ans.some(a => a.toLowerCase().includes(w))) {
                        score += weight * 2.5;
                        hit = true;
                    }
                    if (!hit && kLower.includes(w)) {
                        score += weight;
                        hit = true;
                    }
                    if (hit && !isStop) matchedContentWords++;
                }

                if (score > 1.5 && (matchedContentWords > 0 || score >= 25)) {
                    matches.push({ item, score });
                }
            }

            matches.sort((a, b) => b.score - a.score);

            const finalResults = matches.slice(0, 40).map(m => m.item);
            countElem.innerText = `Encontradas: ${matches.length} preguntas ${unit !== 0 ? '(Unidad ' + unit + ')' : ''}`;

            if (finalResults.length === 0) {
                container.innerHTML = `
                <div class="empty-state">
                    <h3>No se encontraron preguntas coincidentes</h3>
                    <p>Intentá recortar la captura solo a la pregunta o borrá palabras del buscador.</p>
                </div>`;
            } else {
                container.innerHTML = finalResults.map(renderCard).join('');
            }
        }

        // ==========================================
        // OCR Y SOPORTE DE CAPTURAS DE PANTALLA
        // ==========================================

        window.addEventListener('paste', async (e) => {
            const items = (e.clipboardData || window.clipboardData).items;
            for (let item of items) {
                if (item.type.indexOf('image') !== -1) {
                    const blob = item.getAsFile();
                    processImageFile(blob);
                    e.preventDefault();
                    break;
                }
            }
        });

        window.addEventListener('dragover', (e) => e.preventDefault());
        window.addEventListener('drop', (e) => {
            e.preventDefault();
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                const file = e.dataTransfer.files[0];
                if (file.type.startsWith('image/')) {
                    processImageFile(file);
                }
            }
        });

        async function processImageFile(file) {
            const banner = document.getElementById('ocrBanner');
            const statusText = document.getElementById('ocrStatusText');
            const spinner = document.getElementById('ocrSpinner');
            const input = document.getElementById('queryInput');

            banner.style.display = 'flex';
            spinner.style.display = 'inline-block';
            statusText.innerText = '⏳ Cargando motor OCR en WebAssembly...';

            try {
                const worker = await Tesseract.createWorker('eng');
                statusText.innerText = '🔍 Leyendo texto de la captura de pantalla...';

                const ret = await worker.recognize(file);
                await worker.terminate();

                const rawText = ret.data.text.trim();
                if (!rawText) {
                    statusText.innerText = '⚠️ No se detectó texto legible en la imagen.';
                    spinner.style.display = 'none';
                    setTimeout(() => { banner.style.display = 'none'; }, 3000);
                    return;
                }

                // Filtrar ruido de interfaz típica de UTM / Moodle
                const rawLines = rawText.split(/\\r?\\n/).map(l => l.trim()).filter(Boolean);
                const noiseRegex = /^(pregunta|punt|sin responder|marcar|seleccione|tiempo|naveg|simulador|utm|aulas)/i;
                
                let candidateLines = [];
                for (let line of rawLines) {
                    let cleaned = line.replace(/[^a-zA-Z0-9\\s'’]/g, ' ').replace(/\\s+/g, ' ').trim();
                    if (cleaned.length < 4) continue;
                    if (noiseRegex.test(cleaned)) continue;
                    candidateLines.push(cleaned);
                }

                let extractedQuery = candidateLines.join(' ');
                if (!extractedQuery) {
                    extractedQuery = rawText.replace(/[^a-zA-Z0-9\\s'’]/g, ' ').replace(/\\s+/g, ' ').trim();
                }

                // Si la captura incluye "UNIT X", auto-seleccionar la unidad en el filtro
                const unitMatch = rawText.match(/\\bunit\\s*(\\d+)\\b/i);
                if (unitMatch && unitMatch[1]) {
                    const uVal = parseInt(unitMatch[1], 10);
                    if (uVal >= 1 && uVal <= 20) {
                        document.getElementById('unitFilter').value = uVal;
                    }
                }

                input.value = extractedQuery.slice(0, 120);
                spinner.style.display = 'none';
                statusText.innerHTML = `✅ Texto reconocido: <strong>"${escapeHtml(input.value)}"</strong>`;
                
                search();

                setTimeout(() => { banner.style.display = 'none'; }, 4000);
            } catch (err) {
                console.error(err);
                spinner.style.display = 'none';
                statusText.innerText = '❌ Error al procesar imagen: ' + err.message;
                setTimeout(() => { banner.style.display = 'none'; }, 4000);
            }
        }

        // ==========================================
        // AUTENTICACIÓN CON SUPABASE
        // ==========================================
        const SUPABASE_URL = "https://pytzthgogluigkzbpmaj.supabase.co";
        const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB5dHp0aGdvZ2x1aWdremJwbWFqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ2NTk5NzQsImV4cCI6MjEwMDIzNTk3NH0.1F1CpXhrxKUfRnnurdPLipewSFUJPP-6wCuxvxJd7OU";

        let supabaseClient = null;
        if (window.supabase) {
            supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        }

        async function initAuth() {
            if (!supabaseClient) {
                showApp({ email: 'Modo Offline / Local' });
                return;
            }

            try {
                const { data: { session } } = await supabaseClient.auth.getSession();
                if (session && session.user) {
                    showApp(session.user);
                } else {
                    showLogin();
                }
            } catch (e) {
                console.warn('Error verificando sesión previa:', e);
                showLogin();
            }
        }

        function showLogin() {
            document.getElementById('authSection').style.display = 'flex';
            document.getElementById('appSection').style.display = 'none';
        }

        function showApp(user) {
            document.getElementById('authSection').style.display = 'none';
            document.getElementById('appSection').style.display = 'block';
            document.getElementById('userEmailDisplay').innerText = user.email || 'Estudiante';
            search();
        }

        async function handleLogin(e) {
            e.preventDefault();
            const email = document.getElementById('loginEmail').value.trim();
            const password = document.getElementById('loginPassword').value;
            const btn = document.getElementById('loginBtn');
            const errAlert = document.getElementById('loginError');

            errAlert.style.display = 'none';
            btn.disabled = true;
            btn.innerText = 'Verificando con Supabase...';

            try {
                if (!supabaseClient) {
                    throw new Error('No se pudo inicializar la conexión con Supabase.');
                }

                const { data, error } = await supabaseClient.auth.signInWithPassword({
                    email,
                    password
                });

                if (error) throw error;
                showApp(data.user);
            } catch (err) {
                errAlert.innerText = '❌ Error de acceso: ' + (err.message || 'Credenciales inválidas');
                errAlert.style.display = 'block';
            } finally {
                btn.disabled = false;
                btn.innerText = 'Ingresar al Buscador';
            }
        }

        async function handleLogout() {
            if (supabaseClient) {
                try {
                    await supabaseClient.auth.signOut();
                } catch (e) {
                    console.error(e);
                }
            }
            showLogin();
        }

        function fillDemoCredentials() {
            document.getElementById('loginEmail').value = 'estudiante@utm.edu.ec';
            document.getElementById('loginPassword').value = 'UTMingles2026!';
        }

        // Iniciar flujo de verificación de sesión
        initAuth();
    </script>
</body>
</html>"""

    html = template.replace("{{UNITS_OPTIONS}}", units_options).replace("{{JSON_DATA}}", json_data)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    with open(OUTPUT_BUSCADOR, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Buscador con login y OCR generado en: {OUTPUT_HTML} y {OUTPUT_BUSCADOR}")

if __name__ == "__main__":
    print("Compilando índice de búsqueda de 3.367 preguntas...")
    data = build_search_data()
    print(f"Índice listo con {len(data)} elementos. Generando buscador.html...")
    generate_html_search_app(data)
