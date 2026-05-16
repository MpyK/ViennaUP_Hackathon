"""
odoo_integration.py
====================
Integration layer — pushes DPP Battery Passport data into Odoo ERP
using JSON-RPC (works with Odoo SaaS / odoo.com instances)
"""

import json
import requests

# ── Config ─────────────────────────────────────────────────────────────────────
ODOO_URL     = "https://summa.odoo.com"
ODOO_DB      = "summa"
ODOO_USER    = "muthukrishnan158020@gmail.com"
ODOO_API_KEY = "a243afaf9fa35fd57fc8e5e7c0207fa168b40dbf"


def odoo_call(session, model, method, args, kwargs=None):
    """Make a JSON-RPC call to Odoo."""
    if kwargs is None:
        kwargs = {}
    response = session.post(
        f"{ODOO_URL}/web/dataset/call_kw",
        json={
            "jsonrpc": "2.0",
            "method":  "call",
            "id":      1,
            "params": {
                "model":  model,
                "method": method,
                "args":   args,
                "kwargs": kwargs,
            }
        }
    )
    result = response.json()
    if "error" in result:
        raise Exception(result["error"]["data"]["message"])
    return result["result"]


def connect_odoo():
    """Authenticate with Odoo and return session + uid."""
    print(f"Connecting to {ODOO_URL}...")
    session = requests.Session()

    response = session.post(
        f"{ODOO_URL}/web/session/authenticate",
        json={
            "jsonrpc": "2.0",
            "method":  "call",
            "id":      1,
            "params": {
                "db":       ODOO_DB,
                "login":    ODOO_USER,
                "password": ODOO_API_KEY,
            }
        }
    )

    result = response.json()
    uid = result.get("result", {}).get("uid")

    if not uid:
        raise Exception(f"Authentication failed: {result.get('error', result)}")

    print(f"Connected successfully. User ID: {uid}")
    return session, uid


def build_dpp_note(passport):
    """Build formatted DPP text for Odoo product description."""
    g    = passport["general"]
    cf   = passport["carbon_footprint"]
    rc   = passport["recycled_content"]
    crm  = passport["critical_raw_materials"]
    comp = passport["compliance"]
    soh  = passport["state_of_health"]
    eol  = passport["end_of_life"]

    return f"""=== DIGITAL PRODUCT PASSPORT ===
Regulation: EU 2023/1542 | QR: {passport['qr_code']}
Compliance: {comp['compliance_status']}

GENERAL
Manufacturer: {g['manufacturer']}
Model: {g['model']}
Chemistry: {g['chemistry']}
Capacity: {g['capacity_kwh_gross']} kWh | Weight: {g['weight_kg']} kg
Cell Maker: {g['cell_manufacturer']} | Made: {g['date_of_manufacture']}

CARBON FOOTPRINT
Total: {cf['total_kg_co2e']} kg CO2e | Per kWh: {cf['per_kwh_kg_co2e']} kg CO2e/kWh
Class: {cf['performance_class']} | Renewable: {'Yes' if cf['renewable_energy_used'] else 'No'}

RECYCLED CONTENT
Cobalt: {rc['cobalt_pct']}% | Lithium: {rc['lithium_pct']}% | Nickel: {rc['nickel_pct']}%

CRITICAL RAW MATERIALS
Cobalt: {crm['cobalt_kg']} kg from {crm['cobalt_origin']}
Nickel: {crm['nickel_kg']} kg from {crm['nickel_origin']}
Lithium: {crm['lithium_kg']} kg from {crm['lithium_origin']}

COMPLIANCE
CE Marked: {'YES' if comp['ce_marked'] else 'NO - MISSING'}
DoC Ref: {comp['doc_reference']}
Notified Body: {comp['notified_body']}
Verifier: {comp['independent_verifier']}

STATE OF HEALTH
SoH: {soh['soce_pct']}% | Capacity: {soh['remaining_capacity_kwh']} kWh
Cycles: {soh['full_equivalent_cycles']} | Status: {soh['status']}

END OF LIFE
Recyclability: {eol['recyclability_pct']}% | 2nd Life: {'Yes' if eol['second_life_eligible'] else 'No'}
Take-back: {eol['take_back_network']}"""


def push_passport(session, passport):
    """Push one Battery Passport into Odoo as a product."""
    g    = passport["general"]
    name = f"[DPP] {g['model']} | {passport['id']}"
    note = build_dpp_note(passport)

    # Check if product already exists
    existing = odoo_call(
        session, "product.template", "search_read",
        [[["default_code", "=", passport["id"]]]],
        {"fields": ["id", "name"], "limit": 1}
    )

    product_data = {
        "name":         name,
        "type":         "product",
        "description":  note,
        "default_code": passport["id"],
        "list_price":   0.0,
    }

    if existing:
        odoo_call(session, "product.template", "write",
                  [[existing[0]["id"]], product_data])
        print(f"  UPDATED → {name}")
        return existing[0]["id"]
    else:
        product_id = odoo_call(session, "product.template", "create",
                               [product_data])
        print(f"  CREATED → {name} (Odoo ID: {product_id})")
        return product_id


def sync_all_passports():
    """Main sync function."""
    print("\n" + "=" * 60)
    print("  DPP → ODOO INTEGRATION SYNC")
    print("  ViennaUP Hackathon 2026")
    print("=" * 60)

    # Load passport data
    with open("passports.json", "r") as f:
        data = json.load(f)
    passports = data["batteries"]
    print(f"\nLoaded {len(passports)} battery passports")

    # Connect
    try:
        session, uid = connect_odoo()
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # Push each passport
    print(f"\nSyncing to Odoo...")
    results = []
    for passport in passports:
        try:
            pid = push_passport(session, passport)
            results.append({"id": passport["id"], "success": True, "odoo_id": pid})
        except Exception as e:
            print(f"  ERROR {passport['id']}: {e}")
            results.append({"id": passport["id"], "success": False})

    # Summary
    ok = sum(1 for r in results if r["success"])
    print(f"\n{'=' * 60}")
    print(f"  DONE: {ok}/{len(passports)} synced to Odoo")
    print(f"  View: {ODOO_URL}/odoo/inventory/products")
    print("=" * 60)
    for r in results:
        print(f"  {'✅' if r['success'] else '❌'} {r['id']}")


if __name__ == "__main__":
    sync_all_passports()
