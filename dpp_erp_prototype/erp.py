"""
erp.py - Simulated ERP database
Represents what a company's ERP system would normally contain
WITHOUT Digital Product Passport integration
"""

import sqlite3
import os

DB_PATH = "erp_database.db"


def init_erp():
    """Create and populate the simulated ERP database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            battery_id      TEXT PRIMARY KEY,
            product_name    TEXT,
            supplier        TEXT,
            quantity        INTEGER,
            unit_price_eur  REAL,
            total_value_eur REAL,
            warehouse       TEXT,
            received_date   TEXT,
            status          TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id   TEXT PRIMARY KEY,
            name          TEXT,
            country       TEXT,
            contact_email TEXT,
            rating        TEXT
        )
    """)

    # Populate inventory with sample ERP data
    inventory_data = [
        ("B-VOLVO-EX90-2024-001", "Volvo EX90 111kWh Traction Battery",
         "Volvo Cars AB", 12, 18500.00, 222000.00,
         "Warehouse A - Vienna", "2024-03-15", "In Stock"),

        ("B-GENERIC-NMC-2024-002", "EuroBattery 50kWh Industrial NMC622",
         "EuroBattery GmbH", 45, 8200.00, 369000.00,
         "Warehouse B - Linz", "2024-06-01", "In Stock"),

        ("B-NONCOMPLIANT-2023-003", "Generic LFP 50kWh Industrial",
         "UnknownBatt Ltd.", 8, 3100.00, 24800.00,
         "Warehouse C - Graz", "2023-11-20", "Flagged - Compliance Review"),
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO inventory VALUES (?,?,?,?,?,?,?,?,?)
    """, inventory_data)

    # Populate suppliers
    suppliers_data = [
        ("S-001", "Volvo Cars AB", "Sweden", "sustainability@volvocars.com", "A+"),
        ("S-002", "EuroBattery GmbH", "Germany", "compliance@eurobattery.de", "A"),
        ("S-003", "UnknownBatt Ltd.", "Unknown", "N/A", "F - Under Review"),
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO suppliers VALUES (?,?,?,?,?)
    """, suppliers_data)

    conn.commit()
    conn.close()


def get_all_batteries():
    """Return all batteries in the ERP system."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory")
    rows = cursor.fetchall()
    conn.close()

    columns = ["battery_id", "product_name", "supplier", "quantity",
               "unit_price_eur", "total_value_eur", "warehouse",
               "received_date", "status"]
    return [dict(zip(columns, row)) for row in rows]


def get_battery_erp(battery_id):
    """Return ERP data for a specific battery."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE battery_id = ?", (battery_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    columns = ["battery_id", "product_name", "supplier", "quantity",
               "unit_price_eur", "total_value_eur", "warehouse",
               "received_date", "status"]
    return dict(zip(columns, row))
