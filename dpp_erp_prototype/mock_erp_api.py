"""
mock_erp_api.py — Mock ERP REST API for DPP-ERP Prototype
ViennaUP Hackathon 2026

Runs on http://localhost:5000
Simulates a real ERP system with endpoints for:
  - Products / Battery inventory
  - Purchase Orders (from Procurement Advisor)
  - End-of-Life Decisions (from EOL Engine)
  - ERP Health check

Start with:  python mock_erp_api.py
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import uuid
import sqlite3
import os

app = Flask(__name__)
CORS(app)  # Allow Streamlit on port 8501 to call this

# --------------------------------------------------------------------------- #
# In-memory store (also persists to SQLite so it survives restarts)
# --------------------------------------------------------------------------- #
DB_PATH = os.path.join(os.path.dirname(__file__), "erp_database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS erp_products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            battery_id TEXT,
            category TEXT DEFAULT 'Battery',
            status TEXT DEFAULT 'active',
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS erp_purchase_orders (
            id TEXT PRIMARY KEY,
            order_number TEXT UNIQUE,
            battery_id TEXT,
            battery_name TEXT,
            supplier TEXT,
            quantity INTEGER DEFAULT 1,
            unit_price REAL,
            total_price REAL,
            status TEXT DEFAULT 'pending',
            score REAL,
            notes TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS erp_eol_decisions (
            id TEXT PRIMARY KEY,
            decision_number TEXT UNIQUE,
            battery_id TEXT,
            battery_name TEXT,
            decision TEXT,
            state_of_health REAL,
            reason TEXT,
            estimated_value REAL,
            status TEXT DEFAULT 'recorded',
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# --------------------------------------------------------------------------- #
# Utility
# --------------------------------------------------------------------------- #
def new_id():
    return str(uuid.uuid4())

def now():
    return datetime.utcnow().isoformat() + "Z"

def order_number(prefix="PO"):
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{ts}-{str(uuid.uuid4())[:4].upper()}"

def row_to_dict(row):
    return dict(row) if row else None

def rows_to_list(rows):
    return [dict(r) for r in rows]

# --------------------------------------------------------------------------- #
# Health check
# --------------------------------------------------------------------------- #
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "system": "DPP Mock ERP",
        "version": "1.0.0",
        "timestamp": now(),
        "endpoints": [
            "GET  /api/health",
            "GET  /api/products",
            "POST /api/products",
            "GET  /api/purchase-orders",
            "POST /api/purchase-orders",
            "GET  /api/purchase-orders/<id>",
            "PATCH /api/purchase-orders/<id>/status",
            "GET  /api/eol-decisions",
            "POST /api/eol-decisions",
            "GET  /api/eol-decisions/<id>",
            "GET  /api/dashboard/summary",
        ]
    })

# --------------------------------------------------------------------------- #
# Products
# --------------------------------------------------------------------------- #
@app.route("/api/products", methods=["GET"])
def get_products():
    conn = get_db()
    rows = conn.execute("SELECT * FROM erp_products ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify({"count": len(rows), "products": rows_to_list(rows)})

@app.route("/api/products", methods=["POST"])
def create_product():
    data = request.get_json(force=True)
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    product = {
        "id": new_id(),
        "name": data["name"],
        "battery_id": data.get("battery_id", ""),
        "category": data.get("category", "Battery"),
        "status": data.get("status", "active"),
        "created_at": now(),
    }
    conn = get_db()
    conn.execute(
        "INSERT INTO erp_products VALUES (:id,:name,:battery_id,:category,:status,:created_at)",
        product
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Product created", "product": product}), 201

# --------------------------------------------------------------------------- #
# Purchase Orders
# --------------------------------------------------------------------------- #
@app.route("/api/purchase-orders", methods=["GET"])
def get_purchase_orders():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM erp_purchase_orders ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return jsonify({"count": len(rows), "purchase_orders": rows_to_list(rows)})

@app.route("/api/purchase-orders", methods=["POST"])
def create_purchase_order():
    data = request.get_json(force=True)
    required = ["battery_id", "battery_name", "supplier"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    qty = int(data.get("quantity", 1))
    unit_price = float(data.get("unit_price", 0.0))

    po = {
        "id": new_id(),
        "order_number": order_number("PO"),
        "battery_id": data["battery_id"],
        "battery_name": data["battery_name"],
        "supplier": data["supplier"],
        "quantity": qty,
        "unit_price": unit_price,
        "total_price": round(qty * unit_price, 2),
        "status": "pending",
        "score": float(data.get("score", 0.0)),
        "notes": data.get("notes", ""),
        "created_at": now(),
    }

    conn = get_db()
    conn.execute("""
        INSERT INTO erp_purchase_orders
        VALUES (:id,:order_number,:battery_id,:battery_name,:supplier,
                :quantity,:unit_price,:total_price,:status,:score,:notes,:created_at)
    """, po)
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Purchase order created successfully",
        "purchase_order": po,
        "erp_reference": po["order_number"],
    }), 201

@app.route("/api/purchase-orders/<po_id>", methods=["GET"])
def get_purchase_order(po_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM erp_purchase_orders WHERE id=? OR order_number=?",
        (po_id, po_id)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Purchase order not found"}), 404
    return jsonify(row_to_dict(row))

@app.route("/api/purchase-orders/<po_id>/status", methods=["PATCH"])
def update_po_status(po_id):
    data = request.get_json(force=True)
    new_status = data.get("status")
    allowed = ["pending", "approved", "ordered", "received", "cancelled"]
    if new_status not in allowed:
        return jsonify({"error": f"status must be one of {allowed}"}), 400

    conn = get_db()
    cur = conn.execute(
        "UPDATE erp_purchase_orders SET status=? WHERE id=? OR order_number=?",
        (new_status, po_id, po_id)
    )
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        return jsonify({"error": "Purchase order not found"}), 404
    return jsonify({"message": f"Status updated to {new_status}", "status": new_status})

# --------------------------------------------------------------------------- #
# EOL Decisions
# --------------------------------------------------------------------------- #
@app.route("/api/eol-decisions", methods=["GET"])
def get_eol_decisions():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM erp_eol_decisions ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return jsonify({"count": len(rows), "eol_decisions": rows_to_list(rows)})

@app.route("/api/eol-decisions", methods=["POST"])
def create_eol_decision():
    data = request.get_json(force=True)
    required = ["battery_id", "battery_name", "decision"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    valid_decisions = ["repair", "second_life", "recycle", "scrap"]
    if data["decision"].lower() not in valid_decisions:
        return jsonify({"error": f"decision must be one of {valid_decisions}"}), 400

    eol = {
        "id": new_id(),
        "decision_number": order_number("EOL"),
        "battery_id": data["battery_id"],
        "battery_name": data["battery_name"],
        "decision": data["decision"].lower(),
        "state_of_health": float(data.get("state_of_health", 0.0)),
        "reason": data.get("reason", ""),
        "estimated_value": float(data.get("estimated_value", 0.0)),
        "status": "recorded",
        "created_at": now(),
    }

    conn = get_db()
    conn.execute("""
        INSERT INTO erp_eol_decisions
        VALUES (:id,:decision_number,:battery_id,:battery_name,:decision,
                :state_of_health,:reason,:estimated_value,:status,:created_at)
    """, eol)
    conn.commit()
    conn.close()

    return jsonify({
        "message": "EOL decision recorded in ERP",
        "eol_decision": eol,
        "erp_reference": eol["decision_number"],
    }), 201

@app.route("/api/eol-decisions/<eol_id>", methods=["GET"])
def get_eol_decision(eol_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM erp_eol_decisions WHERE id=? OR decision_number=?",
        (eol_id, eol_id)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "EOL decision not found"}), 404
    return jsonify(row_to_dict(row))

# --------------------------------------------------------------------------- #
# Dashboard summary (great for the demo!)
# --------------------------------------------------------------------------- #
@app.route("/api/dashboard/summary", methods=["GET"])
def dashboard_summary():
    conn = get_db()

    po_rows = conn.execute("SELECT status, COUNT(*) as cnt FROM erp_purchase_orders GROUP BY status").fetchall()
    eol_rows = conn.execute("SELECT decision, COUNT(*) as cnt FROM erp_eol_decisions GROUP BY decision").fetchall()
    total_spend = conn.execute("SELECT COALESCE(SUM(total_price),0) as s FROM erp_purchase_orders WHERE status != 'cancelled'").fetchone()["s"]
    product_count = conn.execute("SELECT COUNT(*) as c FROM erp_products").fetchone()["c"]

    conn.close()

    po_by_status = {r["status"]: r["cnt"] for r in po_rows}
    eol_by_decision = {r["decision"]: r["cnt"] for r in eol_rows}

    return jsonify({
        "system": "DPP Mock ERP",
        "timestamp": now(),
        "products_registered": product_count,
        "purchase_orders": {
            "by_status": po_by_status,
            "total": sum(po_by_status.values()),
            "total_spend_eur": round(total_spend, 2),
        },
        "eol_decisions": {
            "by_decision": eol_by_decision,
            "total": sum(eol_by_decision.values()),
        },
    })

# --------------------------------------------------------------------------- #
# Run
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    print("\n🚀 DPP Mock ERP API starting...")
    print("   Base URL : http://localhost:5000")
    print("   Health   : http://localhost:5000/api/health")
    print("   Summary  : http://localhost:5000/api/dashboard/summary")
    print("\n   Press Ctrl+C to stop\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
