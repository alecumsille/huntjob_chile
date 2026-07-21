#!/usr/bin/env python3
import requests
import sqlite3
import os
from datetime import datetime

# Configuración portable
CARPETA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(CARPETA_BASE, "perfil", "jobs_vistos.db")
OUTPUT_FILE = os.path.join(CARPETA_BASE, "ofertas_nuevas.md")
QUERIES = ["python", "data engineer", "backend", "automation"]

def setup_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            url TEXT,
            seen_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def fetch_getonboard_jobs(query):
    print(f"Buscando '{query}' en GetOnBoard...")
    url = f"https://www.getonbrd.com/api/v0/search/jobs?query={query}&per_page=10"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        return data.get('data', [])
    except Exception as e:
        print(f"Error fetching GetOnBoard: {e}")
        return []

def main():
    conn = setup_db()
    cursor = conn.cursor()
    
    new_jobs_found = []
    
    for q in QUERIES:
        jobs = fetch_getonboard_jobs(q)
        for j in jobs:
            attrs = j.get('attributes', {})
            job_id = j.get('id')
            title = attrs.get('title')
            # Extract company name from the nested structure
            try:
                company = j['attributes']['company']['data']['attributes']['name']
            except (KeyError, TypeError):
                company = 'Empresa Oculta/Desconocida'
            
            # Verificamos si ya existe en la DB
            cursor.execute("SELECT job_id FROM jobs WHERE job_id = ?", (job_id,))
            if not cursor.fetchone():
                # Enlace de GetOnBoard
                url = attrs.get('url', f"https://www.getonbrd.com/empleos/{job_id}")
                
                # Insertamos
                cursor.execute("INSERT INTO jobs (job_id, title, company, url) VALUES (?, ?, ?, ?)", 
                              (job_id, title, company, url))
                
                new_jobs_found.append({
                    "title": title,
                    "company": company,
                    "url": url,
                    "query": q
                })
    
    conn.commit()
    conn.close()
    
    if new_jobs_found:
        print(f"¡Se encontraron {len(new_jobs_found)} ofertas nuevas!")
        with open(OUTPUT_FILE, 'a') as f:
            f.write(f"\n## Nuevas Ofertas - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            for job in new_jobs_found:
                f.write(f"- **{job['title']}** en {job['company']} (Filtro: {job['query']})\n")
                f.write(f"  [Ver Oferta]({job['url']})\n\n")
    else:
        print("No se encontraron ofertas nuevas en esta iteración.")

if __name__ == "__main__":
    main()
