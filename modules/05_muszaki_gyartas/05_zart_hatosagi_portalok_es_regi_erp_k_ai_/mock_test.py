# -*- coding: utf-8 -*-
import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handler import run

def test_gov_portal_rpa():
    test_payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
    with open(test_payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    result = run(payload)
    print("Test Result Success:", result.get("success"))
    print("Job ID:", result.get("job_id"))
    print("Official Case Number:", result.get("official_case_number"))

    security = result.get("security_and_avdh", {})
    print("2FA Status:", security.get("two_factor_auth", {}).get("status"))
    print("AVDH Signed Count:", security.get("avdh_signing", {}).get("signed_files_count"))

    rpa_exec = result.get("rpa_execution_details", {})
    print("Portal Execution Status:", rpa_exec.get("portal_execution_status"))
    print("DOM Anomalies Healed:", rpa_exec.get("dom_self_healing", {}).get("anomalies_healed"))

    sync_res = result.get("legacy_erp_and_dms_sync", {})
    print("Legacy ERP Sync Status:", sync_res.get("legacy_erp_sync", {}).get("sync_status"))
    print("Cloud DMS Status:", sync_res.get("cloud_dms_sync", {}).get("dms_status"))

    assert result.get("success") is True, "Expected success to be True"
    assert result.get("official_case_number") is not None, "Case number must be generated"
    assert security.get("avdh_signing", {}).get("signed_files_count") == 3, "Expected 3 signed files"
    assert rpa_exec.get("dom_self_healing", {}).get("anomalies_healed") == 1, "Expected 1 healed anomaly"
    print("All assertions passed successfully!")

if __name__ == "__main__":
    test_gov_portal_rpa()
