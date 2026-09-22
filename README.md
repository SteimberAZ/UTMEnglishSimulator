# UTM English Simulator Suite 🎓📚

Suite completa de estudio, guías pedagógicas y motor de búsqueda inteligente con OCR para el **Simulador de Suficiencia en Inglés** de la Universidad Técnica de Manabí (UTM).

---

## 🚀 Características Principales

1. **Buscador Inteligente con Autenticación ([buscador.html](buscador.html))**:
   - Acceso protegido mediante **Supabase Auth**.
   - **OCR en WebAssembly (Tesseract.js)**: Permite pegar capturas de pantalla con `Ctrl + V` directamente desde el portapapeles.
   - **Algoritmo TF-IDF y detección de frases (n-grams)**: Reconoce encabezados de tareas (ej. `WRITING BOOK 1 MOD 1 UNIT 1`) y auto-detecta la unidad del examen.
   - Base de datos local integrada con **3.367 preguntas oficiales** y sus respuestas verificadas con explicaciones gramaticales.

2. **Guías de Estudio por Unidad (1 a 20)**:
   - Formato HTML imprimible a PDF (`guias_html/Unidad_01.html` a `guias_html/Unidad_20.html`).
   - Formato Markdown compatible con Obsidian (`guias_md/Unidad_01.md` a `guias_md/Unidad_20.md`).
   - Portal unificado interactivo (`index.html`).

3. **Gestor de Accesos ([create_user.py](create_user.py))**:
   - Script CLI para dar de alta usuarios autorizados de forma instantánea tanto en **Supabase Auth** (`auth.users`) como en la tabla `public.Users`.

---

## 🛠️ Requisitos e Instalación

### Requisitos:
- Navegador web moderno (Chrome, Edge, Firefox).
- Python 3.10+ (para scripts de indexación y administración).
- Dependencias mínimas de Python:
  ```bash
  pip install requests
  ```

### Configuración de Supabase:
Crea un archivo `.env` basado en `.env.example`:
```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-service-role-key
SUPABASE_ANON_KEY=tu-anon-key
```

---

## 👥 Gestión de Usuarios

Para crear un nuevo usuario con acceso inmediato:
```bash
python create_user.py "usuario@utm.edu.ec" "ContraseñaSegura123!" "Nombre Estudiante"
```

---

## 📖 Compilación y Generación

- **Compilar el Buscador:**
  ```bash
  python build_search_app.py
  ```
- **Generar todas las guías de estudio:**
  ```bash
  python generate_all_units.py
  ```
