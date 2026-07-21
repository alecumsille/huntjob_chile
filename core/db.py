"""
Módulo de almacenamiento de base de datos SQLite para memoria de perfiles,
historial de postulaciones y registros de usuario.
"""

import sqlite3
import os
import json
from datetime import datetime

RUTA_DB = "perfil/huntjob_memoria.db"


def _obtener_conexion():
    os.makedirs("perfil", exist_ok=True)
    conn = sqlite3.connect(RUTA_DB)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_db():
    """Crea las tablas necesarias si no existen."""
    with _obtener_conexion() as conn:
        cursor = conn.cursor()
        
        # Tabla de perfil persistente de usuario
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS perfil_usuario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                email TEXT,
                telefono TEXT,
                linkedin TEXT,
                anos_experiencia INTEGER DEFAULT 0,
                seniority TEXT,
                stack_principal TEXT,
                logros_y_experiencia TEXT,
                actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de historial de postulaciones generadas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_postulaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                puesto TEXT,
                empresa TEXT,
                mercado TEXT,
                url_oferta TEXT,
                cv_texto TEXT,
                cover_letter_texto TEXT,
                estilo_pdf TEXT,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()


def guardar_historial(puesto: str, empresa: str, mercado: str, url_oferta: str, cv_texto: str, cover_letter_texto: str, estilo_pdf: str):
    """Guarda un registro en la memoria de postulaciones."""
    inicializar_db()
    with _obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO historial_postulaciones 
            (puesto, empresa, mercado, url_oferta, cv_texto, cover_letter_texto, estilo_pdf)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (puesto, empresa, mercado, url_oferta, cv_texto, cover_letter_texto, estilo_pdf))
        conn.commit()


def obtener_historial_reciente(limite: int = 10) -> list[dict]:
    """Obtiene los últimos documentos generados."""
    inicializar_db()
    with _obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT puesto, empresa, mercado, url_oferta, creado_en 
            FROM historial_postulaciones 
            ORDER BY id DESC LIMIT ?
        """, (limite,))
        filas = cursor.fetchall()
        return [dict(f) for f in filas]
