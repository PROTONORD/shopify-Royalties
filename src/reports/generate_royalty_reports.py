#!/usr/bin/env python3
"""
Genererer royalty-rapporter fra Shopify-data lagret i PostgreSQL.
Rapportene matches med layoutet fra royalty_report_2025-09.pdf
"""
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

REPORT_DIR = os.path.join(os.path.dirname(__file__), 'royalty_rapporter')
os.makedirs(REPORT_DIR, exist_ok=True)

MONTHS = [
    '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'
]

class RoyaltyPDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self.title, ln=True, align='C')
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Side {self.page_no()}', align='C')

    def add_royalty_table(self, month, rows, totals):
        # Header tabellen som i PDF
        self.set_font('Arial', 'B', 8)
        headers = ['OrdreID', 'Kjøpsdato', 'Pris eks mva', 'Frakt eks', 'Royalty %', 'Royalty', 'Fradrag30', 'Total eks', 'Kjøper', 'Produktnavn', 'e-post']
        widths = [18, 22, 18, 16, 14, 16, 16, 16, 25, 35, 30]
        
        for i, header in enumerate(headers):
            self.cell(widths[i], 8, header, 1, 0, 'C')
        self.ln()
        
        # Data rader
        self.set_font('Arial', '', 7)
        for row in rows:
            self.cell(widths[0], 6, str(row['order_id']), 1)
            self.cell(widths[1], 6, row['kjopsdato'], 1)
            self.cell(widths[2], 6, f"{row['pris_eks_mva']:.2f}", 1)
            self.cell(widths[3], 6, f"{row['frakt_eks']:.2f}", 1)
            self.cell(widths[4], 6, f"{row['royalty_pct']:.0f}", 1)
            self.cell(widths[5], 6, f"{row['royalty']:.2f}", 1)
            self.cell(widths[6], 6, f"{row['fradrag30']:.2f}", 1)
            self.cell(widths[7], 6, f"{row['total_eks']:.2f}", 1)
            self.cell(widths[8], 6, row['kjoper'][:23], 1)
            self.cell(widths[9], 6, row['produktnavn'][:33], 1)
            self.cell(widths[10], 6, row['epost'][:28], 1)
            self.ln()
        
        # Summer nederst som i PDF
        self.ln(2)
        self.set_font('Arial', 'B', 9)
        self.cell(widths[0] + widths[1], 8, f"SUM Frakt eks mva: {totals['sum_frakt_eks']:.2f}", 0)
        self.cell(widths[2] + widths[3] + widths[4], 8, f"SUM Royalty: {totals['sum_royalty']:.2f}", 0)
        self.cell(widths[5] + widths[6], 8, f"SUM Fradrag30: {totals['sum_fradrag30']:.2f}", 0)
        self.ln()

def fetch_royalty_data(conn, year):
    """Henter royalty-data fra database med alle nødvendige felter"""
    royalty_data = {m: [] for m in MONTHS}
    
    with conn.cursor() as cur:
        for month in MONTHS:
            query = '''
                SELECT 
                    o.id as order_id,
                    o.created_at::date as kjopsdato,
                    li.price as pris_eks_mva,
                    COALESCE(o.total_shipping_price, 0) as frakt_eks,
                    20 as royalty_pct,
                    ROUND(li.price * 0.20, 2) as royalty,
                    ROUND(li.price * 0.30, 2) as fradrag30,
                    ROUND(li.price - (li.price * 0.30), 2) as total_eks,
                    COALESCE(o.customer_email, 'Ukjent kunde') as kjoper,
                    li.title as produktnavn,
                    COALESCE(o.customer_email, '') as epost
                FROM line_items li
                JOIN orders o ON li.order_id = o.id
                WHERE EXTRACT(YEAR FROM o.created_at) = %s 
                  AND EXTRACT(MONTH FROM o.created_at) = %s
                ORDER BY o.created_at ASC
            '''
            cur.execute(query, (year, int(month)))
            
            for row in cur.fetchall():
                royalty_data[month].append({
                    'order_id': row[0],
                    'kjopsdato': row[1].strftime('%Y-%m-%d'),
                    'pris_eks_mva': float(row[2]),
                    'frakt_eks': float(row[3]),
                    'royalty_pct': row[4],
                    'royalty': float(row[5]),
                    'fradrag30': float(row[6]),
                    'total_eks': float(row[7]),
                    'kjoper': str(row[8]),
                    'produktnavn': str(row[9]),
                    'epost': str(row[10])
                })
    
    return royalty_data

def calculate_totals(rows):
    """Beregner summer for rapport"""
    return {
        'sum_frakt_eks': sum(row['frakt_eks'] for row in rows),
        'sum_royalty': sum(row['royalty'] for row in rows),
        'sum_fradrag30': sum(row['fradrag30'] for row in rows)
    }

def save_royalty_json_report(royalty_data, year):
    """Lagrer JSON-rapporter"""
    for month, rows in royalty_data.items():
        if rows:  # Kun hvis det er data
            totals = calculate_totals(rows)
            report_data = {
                'year': year,
                'month': month,
                'data': rows,
                'totals': totals
            }
            filename = os.path.join(REPORT_DIR, f'royalty_report_{year}-{month}.json')
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

def save_royalty_pdf_report(royalty_data, year):
    """Lagrer PDF-rapporter som matcher vedlagt layout"""
    for month, rows in royalty_data.items():
        if rows:  # Kun hvis det er data
            totals = calculate_totals(rows)
            pdf = RoyaltyPDFReport()
            company_name = os.getenv('COMPANY_NAME', 'Your Company')
            pdf.title = f'Royaltyrapport for {year}-{month} ({company_name})'
            pdf.add_page('L')  # Landscape for bedre plass
            pdf.add_royalty_table(month, rows, totals)
            filename = os.path.join(REPORT_DIR, f'royalty_report_{year}-{month}.pdf')
            pdf.output(filename)

def upload_to_cloud_storage(year):
    """Laster opp rapporter til konfigurerbar cloud storage"""
    cloud_path = os.getenv('CLOUD_STORAGE_PATH', 'your-cloud-path/reports/')
    for month in MONTHS:
        json_file = os.path.join(REPORT_DIR, f'royalty_report_{year}-{month}.json')
        pdf_file = os.path.join(REPORT_DIR, f'royalty_report_{year}-{month}.pdf')
        
        if os.path.exists(json_file):
            os.system(f"rclone copy '{json_file}' '{cloud_path}'")
        if os.path.exists(pdf_file):
            os.system(f"rclone copy '{pdf_file}' '{cloud_path}'")

def main():
    # Først synkroniser data fra Shopify
    print("Synkroniserer data fra Shopify...")
    os.system("python3 shopify_to_postgres.py")
    
    year = 2025
    print(f"Genererer royalty-rapporter for {year}...")
    
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    
    royalty_data = fetch_royalty_data(conn, year)
    save_royalty_json_report(royalty_data, year)
    save_royalty_pdf_report(royalty_data, year)
    conn.close()
    
    print(f"Royalty-rapporter generert for {year} i mappen 'royalty_rapporter'.")
    
    # Last opp til cloud storage
    print("Laster opp rapporter til cloud storage...")
    upload_to_cloud_storage(year)
    print(f"Royalty-rapporter for {year} er lastet opp til Jottacloud under 'protonord_shopify/rapport'.")

if __name__ == "__main__":
    main()