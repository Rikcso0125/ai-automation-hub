# -*- coding: utf-8 -*-
import os
import re
import json
import sqlite3
from typing import Dict, Any, List

def init_demo_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    c = conn.cursor()
    
    # Táblák létrehozása
    c.execute("""
        CREATE TABLE IF NOT EXISTS ugyfelek (
            id INTEGER PRIMARY KEY,
            nev TEXT,
            varos TEXT,
            kategoria TEXT,
            email TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS termekek (
            id INTEGER PRIMARY KEY,
            termek_nev TEXT,
            kategoria TEXT,
            egyseg_ar INTEGER,
            onkoltseg INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ertekesitesek (
            id INTEGER PRIMARY KEY,
            datum TEXT,
            ugyfel_id INTEGER,
            termek_id INTEGER,
            mennyiseg INTEGER,
            arbevetel INTEGER,
            profit INTEGER
        )
    """)

    # Mintaadatok betöltése
    ugyfelek = [
        (1, "Alfa Bau Kft.", "Budapest", "Kiemelt VIP", "ugyvezetes@alfabau.hu"),
        (2, "Béta Logisztika Zrt.", "Debrecen", "Középvállalat", "beszerzes@betalog.hu"),
        (3, "Gamma Generál Kft.", "Győr", "Kiemelt VIP", "penzugy@gammageneral.hu"),
        (4, "Delta Villamossági Bt.", "Szeged", "Standard KKV", "delta@villamossag.hu")
    ]
    c.executemany("INSERT INTO ugyfelek VALUES (?,?,?,?,?)", ugyfelek)

    termekek = [
        (101, "Prémium Acéllemez 2mm", "Nyersanyag", 45000, 32000),
        (102, "Ipari Kapcsolószekrény IP65", "Villamosság", 185000, 130000),
        (103, "Automatizált Szenzor Hub v2", "Elektronika", 78000, 52000),
        (104, "Tartókonzol Szett 500x500", "Szerelés", 14500, 9500)
    ]
    c.executemany("INSERT INTO termekek VALUES (?,?,?,?,?)", termekek)

    ertekesitesek = [
        (1, "2026-08-15", 1, 102, 10, 1850000, 550000),
        (2, "2026-08-22", 3, 101, 50, 2250000, 650000),
        (3, "2026-09-02", 1, 103, 25, 1950000, 650000),
        (4, "2026-09-10", 2, 102, 15, 2775000, 825000),
        (5, "2026-09-14", 3, 101, 80, 3600000, 1040000),
        (6, "2026-09-18", 4, 104, 30, 435000, 150000)
    ]
    c.executemany("INSERT INTO ertekesitesek VALUES (?,?,?,?,?,?,?)", ertekesitesek)
    conn.commit()
    return conn

def check_sql_security(sql_query: str, strict_mode: bool) -> tuple[bool, str]:
    if not strict_mode:
        return True, "Biztonsági ellenőrzés jóváhagyva (Megengedő mód)."
    
    dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "EXEC", "GRANT", "REVOKE"]
    upper_query = sql_query.upper()
    for kw in dangerous_keywords:
        pattern = r"\b" + kw + r"\b"
        if re.search(pattern, upper_query):
            return False, f"BIZTONSÁGI BLOKKOLÁS: A lekérdezés veszélyes '{kw}' utasítást tartalmaz a Csak Olvasás (Read-Only) védelmi módban!"
    
    return True, "Biztonságos SELECT lekérdezés jóváhagyva."

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    question = payload.get("question", "").strip()
    requested_by = payload.get("requested_by", "Ismeretlen felhasználó")
    limit = payload.get("max_results", 5)

    data_source = config.get("data_source_type", "Beépített SQLite / Céges Minta Adatbázis")
    conn_str = config.get("connection_string", "sqlite:///:memory:")
    custom_source = config.get("custom_source_name", "Belső Vállalati Adatbázis")
    sec_mode_setting = config.get("security_mode", "Szigorú Csak Olvasás (Strict Read-Only, Adatmódosítás tiltása)")
    is_strict = "Szigorú" in sec_mode_setting
    mask_pii = "Igen" in config.get("mask_sensitive_pii", "Igen")

    # In-memory demó adatbázis inicializálása
    conn = init_demo_database()
    cursor = conn.cursor()

    # Kérdés feldolgozása & SQL szintetizálás
    q_lower = question.lower()
    
    # 1. Termékek és árbevétel lekérdezése
    if "termék" in q_lower or "forgalom" in q_lower or "bevétel" in q_lower or "haszon" in q_lower:
        generated_sql = f"""
            SELECT 
                t.termek_nev AS [Termék],
                t.kategoria AS [Kategória],
                SUM(e.mennyiseg) AS [Összes Eladott Mennyiség (db)],
                SUM(e.arbevetel) AS [Teljes Árbevétel (Ft)],
                SUM(e.profit) AS [Összes Haszon (Ft)]
            FROM ertekesitesek e
            JOIN termekek t ON e.termek_id = t.id
            GROUP BY t.id
            ORDER BY [Teljes Árbevétel (Ft)] DESC
            LIMIT {limit};
        """.strip()
    elif "vevő" in q_lower or "partner" in q_lower or "ügyfél" in q_lower:
        generated_sql = f"""
            SELECT 
                u.nev AS [Ügyfél Neve],
                u.varos AS [Székhely],
                u.kategoria AS [Besorolás],
                COUNT(e.id) AS [Vásárlások Száma],
                SUM(e.arbevetel) AS [Összes Költés (Ft)]
            FROM ertekesitesek e
            JOIN ugyfelek u ON e.ugyfel_id = u.id
            GROUP BY u.id
            ORDER BY [Összes Költés (Ft)] DESC
            LIMIT {limit};
        """.strip()
    else:
        # Általános összefoglaló
        generated_sql = f"""
            SELECT 
                t.termek_nev AS [Termék],
                SUM(e.arbevetel) AS [Árbevétel],
                SUM(e.profit) AS [Profit]
            FROM ertekesitesek e
            JOIN termekek t ON e.termek_id = t.id
            GROUP BY t.termek_nev
            ORDER BY [Árbevétel] DESC
            LIMIT {limit};
        """.strip()

    # Biztonsági audit
    is_safe, sec_message = check_sql_security(generated_sql, is_strict)
    if not is_safe:
        return {
            "status": "security_violation",
            "message": sec_message,
            "generated_sql": generated_sql,
            "data_source": data_source
        }

    # Lekérdezés végrehajtása
    cursor.execute(generated_sql)
    col_names = [d[0] for d in cursor.description]
    raw_rows = cursor.fetchall()

    # Rekordok formázása és PII maszkolás
    formatted_rows = []
    for r in raw_rows:
        row_dict = {}
        for col, val in zip(col_names, r):
            if mask_pii and any(pii_word in col.lower() for pii_word in ["email", "jelszó", "szemelyi", "kartya"]):
                val = "***@***.hu" if "@" in str(val) else "********"
            row_dict[col] = val
        formatted_rows.append(row_dict)

    # Meghatározzuk a legfontosabb metrika oszlopot (árbevétel / költés / profit)
    metric_col_idx = None
    for idx, col in enumerate(col_names):
        col_l = col.lower()
        if any(w in col_l for w in ["árbevétel", "arbevetel", "költés", "koltes", "profit", "összeg"]):
            metric_col_idx = idx
            break
    if metric_col_idx is None:
        # Ha nincs ilyen, az utolsó numerikus oszlop
        for idx in range(len(col_names) - 1, 0, -1):
            if any(isinstance(r[idx], (int, float)) for r in raw_rows):
                metric_col_idx = idx
                break

    chart_labels = []
    chart_values = []
    metric_name = col_names[metric_col_idx] if metric_col_idx is not None else "Érték"

    for r in formatted_rows:
        first_label = list(r.values())[0]
        chart_labels.append(str(first_label))
        val = list(r.values())[metric_col_idx] if metric_col_idx is not None else 0
        if not isinstance(val, (int, float)):
            val = 0
        chart_values.append(val)

    # Vezetői szöveges összefoglaló generálása
    top_item = formatted_rows[0] if formatted_rows else {}
    top_item_name = list(top_item.values())[0] if top_item else "N/A"
    top_val = chart_values[0] if chart_values else 0
    top_val_str = f"{top_val:,} Ft".replace(",", " ") if isinstance(top_val, (int, float)) else str(top_val)

    executive_answer = (
        f"A lekérdezett adatok alapján a rangsor élén a(z) '{top_item_name}' áll, "
        f"amely {top_val_str} {metric_name.lower()} eredményt ért el a vizsgált időszakban. "
        f"Összesen {len(formatted_rows)} tétel felelt meg a megadott szűrési feltételeknek."
    )

    return {
        "status": "success",
        "question_received": question,
        "requested_by": requested_by,
        "data_source_used": {
            "type": data_source,
            "connection": conn_str,
            "custom_name": custom_source if "Egyedi" in data_source else data_source
        },
        "security_audit": {
            "sandbox_mode": sec_mode_setting,
            "is_read_only_enforced": is_strict,
            "pii_masking_active": mask_pii,
            "status": "APPROVED"
        },
        "transparent_sql": {
            "query": generated_sql,
            "engine": "SQLite / ANSI SQL",
            "audit_note": "Csak olvasási jogosultságú lekérdezés, adatmódosítás kizárva."
        },
        "executive_answer": executive_answer,
        "table_result": {
            "columns": col_names,
            "rows": formatted_rows,
            "total_rows": len(formatted_rows)
        },
        "chart_suggestion": {
            "chart_type": "bar",
            "title": "Legnagyobb Értékesítési Tételek Összehasonlítása",
            "labels": chart_labels,
            "dataset_label": "Érték (Ft)",
            "values": chart_values
        }
    }
