"""
B2B Kintlévőség-kezelés 40 EUR Költségátalánnyal
Modul: 07_b2b_kintlevoseg_kezeles_40_eur_koltsegat
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class B2BDebtCollectionHandler:
    """
    Szigorú B2B Kintlévőség-kezelő és Hitelkontrolling Motor.
    Kezeli a 4-lépcsős felszólító láncolatot, a raktári szállítási zárolást (Credit Hold),
    a 2016. évi IX. tv. szerinti 40 EUR költségátalányt és a Ptk. késedelmi kamatot,
    valamint 30+ napos késedelem esetén MOKK-kompatibilis FMH jogi csomagot generál.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.credit_hold_policy = self.config.get("credit_hold_policy", "grace_period_days")
        self.credit_hold_grace_days = int(self.config.get("credit_hold_grace_days", 15))
        self.fee_calculation_mode = self.config.get("fee_calculation_mode", "configurable_per_partner")
        self.allow_vip_fee_waiver = bool(self.config.get("allow_vip_fee_waiver", True))
        self.escalation_mode = self.config.get("escalation_mode", "both_combined")
        self.eur_huf_rate = float(self.config.get("eur_huf_exchange_rate", 405.50))
        self.annual_interest_rate = float(self.config.get("annual_interest_rate_percent", 14.50))
        self.partners_db_path = self.config.get("partners_db_path", "data/b2b_partnerek.json")
        self.collection_db_path = self.config.get("collection_db_path", "data/b2b_kintlevosegek_naplo.json")

    def _load_partner_profile(self, partner_code: str, partner_name: str) -> Dict[str, Any]:
        """Partnerprofil betöltése a B2B partnertörzsből"""
        if os.path.exists(self.partners_db_path):
            try:
                with open(self.partners_db_path, "r", encoding="utf-8") as f:
                    partners = json.load(f)
                for p in partners:
                    if p.get("partner_code") == partner_code or p.get("company_name") == partner_name:
                        return p
            except Exception:
                pass
        return {
            "partner_code": partner_code,
            "company_name": partner_name,
            "tier": "BRONZE",
            "discount_percent": 10.0,
            "credit_limit_huf": 1000000
        }

    def _calculate_delay_and_level(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Késedelmi napok és felszólítási fokozat (Level 1 - 4) megállapítása"""
        due_str = invoice.get("due_date")
        ref_str = invoice.get("reference_date") or datetime.date.today().isoformat()
        
        try:
            due_date = datetime.date.fromisoformat(due_str)
            ref_date = datetime.date.fromisoformat(ref_str)
            days_overdue = (ref_date - due_date).days
        except Exception:
            days_overdue = 15
            
        if days_overdue <= 0:
            level = "LEVEL_0_ON_TIME"
            level_title = "Időben lévő számla"
            severity = "NONE"
        elif days_overdue <= 7:
            level = "LEVEL_1_FRIENDLY_REMINDER"
            level_title = "1. Lépcső: Baráti Emlékeztető"
            severity = "LOW"
        elif days_overdue <= 14:
            level = "LEVEL_2_FORMAL_NOTICE"
            level_title = "2. Lépcső: Hivatalos Fizetési Felszólítás"
            severity = "MEDIUM"
        elif days_overdue <= 29:
            level = "LEVEL_3_STRICT_HOLD_AND_FEE"
            level_title = "3. Lépcső: Szigorú Zárlat & 40 EUR Behajtási Átalány"
            severity = "HIGH_URGENT"
        else:
            level = "LEVEL_4_LEGAL_FMH_ESCALATION"
            level_title = "4. Lépcső: Jogi és FMH (Fizetési Meghagyás) Átadás"
            severity = "LEGAL_CRITICAL"
            
        return {
            "days_overdue": max(0, days_overdue),
            "due_date": due_str,
            "reference_date": ref_str,
            "level": level,
            "level_title": level_title,
            "severity": severity
        }

    def _calculate_penalties(self, invoice: Dict[str, Any], days_overdue: int, partner_tier: str) -> Dict[str, Any]:
        """Késedelmi kamat (Ptk. 6:155. §) és 40 EUR költségátalány (2016. évi IX. tv.) számítás"""
        orig = float(invoice.get("original_amount", 0))
        paid = float(invoice.get("paid_amount", 0))
        principal_huf = max(0.0, orig - paid)
        
        # Késedelmi kamat kalkuláció
        if days_overdue > 0:
            daily_interest_rate = (self.annual_interest_rate / 100.0) / 365.0
            interest_huf = round(principal_huf * daily_interest_rate * days_overdue)
        else:
            interest_huf = 0
            
        # 40 EUR behajtási költségátalány
        fee_eur = 40.0
        fee_huf = round(fee_eur * self.eur_huf_rate)
        
        # Szabály alapú érvényesítés (15 napos csúszás után vagy azonnal mód szerint)
        apply_fee = False
        if self.fee_calculation_mode == "auto_invoice_immediate" and days_overdue >= 1:
            apply_fee = True
        elif days_overdue >= 15:
            apply_fee = True
            
        fee_waived = False
        waiver_note = None
        
        # VIP méltányossági kedvezmény elengedése (ha engedélyezett)
        if apply_fee and self.allow_vip_fee_waiver and partner_tier in ["GOLD", "PLATINUM"] and self.fee_calculation_mode == "configurable_per_partner":
            fee_waived = True
            waiver_note = "Kiemelt VIP partneri méltányosság: A 40 EUR behajtási díj elengedve az azonnali tőketartozás-rendezés fejében."
            billed_fee_huf = 0
        elif apply_fee:
            billed_fee_huf = fee_huf
        else:
            billed_fee_huf = 0
            
        total_payable_huf = round(principal_huf + interest_huf + billed_fee_huf)
        
        return {
            "principal_huf": principal_huf,
            "interest_rate_percent": self.annual_interest_rate,
            "accumulated_interest_huf": interest_huf,
            "statutory_fee_eur": fee_eur,
            "eur_huf_rate": self.eur_huf_rate,
            "statutory_fee_huf": fee_huf,
            "fee_applied": apply_fee,
            "fee_waived": fee_waived,
            "fee_waiver_note": waiver_note,
            "billed_recovery_fee_huf": billed_fee_huf,
            "total_payable_huf": total_payable_huf
        }

    def _evaluate_credit_hold(self, invoice: Dict[str, Any], days_overdue: int, partner_tier: str) -> Dict[str, Any]:
        """Raktári rendelés zárolás (Credit Hold) és szállítási stop vizsgálat"""
        pending_orders = invoice.get("pending_orders", [])
        is_hold_active = False
        hold_type = "CLEAR"
        hold_message = "A partner hitelkerete és rendeléskiszolgálása aktív."
        
        if self.credit_hold_policy == "immediate_freeze":
            if days_overdue >= 1:
                is_hold_active = True
                hold_type = "IMMEDIATE_DISPATCH_FREEZE"
                hold_message = f"SZÁLLÍTÁSI STOP AKTÍV! {days_overdue} napos késedelem miatt új rendelés nem adható ki."
        elif self.credit_hold_policy == "manager_override_warning":
            if days_overdue >= 1:
                is_hold_active = True
                hold_type = "WARNING_MANAGER_OVERRIDE_REQUIRED"
                hold_message = "FIGYELMEZTETÉS: Lejárt tartozás! Szállítás kizárólag cégvezetői jóváhagyással engedélyezett."
        else:  # grace_period_days
            if days_overdue >= self.credit_hold_grace_days:
                is_hold_active = True
                hold_type = "GRACE_PERIOD_EXCEEDED_FREEZE"
                hold_message = f"RAKTÁRI ZÁROLÁS! A {self.credit_hold_grace_days} napos türelmi idő lejárt ({days_overdue} napos késés). Árukiadás tiltva!"
            elif days_overdue >= 8:
                is_hold_active = False
                hold_type = "PRE_HOLD_WARNING"
                hold_message = f"FIGYELMEZTETŐ ZÓNA: {days_overdue} napos késedelem. Raktári zárolásig hátralévő idő: {self.credit_hold_grace_days - days_overdue} nap."
                
        # Függőben lévő megrendelések státuszának frissítése
        updated_orders = []
        for order in pending_orders:
            ord_copy = dict(order)
            if is_hold_active:
                ord_copy["dispatch_status"] = "LOCKED_CREDIT_HOLD"
                ord_copy["warehouse_instruction"] = "Árukiadás megtagadva – Pénzügyi zárlat"
            else:
                ord_copy["dispatch_status"] = "APPROVED_FOR_DISPATCH"
                ord_copy["warehouse_instruction"] = "Normál kiadás engedélyezve"
            updated_orders.append(ord_copy)
            
        # Partner kedvezmény védelmi figyelmeztetés
        tier_warning = None
        if days_overdue >= 15 and partner_tier in ["GOLD", "PLATINUM"]:
            tier_warning = f"FIGYELEM: A partner {partner_tier} kedvezménye (-22% / -28%) és halasztott fizetési joga felfüggesztésre kerül, amíg a tartozás fennáll!"
            
        return {
            "credit_hold_policy": self.credit_hold_policy,
            "is_hold_active": is_hold_active,
            "hold_type": hold_type,
            "hold_message": hold_message,
            "tier_downgrade_warning": tier_warning,
            "frozen_orders_count": len(updated_orders) if is_hold_active else 0,
            "pending_orders": updated_orders
        }

    def _generate_notice_letter(self, invoice: Dict[str, Any], delay_info: Dict[str, Any], penalty_info: Dict[str, Any], hold_info: Dict[str, Any], partner: Dict[str, Any]) -> Dict[str, Any]:
        """Hivatalos B2B felszólító levél generálása jogszabályi hivatkozásokkal"""
        company = invoice.get("partner_name") or partner.get("company_name", "Partner")
        contact = invoice.get("contact_person") or partner.get("contact_person", "Ügyvezető")
        inv_num = invoice.get("invoice_number", "SZAMLA-N/A")
        due = delay_info["due_date"]
        days = delay_info["days_overdue"]
        principal = penalty_info["principal_huf"]
        interest = penalty_info["accumulated_interest_huf"]
        fee = penalty_info["billed_recovery_fee_huf"]
        total = penalty_info["total_payable_huf"]
        level = delay_info["level"]
        
        if level == "LEVEL_1_FRIENDLY_REMINDER":
            subject = f"Baráti emlékeztető lejárt számláról – {inv_num} ({company})"
            body_lines = [
                f"Tisztelt {contact}!",
                "",
                f"Értesítjük, hogy nyilvántartásunk szerint a(z) {inv_num} számú számlánk (összeg: {principal:,.0f} Ft), melynek fizetési határideje {due} volt, még nem került kiegyenlítésre.",
                "",
                "Kérjük, szíveskedjenek ellenőrizni és a mai napon átutalni az összeget központi bankszámlánkra:",
                "Bankszámlaszám: OTP Bank 11705008-20498112",
                f"Közlemény: {inv_num}",
                "",
                "Amennyiben a fizetés időközben már megtörtént, kérjük, levelünket tekintse tárgytalannak.",
                "Üdvözlettel: ProfiGépész Pénzügyi Osztály"
            ]
        elif level == "LEVEL_2_FORMAL_NOTICE":
            subject = f"Hivatalos fizetési felszólítás – {inv_num} – Szállítási zárlat figyelmeztetés"
            body_lines = [
                f"Tisztelt {contact}!",
                "",
                f"Hivatkozva a(z) {inv_num} számú számlánkra ({principal:,.0f} Ft), sajnálattal tapasztaljuk, hogy az immár {days} napja lejárt ({due}).",
                "",
                "Tájékoztatjuk, hogy cégünk szigorú hitelkontrolling szabályzata alapján a 15 napot meghaladó késedelem esetén a 2016. évi IX. törvény értelmében 40 EUR behajtási költségátalány és Ptk. késedelmi kamat kerül felszámításra, valamint a raktári árukiadás és új rendelések kiszolgálása zárolásra kerül.",
                "",
                "Kérjük, a számla összegét 3 banki munkanapon belül hiánytalanul utalják át!",
                "Fizetési határidő: 3 munkanap | Bankszámla: OTP Bank 11705008-20498112",
                "Üdvözlettel: ProfiGépész Kintlévőség-kezelési Csoport"
            ]
        elif level == "LEVEL_3_STRICT_HOLD_AND_FEE":
            subject = f"SZIGORÚ FELSZÓLÍTÁS & 40 EUR KÖLTSÉGÁTALÁNY – RAKTÁRI ZÁROLÁS – {inv_num}"
            body_lines = [
                f"Tisztelt {contact}!",
                "",
                f"Ezúton hivatalosan felszólítjuk a(z) {company}-t a(z) {inv_num} számú lejárt számla rendezésére!",
                f"Késedelem időtartama: {days} nap (Esedékesség: {due}).",
                "",
                "KÖVETELÉS ÖSSZESÍTŐ:",
                f"1. Eredeti tőketartozás: {principal:,.0f} Ft",
                f"2. Ptk. 6:155. § szerinti késedelmi kamat: {interest:,.0f} Ft",
                f"3. 2016. évi IX. tv. szerinti 40 EUR behajtási költségátalány: {fee:,.0f} Ft",
                f"-> ÖSSZESEN FIZETENDŐ: {total:,.0f} Ft",
                "",
                "ÉRTESÍTÉS RAKTÁRI SZÁLLÍTÁSI STOPRÓL:",
                f"A kintlévőség fennállása miatt a(z) {company} részére a raktári árukiadást és új megrendelések teljesítését azonnali hatállyal felfüggesztettük!",
                "A szállítási zárlat feloldásának feltétele a teljes tartozás banki jóváírása.",
                "",
                "Azonnali fizetési határidő: 48 óra.",
                "Üdvözlettel: ProfiGépész Jogi és Pénzügyi Igazgatóság"
            ]
        else:  # LEVEL_4_LEGAL_FMH_ESCALATION
            subject = f"ÜGYVÉDI ÉS KÖZJEGYZŐI FMH ÁTADÁS ELŐTTI UTOLSÓ FELSZÓLÍTÁS – {inv_num}"
            body_lines = [
                f"Tisztelt {contact}!",
                "",
                f"Tájékoztatjuk, hogy a(z) {company} ellen a(z) {inv_num} számla kapcsán fennálló {total:,.0f} Ft összegű követelésünket ({days} napos súlyos késedelem) a mai nappal jogi útra tereljük.",
                "",
                "Önökkel szemben a Magyar Országos Közjegyzői Kamara (MOKK) rendszerén keresztül",
                "FIZETÉSI MEGHAGYÁSOS (FMH) ÉS VÉGREHAJTÁSI ELJÁRÁST KEZDEMÉNYEZÜNK,",
                "melynek valamennyi eljárási, ügyvédi és végrehajtási díja a kötelezettet terheli!",
                "",
                "Utolsó jogvesztő határidő a peren kívüli rendezésre: 2 munkanap.",
                "ProfiGépész Nagykereskedelmi Kft. Jogi Képviselet"
            ]
            
        return {
            "subject": subject,
            "body": chr(10).join(body_lines),
            "payment_link": f"https://fizetes.profigepesz.hu/pay/{inv_num}",
            "bank_transfer_info": {
                "bank_name": "OTP Bank Nyrt.",
                "account_number": "11705008-20498112-00000000",
                "iban": "HU42117050082049811200000000",
                "swift": "OTPVHUHB",
                "beneficiary": "ProfiGépész Nagykereskedelmi Kft.",
                "reference": inv_num,
                "amount_huf": total
            }
        }

    def _generate_fmh_dossier(self, invoice: Dict[str, Any], delay_info: Dict[str, Any], penalty_info: Dict[str, Any], partner: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """MOKK-kompatibilis Fizetési Meghagyás (FMH) jogi adatcsomag összeállítása (30+ nap esetén)"""
        if delay_info["days_overdue"] < 30 or self.escalation_mode not in ["auto_fmh_package", "both_combined"]:
            return None
            
        inv_num = invoice.get("invoice_number", "SZAMLA-N/A")
        company = invoice.get("partner_name") or partner.get("company_name", "Kötelezett")
        tax_id = invoice.get("tax_id") or partner.get("tax_id", "N/A")
        
        dossier = {
            "dossier_id": f"FMH-MOKK-{inv_num}",
            "status": "READY_FOR_ATTORNEY_SUBMISSION",
            "created_at": datetime.datetime.now().isoformat(),
            "creditor": {
                "name": "ProfiGépész Nagykereskedelmi Kft.",
                "tax_id": "12345678-2-41",
                "address": "1107 Budapest, Szállás utca 21.",
                "legal_representative": "Dr. Varga & Partnerei Ügyvédi Iroda"
            },
            "debtor": {
                "company_name": company,
                "tax_id": tax_id,
                "contact_person": invoice.get("contact_person") or partner.get("contact_person", "N/A"),
                "email": invoice.get("contact_email") or partner.get("contact_email", "N/A"),
                "phone": invoice.get("contact_phone") or partner.get("contact_phone", "N/A")
            },
            "claim_breakdown": {
                "principal_huf": penalty_info["principal_huf"],
                "interest_huf": penalty_info["accumulated_interest_huf"],
                "statutory_fee_40_eur_huf": penalty_info["billed_recovery_fee_huf"],
                "total_claim_huf": penalty_info["total_payable_huf"],
                "legal_basis_interest": "Polgári Törvénykönyvről szóló 2013. évi V. törvény (Ptk.) 6:155. §",
                "legal_basis_recovery_fee": "A behajtási költségátalányról szóló 2016. évi IX. törvény 3. § (1) bek."
            },
            "evidence_attached": [
                f"Eredeti számla másolata ({inv_num})",
                "Igazolt raktári átadás-átvételi szállítólevél",
                "Fizetési felszólítások és elektronikus kézbesítési igazolások (L1, L2, L3)",
                "Törvényes kamatszámítási analitika"
            ],
            "recommended_action": "Közjegyzői FMH azonnali kibocsátása a MOKK elektronikus felületén."
        }
        return dossier

    def process_single_invoice(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Egyetlen lejárt számla komplett B2B kintlévőség vizsgálata"""
        p_code = invoice.get("partner_code", "")
        p_name = invoice.get("partner_name", "")
        partner_profile = self._load_partner_profile(p_code, p_name)
        tier = partner_profile.get("tier", "BRONZE")
        
        delay_info = self._calculate_delay_and_level(invoice)
        days = delay_info["days_overdue"]
        
        penalties = self._calculate_penalties(invoice, days, tier)
        credit_hold = self._evaluate_credit_hold(invoice, days, tier)
        notice_letter = self._generate_notice_letter(invoice, delay_info, penalties, credit_hold, partner_profile)
        fmh_dossier = self._generate_fmh_dossier(invoice, delay_info, penalties, partner_profile)
        
        # KAM riasztás előkészítése
        kam_alert = None
        if delay_info["severity"] in ["HIGH_URGENT", "LEGAL_CRITICAL"]:
            clean_phone = "".join([c for c in invoice.get("contact_phone", "") if c.isdigit() or c == "+"])
            kam_alert = {
                "priority": "URGENT_CREDIT_ALERT",
                "recipient": "Területi Key Account Manager & Pénzügyi Vezető",
                "message": f"Kintlévőségi zárlat aktiválva: {p_name} ({days} napja lejárt, Tartozás: {penalties['total_payable_huf']:,.0f} Ft)",
                "one_click_dial": f"tel:{clean_phone}" if clean_phone else None,
                "action_required": "Azonnali kapcsolatfelvétel a partner ügyvezetőjével!"
            }
            
        record = {
            "invoice_number": invoice.get("invoice_number"),
            "partner_code": p_code,
            "partner_name": p_name,
            "partner_tier": tier,
            "processed_at": datetime.datetime.now().isoformat(),
            "delay_analysis": delay_info,
            "penalties": penalties,
            "credit_hold": credit_hold,
            "notice_letter": notice_letter,
            "fmh_dossier": fmh_dossier,
            "kam_alert": kam_alert
        }
        return record

    def _persist_records(self, processed_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Kintlévőségi adatok és statisztikák tartós naplózása"""
        os.makedirs(os.path.dirname(self.collection_db_path), exist_ok=True)
        existing_records = []
        if os.path.exists(self.collection_db_path):
            try:
                with open(self.collection_db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        existing_records = data
                    elif isinstance(data, dict) and "records" in data:
                        existing_records = data.get("records", [])
            except Exception:
                existing_records = []
                
        existing_map = {r.get("invoice_number"): idx for idx, r in enumerate(existing_records)}
        for pr in processed_records:
            num = pr.get("invoice_number")
            if num in existing_map:
                existing_records[existing_map[num]] = pr
            else:
                existing_records.append(pr)
                existing_map[num] = len(existing_records) - 1
                
        total_overdue = sum(r.get("penalties", {}).get("principal_huf", 0) for r in existing_records)
        total_interest = sum(r.get("penalties", {}).get("accumulated_interest_huf", 0) for r in existing_records)
        total_fees = sum(r.get("penalties", {}).get("billed_recovery_fee_huf", 0) for r in existing_records)
        total_frozen = sum(1 for r in existing_records if r.get("credit_hold", {}).get("is_hold_active"))
        total_fmh = sum(1 for r in existing_records if r.get("fmh_dossier") is not None)
        
        db_payload = {
            "last_updated": datetime.datetime.now().isoformat(),
            "total_tracked_invoices": len(existing_records),
            "collection_metrics": {
                "total_overdue_principal_huf": round(total_overdue),
                "total_accumulated_interest_huf": round(total_interest),
                "total_recovery_fees_huf": round(total_fees),
                "total_payable_claims_huf": round(total_overdue + total_interest + total_fees),
                "accounts_under_credit_hold": total_frozen,
                "fmh_legal_dossiers_prepared": total_fmh
            },
            "records": existing_records
        }
        
        with open(self.collection_db_path, "w", encoding="utf-8") as f:
            json.dump(db_payload, f, indent=2, ensure_ascii=False)
            
        return db_payload["collection_metrics"]

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fő végrehajtási pont"""
        invoices_to_process = []
        if "invoices" in payload and isinstance(payload["invoices"], list):
            invoices_to_process = payload["invoices"]
        elif "invoice" in payload and isinstance(payload["invoice"], dict):
            invoices_to_process = [payload["invoice"]]
        elif "sample_data" in payload and isinstance(payload["sample_data"], dict):
            invoices_to_process = [payload["sample_data"]]
        else:
            invoices_to_process = [payload]
            
        results = []
        for inv in invoices_to_process:
            results.append(self.process_single_invoice(inv))
            
        summary = self._persist_records(results)
        credit_holds = [r for r in results if r["credit_hold"]["is_hold_active"]]
        fmh_cases = [r for r in results if r["fmh_dossier"] is not None]
        
        return {
            "status": "success",
            "module_id": "07_b2b_kintlevoseg_kezeles_40_eur_koltsegat",
            "processed_at": datetime.datetime.now().isoformat(),
            "invoices_processed_count": len(results),
            "collection_metrics": summary,
            "credit_hold_active_count": len(credit_holds),
            "fmh_dossiers_prepared_count": len(fmh_cases),
            "immediate_actions": [
                {
                    "invoice_number": r["invoice_number"],
                    "partner_name": r["partner_name"],
                    "days_overdue": r["delay_analysis"]["days_overdue"],
                    "level": r["delay_analysis"]["level"],
                    "total_payable_huf": r["penalties"]["total_payable_huf"],
                    "credit_hold_active": r["credit_hold"]["is_hold_active"],
                    "kam_alert": r.get("kam_alert")
                }
                for r in results
            ],
            "processed_invoices": results
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Szabványos hub belépési pont"""
    handler = B2BDebtCollectionHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample = {
        "invoices": [
            {
                "invoice_number": "SZ-TEST-001",
                "partner_name": "Teszt Kivitelező Kft.",
                "original_amount": 1000000,
                "due_date": "2026-08-01",
                "reference_date": "2026-09-01"
            }
        ]
    }
    res = run(sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))