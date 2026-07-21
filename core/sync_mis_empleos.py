#!/usr/bin/env python3
import browser_cookie3
import requests
import sqlite3
import re
import os
from bs4 import BeautifulSoup
import time

CARPETA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(CARPETA_BASE, "perfil", "jobs_vistos.db")

def get_cookies():
    # Intenta sacar cookies de los navegadores más comunes en Linux
    try:
        print("Intentando extraer cookies de Chrome...")
        return browser_cookie3.chrome(domain_name='getonbrd.com')
    except Exception:
        try:
            print("Intentando extraer cookies de Firefox...")
            return browser_cookie3.firefox(domain_name='getonbrd.com')
        except Exception:
            try:
                print("Intentando extraer cookies de Brave...")
                return browser_cookie3.brave(domain_name='getonbrd.com')
            except Exception as e:
                print(f"No se pudieron extraer cookies: {e}")
                return None

def sync_jobs():
    cj = get_cookies()
    if not cj:
        print("No se encontraron cookies para GetOnBoard. Aborta la misión.")
        return

    url = "https://www.getonbrd.com/misempleos"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }

    print(f"Conectando a {url} con tu sesión...")
    res = requests.get(url, cookies=cj, headers=headers)
    
    if res.status_code != 200:
        print(f"Error HTTP {res.status_code}. ¿Seguro que estás logueado en este navegador?")
        return
        
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Extraer todos los links que vayan a /empleos/...
    job_ids = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        match = re.search(r'/empleos/([^/]+)', href)
        if match:
            # Eliminar posibles queries "?..."
            job_id = match.group(1).split('?')[0]
            job_ids.add(job_id)

    if not job_ids:
        print("No se encontraron links de empleos en la página (o la sesión expiró).")
        return

    print(f"Se extrajeron {len(job_ids)} IDs únicos de tu historial de GetOnBoard.")

    # Conectar a la DB e inyectar
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Asegurar que la tabla existe (por si el bot principal no ha corrido)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            url TEXT,
            seen_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    nuevos_ignorados = 0
    for jid in job_ids:
        try:
            cursor.execute('''
                INSERT INTO jobs (job_id, title, company, url) 
                VALUES (?, ?, ?, ?)
            ''', (jid, 'Ya Postulado (Sincronizado)', 'Desconocida', f"https://www.getonbrd.com/empleos/{jid}"))
            nuevos_ignorados += 1
        except sqlite3.IntegrityError:
            # Ya existía en la DB
            pass

    conn.commit()
    conn.close()
    
    print(f"¡Sincronización completa! Se agregaron {nuevos_ignorados} empleos al historial de ignorados.")

if __name__ == "__main__":
    sync_jobs()
