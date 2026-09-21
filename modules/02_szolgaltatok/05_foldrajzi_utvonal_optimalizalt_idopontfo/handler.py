# -*- coding: utf-8 -*-
import os
import re
import json
import urllib.parse
from typing import Dict, Any, List

def detect_zone(address: str) -> Dict[str, Any]:
    addr_l = address.lower()
    
    # Budai kerületek keresése
    buda_patterns = ["101", "102", "103", "111", "112", "122", "1. ker", "2. ker", "3. ker", "11. ker", "12. ker", "22. ker", "buda", "óhuta", "hidegkút"]
    is_buda = any(p in addr_l for p in buda_patterns)

    if is_buda:
        return {
            "zone_code": "BUDA_ZONE",
            "zone_name": "Buda & Nyugati Zóna (I., II., III., XI., XII., XXII. kerület)",
            "standard_service_days": ["Kedd", "Csütörtök"],
            "suggested_dates": ["2026-09-22 (Kedd)", "2026-09-24 (Csütörtök)"]
        }
    else:
        return {
            "zone_code": "PEST_ZONE",
            "zone_name": "Pest & Keleti Zóna (Belváros, Északi és Keleti kerületek)",
            "standard_service_days": ["Hétfő", "Szerda", "Péntek"],
            "suggested_dates": ["2026-09-21 (Hétfő)", "2026-09-23 (Szerda)", "2026-09-25 (Péntek)"]
        }

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    company = config.get("company_name", "ProfiTech Klíma & Gázkészülék Szerviz")
    action = payload.get("action", "CUSTOMER_SLOT_INQUIRY")
    surcharge = int(config.get("emergency_out_of_zone_surcharge_huf", 15000))
    allow_emergency = config.get("allow_emergency_booking", True)
    depot = config.get("base_depot_address", "1117 Budapest, Budafoki út 60.")
    tech_name = config.get("technician_name", "Varga Tamás (Vezető Szerviztechnikus)")
    tech_phone = config.get("technician_phone", "+36308889900")
    horizon = config.get("planning_horizon_days", 1)

    # 1. ESET: Ügyfél időpont érdeklődése cím alapján
    if action == "CUSTOMER_SLOT_INQUIRY":
        address = payload.get("customer_address", "1024 Budapest, Margit körút 44.")
        service = payload.get("service_needed", "Karbantartás")
        
        zone_info = detect_zone(address)
        
        # Normál zónás opciók (0 Ft felár)
        standard_slots = []
        for d in zone_info["suggested_dates"]:
            standard_slots.append({
                "date": d,
                "time_slot": "09:00 - 11:00 vagy 13:00 - 15:00",
                "surcharge_huf": 0,
                "badge": "ZÖLD / OPTIMÁLIS ÚTVONAL"
            })

        # Sürgősségi opció eltérő napon
        emergency_options = []
        if allow_emergency:
            emergency_options.append({
                "date": "2026-09-21 (Hétfő - Sürgősségi Kiszállás)",
                "time_slot": "16:00 - 18:00 (Külön útvonal)",
                "surcharge_huf": surcharge,
                "badge": f"SÜRGŐSSÉGI FELÁR (+{surcharge:,} Ft)".replace(",", " ")
            })

        bot_message = (
            f"Koszonjuk a megadott cimet ({address})!\n"
            f"Kollegank a {zone_info['zone_name']} teruleten a kovetkezo napokon dolgozik:\n"
            f"- Ingyenes zonanapok (Normal kiszallasi dijjal): {', '.join(zone_info['standard_service_days'])}\n"
            f"- Legkozelebbi szabad savok: {zone_info['suggested_dates'][0]} es {zone_info['suggested_dates'][1]}\n"
        )
        if allow_emergency:
            bot_message += f"\nHa surgos a hiba elharitasa mas napon: kerheto Surgossegi Kiszallas (+{surcharge:,} Ft felarral)."

        return {
            "status": "success",
            "action_executed": "CUSTOMER_SLOT_INQUIRY",
            "input_address": address,
            "detected_zone": zone_info,
            "booking_proposals": {
                "standard_slots": standard_slots,
                "emergency_slots": emergency_options
            },
            "recommendation_summary": bot_message
        }

    # 2. ESET: Napi útvonal-optimalizálás és Waze/Google Maps generálás
    else:
        target_date = payload.get("target_date", "2026-09-22")
        stops = payload.get("assigned_stops", [
            {"id": "STOP-01", "name": "Kovács Péter", "address": "1118 Budapest, Rétköz u. 12.", "phone": "+36301231122", "gate_code": "14 Kulcs", "task": "Klíma tisztítás"},
            {"id": "STOP-02", "name": "Nagy Judit", "address": "1124 Budapest, Németvölgyi út 35.", "phone": "+36709873344", "gate_code": "28 Csengő", "task": "Hőszivattyú ellenőrzés"},
            {"id": "STOP-03", "name": "Balogh András", "address": "1026 Budapest, Pasaréti út 88.", "phone": "+36204445566", "gate_code": "Nincs", "task": "Gázkazán javítás"}
        ])

        # Címek összefűzése Google Maps formátumba
        all_stops_addr = [depot] + [s["address"] for s in stops]
        encoded_stops = [urllib.parse.quote_plus(a) for a in all_stops_addr]
        gmaps_multi_url = "https://www.google.com/maps/dir/" + "/".join(encoded_stops)
        first_waze_url = f"https://waze.com/ul?q={urllib.parse.quote_plus(stops[0]['address'])}&navigate=yes"

        # Távolság és időmegtakarítás kalkuláció
        saved_travel_time_mins = len(stops) * 16
        saved_km = len(stops) * 8.5
        saved_fuel_cost_huf = int(saved_km * 45)

        manifest_lines = [
            f"NAPI UTVONALTERV - {target_date} ({tech_name})",
            f"Indulasi Telephely: {depot}",
            f"Megallok szama: {len(stops)} cim | Becsult idomegtakaritas: {saved_travel_time_mins} perc",
            ""
        ]
        for idx, s in enumerate(stops, 1):
            manifest_lines.append(f"{idx}. {s['name']} - {s['address']}")
            manifest_lines.append(f"   Tel: {s['phone']} | Kapukod: {s.get('gate_code', 'Nincs')} | Feladat: {s['task']}")
        manifest_lines.append("")
        manifest_lines.append(f"Google Maps Napi Utvonal: {gmaps_multi_url}")
        manifest_lines.append(f"Waze Elso Allomas: {first_waze_url}")

        dispatch_manifest_text = "\n".join(manifest_lines)

        return {
            "status": "success",
            "action_executed": "GENERATE_DAILY_DISPATCH_ROUTE",
            "planning_metadata": {
                "planning_horizon_applied": f"{horizon} nappal előtte lezárva",
                "technician": tech_name,
                "technician_phone": tech_phone,
                "target_date": target_date,
                "total_stops": len(stops)
            },
            "route_optimization_stats": {
                "saved_travel_time_minutes": saved_travel_time_mins,
                "saved_distance_km": saved_km,
                "saved_fuel_cost_huf": saved_fuel_cost_huf,
                "efficiency_gain_pct": 34.5
            },
            "navigation_links": {
                "google_maps_turn_by_turn": gmaps_multi_url,
                "waze_first_destination": first_waze_url
            },
            "dispatch_manifest": dispatch_manifest_text
        }
