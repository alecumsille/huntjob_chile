"""
Mapeador de Demanda Laboral e Industrias por Región en Chile.
Inspirado en datachile/datachile y cortega26/chile-hub.

Proporciona información sobre la industria predominante y el nivel de demanda
laboral en las 16 regiones del territorio nacional.
"""

MERCADO_REGIONAL_CHILE = {
    "arica_y_parinacota": {"nombre": "Arica y Parinacota", "industria_clave": "Comercio Transfronterizo, Logística, Agricultura de Azapa, Servicios", "demanda": "Media"},
    "tarapaca": {"nombre": "Tarapacá (Iquique)", "industria_clave": "Minería (Cobre), ZOFRI Comercio, Puerto y Logística", "demanda": "Alta"},
    "antofagasta": {"nombre": "Antofagasta", "industria_clave": "Gran Minería del Cobre, Energía Solar, Servicios Industriales", "demanda": "Muy Alta"},
    "atacama": {"nombre": "Atacama", "industria_clave": "Minería, Agricultura de Exportación, Energías Renovables", "demanda": "Media-Alta"},
    "coquimbo": {"nombre": "Coquimbo (La Serena)", "industria_clave": "Turismo, Vitivinicultura, Minería y Pesca", "demanda": "Media"},
    "valparaiso": {"nombre": "Valparaíso / Viña del Mar", "industria_clave": "Puertos, Educación Superior, Turismo, Tecnología y Servicios", "demanda": "Alta"},
    "metropolitana": {"nombre": "Región Metropolitana (Santiago)", "industria_clave": "Servicios Financieros, Tecnología / IT, Retail, Casa Matriz Corporativa", "demanda": "Muy Alta"},
    "ohiggins": {"nombre": "O'Higgins (Rancagua)", "industria_clave": "Agroindustria, Minería (El Teniente), Fruticultura", "demanda": "Media-Alta"},
    "maule": {"nombre": "Maule (Talca)", "industria_clave": "Agroindustria, Vitivinicultura, Industria Forestal", "demanda": "Media"},
    "nuble": {"nombre": "Ñuble (Chillán)", "industria_clave": "Agroindustria, Maderera y Servicios", "demanda": "Media"},
    "biobio": {"nombre": "Biobío (Concepción)", "industria_clave": "Siderurgia, Industria Forestal / Celulosa, Educación, Puertos", "demanda": "Alta"},
    "araucania": {"nombre": "La Araucanía (Temuco)", "industria_clave": "Agropecuaria, Turismo, Universidad y Comercio", "demanda": "Media"},
    "los_rios": {"nombre": "Los Ríos (Valdivia)", "industria_clave": "Cervecería, Investigación / Biotecnología, Turismo, Maderera", "demanda": "Media"},
    "los_lagos": {"nombre": "Los Lagos (Puerto Montt / Chiloé)", "industria_clave": "Acuicultura (Salmón), Mitilicultura, Turismo, Agropecuaria", "demanda": "Alta"},
    "aysen": {"nombre": "Aysén", "industria_clave": "Pesca y Acuicultura, Ganadería, Turismo de Naturaleza", "demanda": "Media"},
    "magallanes": {"nombre": "Magallanes (Punta Arenas)", "industria_clave": "Hidrógeno Verde, Minería / Petróleo, Turismo Antártico, Ganadería", "demanda": "Alta"}
}


def consultar_demanda_regional(region_str: str) -> dict:
    """Devuelve las industrias clave y el nivel de demanda para una región dada."""
    if not region_str:
        return MERCADO_REGIONAL_CHILE["metropolitana"]

    slug = region_str.lower().strip().replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")

    for key, data in MERCADO_REGIONAL_CHILE.items():
        if key in slug or slug in key:
            return data

    return MERCADO_REGIONAL_CHILE["metropolitana"]
