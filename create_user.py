import os
import sys
import requests

def _load_env():
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

_load_env()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://pytzthgogluigkzbpmaj.supabase.co")
SERVICE_KEY = os.environ.get("SUPABASE_KEY", "")

def create_or_update_user(email, password, name="Estudiante UTM"):
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json"
    }

    # 1. Crear en Supabase Auth (auth.users)
    auth_url = f"{SUPABASE_URL}/auth/v1/admin/users"
    auth_payload = {
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {"name": name}
    }
    r1 = requests.post(auth_url, headers=headers, json=auth_payload)
    if r1.status_code in (200, 201):
        print(f"[OK] Usuario creado en Supabase Auth: {email}")
    else:
        print(f"[INFO] Supabase Auth status: {r1.status_code} ({r1.text})")

    # 2. Sincronizar en tabla pública Users (public.Users)
    db_url = f"{SUPABASE_URL}/rest/v1/Users"
    db_payload = {
        "name": name,
        "email": email,
        "password": password
    }
    headers["Prefer"] = "resolution=merge-duplicates"
    r2 = requests.post(db_url, headers=headers, json=db_payload)
    if r2.status_code in (200, 201):
        print(f"[OK] Usuario sincronizado en tabla public.Users: {email}")
    else:
        print(f"[INFO] public.Users status: {r2.status_code} ({r2.text})")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else "Estudiante UTM"
        create_or_update_user(email, password, name)
    else:
        print("Uso: python create_user.py <correo> <contraseña> [nombre]")
        print("Ejemplo: python create_user.py amigo@utm.edu.ec MiClave123! 'Carlos'")
