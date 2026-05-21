"""
ERP Integration Layer for DPP-ERP Prototype
ViennaUP Hackathon 2026

Drop this file next to app_v2.py.
It handles all communication with the Mock ERP REST API (localhost:5000).
Falls back gracefully to SQLite-only mode if the API is unreachable.

Usage Example:
    from erp_connector import ERPConnector
    erp = ERPConnector()

    # purchase order
    result = erp.create_purchase_order(
        battery_id="bat_001",
        battery_name="Northvolt Gen4",
        supplier="Northvolt AB",
        quantity=10,
        unit_price=4200.0,
        score=87.5,
        notes="Top ranked by Procurement Advisor"
    )

    # EOL decision
    result = erp.create_eol_decision(
        battery_id="bat_003",
        battery_name="Samsung SDI",
        decision="second_life",
        state_of_health=72.4,
        reason="SOH above 70% — suitable for stationary storage",
        estimated_value=1800.0
    )
"""

import requests
import json

ERP_BASE_URL = "http://localhost:5000/api"
TIMEOUT = 5  # seconds


class ERPConnector:
    def __init__(self, base_url: str = ERP_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self._online = None  # cached connectivity state

    # Connectivity
    def is_online(self) -> bool:
        """Check if the Mock ERP API is reachable."""
        try:
            r = requests.get(f"{self.base_url}/health", timeout=TIMEOUT)
            self._online = r.status_code == 200
        except Exception:
            self._online = False
        return self._online

    def status_badge(self) -> dict:
        """
        Returns a dict for displaying a status badge in Streamlit.
        Example:
            badge = erp.status_badge()
            st.success(badge["message"]) if badge["online"] else st.warning(badge["message"])
        """
        online = self.is_online()
        return {
            "online": online,
            "message": (
                "✅ Mock ERP API connected (localhost:5000)"
                if online
                else "⚠️ Mock ERP API offline — running in local SQLite mode"
            ),
            "color": "green" if online else "orange",
        }

    # Internal helpers
    def _post(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            r = requests.post(url, json=payload, timeout=TIMEOUT)
            r.raise_for_status()
            return {"success": True, "data": r.json(), "status_code": r.status_code}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "ERP API not reachable", "offline": True}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": str(e), "status_code": r.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            r = requests.get(url, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            return {"success": True, "data": r.json()}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "ERP API not reachable", "offline": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _patch(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            r = requests.patch(url, json=payload, timeout=TIMEOUT)
            r.raise_for_status()
            return {"success": True, "data": r.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------ #
    # Purchase Orders
    # ------------------------------------------------------------------ #
    def create_purchase_order(
        self,
        battery_id: str,
        battery_name: str,
        supplier: str,
        quantity: int = 1,
        unit_price: float = 0.0,
        score: float = 0.0,
        notes: str = "",
    ) -> dict:
        """
        POST /api/purchase-orders
        Returns a result dict with keys: success, erp_reference, data, error
        """
        payload = {
            "battery_id": battery_id,
            "battery_name": battery_name,
            "supplier": supplier,
            "quantity": quantity,
            "unit_price": unit_price,
            "score": score,
            "notes": notes,
        }
        result = self._post("/purchase-orders", payload)
        if result["success"]:
            result["erp_reference"] = result["data"].get("erp_reference", "N/A")
        return result

    def get_purchase_orders(self) -> dict:
        """GET /api/purchase-orders"""
        return self._get("/purchase-orders")

    def get_purchase_order(self, po_id: str) -> dict:
        """GET /api/purchase-orders/<id>"""
        return self._get(f"/purchase-orders/{po_id}")

    def approve_purchase_order(self, po_id: str) -> dict:
        """PATCH /api/purchase-orders/<id>/status  → approved"""
        return self._patch(f"/purchase-orders/{po_id}/status", {"status": "approved"})

    def update_po_status(self, po_id: str, status: str) -> dict:
        """PATCH /api/purchase-orders/<id>/status"""
        return self._patch(f"/purchase-orders/{po_id}/status", {"status": status})

    # ------------------------------------------------------------------ #
    # EOL Decisions
    # ------------------------------------------------------------------ #
    def create_eol_decision(
        self,
        battery_id: str,
        battery_name: str,
        decision: str,
        state_of_health: float = 0.0,
        reason: str = "",
        estimated_value: float = 0.0,
    ) -> dict:
        """
        POST /api/eol-decisions
        decision must be one of: repair | second_life | recycle | scrap
        Returns a result dict with keys: success, erp_reference, data, error
        """
        payload = {
            "battery_id": battery_id,
            "battery_name": battery_name,
            "decision": decision,
            "state_of_health": state_of_health,
            "reason": reason,
            "estimated_value": estimated_value,
        }
        result = self._post("/eol-decisions", payload)
        if result["success"]:
            result["erp_reference"] = result["data"].get("erp_reference", "N/A")
        return result

    def get_eol_decisions(self) -> dict:
        """GET /api/eol-decisions"""
        return self._get("/eol-decisions")

    # ------------------------------------------------------------------ #
    # Products
    # ------------------------------------------------------------------ #
    def register_product(
        self, name: str, battery_id: str, category: str = "Battery"
    ) -> dict:
        """POST /api/products"""
        payload = {"name": name, "battery_id": battery_id, "category": category}
        return self._post("/products", payload)

    def get_products(self) -> dict:
        """GET /api/products"""
        return self._get("/products")

    # ------------------------------------------------------------------ #
    # Dashboard summary
    # ------------------------------------------------------------------ #
    def get_dashboard_summary(self) -> dict:
        """GET /api/dashboard/summary"""
        return self._get("/dashboard/summary")

    # ------------------------------------------------------------------ #
    # Pretty-print for debugging
    # ------------------------------------------------------------------ #
    def print_summary(self):
        result = self.get_dashboard_summary()
        if result["success"]:
            print(json.dumps(result["data"], indent=2))
        else:
            print(f"Could not reach ERP: {result['error']}")
