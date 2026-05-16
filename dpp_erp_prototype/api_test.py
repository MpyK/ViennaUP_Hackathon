import xmlrpc.client

ODOO_URL = "https://summa.odoo.com"
ODOO_USER = "muthukrishnan158020@gmail.com"
ODOO_API_KEY = "YOUR_API_KEY"

common = xmlrpc.client.ServerProxy(
    f"{ODOO_URL}/xmlrpc/2/common"
)

print("Server version:")
print(common.version())

# Try possible DB names
possible_dbs = [
    "summa",
    "summa.odoo.com",
    "summa-main",
    "production",
    "default",
]

print("\nTesting database names...\n")

for db in possible_dbs:
    try:
        uid = common.authenticate(
            db,
            ODOO_USER,
            ODOO_API_KEY,
            {}
        )

        print(f"DB '{db}' -> UID: {uid}")

        if uid:
            print("\n✅ SUCCESS")
            print("Correct DB =", db)
            break

    except Exception as e:
        print(f"DB '{db}' ERROR:", e)