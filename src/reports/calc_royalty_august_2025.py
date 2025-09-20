#!/usr/bin/env python3
"""
Regner ut 20% royalty av produktverdi eks. mva for alle ordrer i august 2025
""" 

import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, date
import json


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5433')

# Finn inneværende måned (eller bruk ønsket måned via env/argument)
today = date.today()
year = today.year
month = today.month
start_date = f"{year}-{month:02d}-01"
if month == 12:
    end_date = f"{year+1}-01-01"
else:
    end_date = f"{year}-{month+1:02d}-01"
json_filename = f"royalty_report_{year}-{month:02d}.json"

conn = psycopg2.connect(
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT
)
cursor = conn.cursor()


# Hent alle ordrer for valgt måned, kun for din spesifiserte vendor
# Konfigurer VENDOR_NAME i .env filen
cursor.execute(
    "SELECT o.id, o.created_at, o.subtotal_price, o.total_shipping_price, o.total_tax, o.raw_data, c.first_name, c.last_name, c.email "
    "FROM orders o LEFT JOIN customers c ON o.customer_id = c.id "
    f"WHERE o.created_at >= '{start_date}' AND o.created_at < '{end_date}' "
    "ORDER BY o.created_at"
)
orders = cursor.fetchall()






header = (
    f"{'OrdreID':<10} {'Kjøpstidspunkt':<17} {'Pris eks':>10} {'Frakt eks':>10} {'Royalty %':>9} {'Royalty':>10} {'Fladby3D':>10} {'Total eks':>10} "
    f"{'Kjøper':<25} {'Produktnavn':<30} {'E-post':<30}"
)
print(header)
print("-"*len(header))

json_rows = []



royalty_total = 0.0
frakt_total_eks = 0.0
utbetalt_total = 0.0
order_count = 0







for order in orders:
    order_id, created_at, subtotal_price, shipping, tax, raw_data, first_name, last_name, email = order
    raw = raw_data if isinstance(raw_data, dict) else json.loads(raw_data)
    kjøper = f"{first_name or ''} {last_name or ''}".strip()
    tidspunkt = created_at.strftime("%Y-%m-%d %H:%M") if created_at else ""
    frakt_inkl = float(shipping or 0)
    frakt_eks = frakt_inkl / 1.25 if frakt_inkl else 0
    frakt_total_eks += frakt_eks
    epost = email or ''
    # For hver line item i ordren
    for li in raw.get("line_items", []):
        # Sjekk vendor
        vendor_name = os.getenv('VENDOR_NAME', 'your-vendor-name').lower()
        if li.get("vendor", "").lower() != vendor_name:
            continue
        produktnavn = li.get("title", "")
        pris = float(li.get("price", 0)) * int(li.get("quantity", 1))
        # Hent royalty_percent fra products-tabellen
        product_id = li.get("product_id")
        royalty_percent = 20.0
        if product_id:
            cursor2 = conn.cursor()
            cursor2.execute("SELECT royalty_percent FROM products WHERE id = %s", (product_id,))
            res = cursor2.fetchone()
            if res and res[0] is not None:
                royalty_percent = float(res[0])
            cursor2.close()
        pris_eks_mva = pris / 1.25 if pris else 0
        royalty = pris_eks_mva * (royalty_percent / 100.0)
        utbetalt = pris_eks_mva - royalty
        royalty_total += royalty
        utbetalt_total += utbetalt
        total_eks = pris_eks_mva + frakt_eks
        print(f"{str(order_id):<10} {tidspunkt:<17} {pris_eks_mva:>10.2f} {frakt_eks:>10.2f} {royalty_percent:>9.2f} {royalty:>10.2f} {utbetalt:>10.2f} {total_eks:>10.2f} "
              f"{kjøper:<25} {produktnavn:<30} {epost:<30}")
        json_rows.append({
            "order_id": order_id,
            "created_at": tidspunkt,
            "product_name": produktnavn,
            "customer": kjøper,
            "email": epost,
            "price_ex_vat": round(pris_eks_mva,2),
            "shipping_ex_vat": round(frakt_eks,2),
            "royalty_percent": round(royalty_percent,2),
            "royalty": round(royalty,2),
            "fladby3d": round(utbetalt,2),
            "total_ex_vat": round(total_eks,2)
        })
        order_count += 1





print("-"*len(header))
print(f"{'SUM':<37}{frakt_total_eks:>10.2f} {royalty_total:>10.2f} {utbetalt_total:>10.2f}")

# Skriv JSON-rapport for måneden
with open(json_filename, "w", encoding="utf-8") as f:
    json.dump(json_rows, f, ensure_ascii=False, indent=2)
print(f"Skrev JSON-rapport: {json_filename}")

cursor.close()
conn.close()
