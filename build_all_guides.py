import os
import json
import time
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

def fetch_and_cache_data():
    session = get_session()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    q_file = os.path.join(base_dir, "questions_all.json")
    t_file = os.path.join(base_dir, "tasks_all.json")

    # 1. Descargar preguntas de los 5 libros
    if os.path.exists(q_file):
        print(f"[CACHE] Cargando preguntas desde {q_file}...")
        with open(q_file, "r", encoding="utf-8") as f:
            all_questions = json.load(f)
    else:
        print("[HTTP] Descargando preguntas de los 5 libros (Books 1 a 5)...")
        all_questions = []
        for b in range(1, 6):
            r = session.get(f"{API_BASE}/simulador/book/books/{b}")
            if r.status_code == 200:
                qs = r.json()
                print(f"  -> Book {b}: {len(qs)} preguntas")
                all_questions.extend(qs)
            else:
                print(f"  [!] Error en Book {b}: {r.status_code}")
            time.sleep(0.2)

        with open(q_file, "w", encoding="utf-8") as f:
            json.dump(all_questions, f, ensure_ascii=False)
        print(f"[OK] Total preguntas guardadas en {q_file}: {len(all_questions)}")

    # 2. Obtener lista de todos los task_id únicos
    unique_task_ids = sorted(list(set(q.get("task_id") for q in all_questions if q.get("task_id"))))
    print(f"\n[INFO] Total tareas únicas a mapear: {len(unique_task_ids)}")

    # 3. Descargar info de cada tarea
    if os.path.exists(t_file):
        print(f"[CACHE] Cargando tareas desde {t_file}...")
        with open(t_file, "r", encoding="utf-8") as f:
            tasks_info = json.load(f)
    else:
        tasks_info = {}

    missing_ids = [tid for tid in unique_task_ids if str(tid) not in tasks_info]
    if missing_ids:
        print(f"[HTTP] Descargando información de {len(missing_ids)} tareas pendientes...")
        for i, tid in enumerate(missing_ids, 1):
            r = session.get(f"{API_BASE}/simulador/task/info/{tid}")
            if r.status_code == 200:
                tasks_info[str(tid)] = r.json()
            elif r.status_code == 429:
                print(f"  [!] Rate limit en tarea {tid}, pausando 2 segundos...")
                time.sleep(2)
                r = session.get(f"{API_BASE}/simulador/task/info/{tid}")
                if r.status_code == 200:
                    tasks_info[str(tid)] = r.json()
            else:
                print(f"  [!] Error en tarea {tid}: {r.status_code}")

            if i % 25 == 0 or i == len(missing_ids):
                print(f"  Progreso: {i}/{len(missing_ids)} tareas descargadas...")
            time.sleep(0.06)

        with open(t_file, "w", encoding="utf-8") as f:
            json.dump(tasks_info, f, ensure_ascii=False, indent=2)
        print(f"[OK] Tareas guardadas en {t_file}: {len(tasks_info)}")

    return all_questions, tasks_info

if __name__ == "__main__":
    fetch_and_cache_data()
