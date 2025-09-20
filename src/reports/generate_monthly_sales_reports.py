import os
import psycopg2
import json
from fpdf import FPDF
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'shopify')
DB_USER = os.getenv('POSTGRES_USER', 'shopifyuser')
DB_PASS = os.getenv('POSTGRES_PASSWORD', '')

REPORT_DIR = os.path.join(os.path.dirname(__file__), 'rapporter')
os.makedirs(REPORT_DIR, exist_ok=True)

MONTHS = [
    '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'
]

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, self.title, ln=True, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Side {self.page_no()}', align='C')

    def add_month_table(self, month, rows):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'Måned: {month}', ln=True)
        self.set_font('Arial', '', 10)
        self.cell(40, 8, 'OrdreID', 1)
        self.cell(40, 8, 'Vendor', 1)
        self.cell(40, 8, 'Produkt', 1)
        self.cell(30, 8, 'Pris', 1)
        self.cell(20, 8, 'Antall', 1)
        self.ln()
        for row in rows:
            self.cell(40, 8, str(row['order_id']), 1)
            self.cell(40, 8, row['vendor'], 1)
            self.cell(40, 8, row['title'][:18], 1)
            self.cell(30, 8, f"{row['price']:.2f}", 1)
            self.cell(20, 8, str(row['quantity']), 1)
            self.ln()
        self.ln(5)

def fetch_monthly_sales(conn, year):
    sales = {m: [] for m in MONTHS}
    with conn.cursor() as cur:
        for month in MONTHS:
            cur.execute('''
                SELECT li.order_id, li.vendor, li.title, li.price, li.quantity, o.created_at
                FROM line_items li
                JOIN orders o ON li.order_id = o.id
                WHERE EXTRACT(YEAR FROM o.created_at) = %s AND EXTRACT(MONTH FROM o.created_at) = %s
                ORDER BY o.created_at ASC
            ''', (year, int(month)))
            for row in cur.fetchall():
                sales[month].append({
                    'order_id': row[0],
                    'vendor': row[1] or '',
                    'title': row[2] or '',
                    'price': float(row[3]),
                    'quantity': int(row[4]),
                    'created_at': row[5].strftime('%Y-%m-%d')
                })
    return sales

def save_json_report(sales, year):
    for month, rows in sales.items():
        filename = os.path.join(REPORT_DIR, f'sales_report_{year}-{month}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

def save_pdf_report(sales, year):
    for month, rows in sales.items():
        pdf = PDFReport()
        pdf.title = f'Salgsrapport {year}-{month}'
        pdf.add_page()
        pdf.add_month_table(month, rows)
        filename = os.path.join(REPORT_DIR, f'sales_report_{year}-{month}.pdf')
        pdf.output(filename)

def main():
    year = 2025
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    sales = fetch_monthly_sales(conn, year)
    save_json_report(sales, year)
    save_pdf_report(sales, year)
    conn.close()
    print(f"Rapporter generert for {year} i mappen 'rapporter'.")

    # Last opp rapporter til konfigurerbar cloud storage
    cloud_path = os.getenv('CLOUD_STORAGE_PATH', 'your-cloud-path/reports/')
    for month in MONTHS:
        json_file = os.path.join(REPORT_DIR, f'sales_report_{year}-{month}.json')
        pdf_file = os.path.join(REPORT_DIR, f'sales_report_{year}-{month}.pdf')
        os.system(f"rclone copy '{json_file}' '{cloud_path}'")
        os.system(f"rclone copy '{pdf_file}' '{cloud_path}'")
    print(f"Rapporter for {year} er lastet opp til cloud storage under '{cloud_path}'.")

if __name__ == "__main__":
    main()
