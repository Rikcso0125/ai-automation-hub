# -*- coding: utf-8 -*-
import os
import json
from handler import run

payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "data_source_type": "Beépített SQLite / Céges Minta Adatbázis",
    "connection_string": "sqlite:///:memory:",
    "security_mode": "Szigorú Csak Olvasás (Strict Read-Only, Adatmódosítás tiltása)",
    "mask_sensitive_pii": "Igen (Jelszavak, banki adatok és személyes adatok maszkolása)",
    "ai_engine": "Beépített Szabály- és Mintaillesztő (Ingyenes, helyi)"
}

print("=== TERMESZETES NYELVU ADATBAZIS KERESO (TEXT-TO-SQL) TESZT ===")
res = run(payload, config)
print("Status:", res.get("status"))
print("Kerdes:", res.get("question_received"))
print("Vezetoi Valasz:", res.get("executive_answer"))
print("Generalt SQL:", res.get("transparent_sql", {}).get("query"))
print("Eredmeny Rekordok Szama:", res.get("table_result", {}).get("total_rows"))
print("Diagram Cimkek:", res.get("chart_suggestion", {}).get("labels"))
print("Diagram Ertekek:", res.get("chart_suggestion", {}).get("values"))
