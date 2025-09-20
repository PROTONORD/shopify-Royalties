#!/usr/bin/env python3
"""
STRUKTURERT SHOPIFY BACKUP SYSTEM
Lager en mappestruktur som gjenspeiler kategorier og produkter i Shopify.
Organiserer alt i logiske mapper før database-lagring.
"""
import os
import requests
import psycopg2
from psycopg2.extras import execute_batch, Json
from dotenv import load_dotenv
from datetime import datetime
import json
import time
import urllib.parse
from pathlib import Path
import re
import shutil

# Last inn miljøvariabler
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
SHOPIFY_API_KEY = os.getenv('SHOPIFY_API_KEY')
SHOPIFY_API_VERSION = '2023-10'
SHOPIFY_STORE_URL = os.getenv('SHOPIFY_STORE_URL')

POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')

SHOPIFY_BASE_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/{SHOPIFY_API_VERSION}"
SHOPIFY_HEADERS = {
    'Content-Type': 'application/json',
    'X-Shopify-Access-Token': SHOPIFY_API_KEY
}

# Opprett organisert mappestruktur
BACKUP_DATE = datetime.now().strftime('%Y-%m-%d')
BACKUP_BASE_DIR = os.path.join(os.path.dirname(__file__), 'shopify_organized_backup', BACKUP_DATE)

# Hovedmapper
STRUCTURE = {
    'collections': os.path.join(BACKUP_BASE_DIR, 'collections'),
    'products': os.path.join(BACKUP_BASE_DIR, 'products'),
    'customers': os.path.join(BACKUP_BASE_DIR, 'customers'),
    'orders': os.path.join(BACKUP_BASE_DIR, 'orders'),
    'shop_settings': os.path.join(BACKUP_BASE_DIR, 'shop_settings'),
    'themes': os.path.join(BACKUP_BASE_DIR, 'themes'),
    'media': os.path.join(BACKUP_BASE_DIR, 'media'),
    'reports': os.path.join(BACKUP_BASE_DIR, 'reports'),
    'metadata': os.path.join(BACKUP_BASE_DIR, '_metadata')
}

# Opprett alle mapper
for path in STRUCTURE.values():
    os.makedirs(path, exist_ok=True)

def safe_filename(name):
    """Lager sikre filnavn fra Shopify-titler"""
    if not name:
        return "untitled"
    # Fjern spesialtegn og erstatt med underscore
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', str(name))
    safe_name = re.sub(r'\s+', '_', safe_name)  # Erstatt mellomrom med underscore
    return safe_name[:100]  # Begrens lengde

def safe_request(url, params=None, max_retries=3):
    """Sikker API-forespørsel med retry og rate limiting"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=SHOPIFY_HEADERS, params=params)
            
            if response.status_code == 429:
                print("⏱️  Rate limit, venter 2 sekunder...")
                time.sleep(2)
                continue
            elif response.status_code == 200:
                return response
            else:
                print(f"⚠️  HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Feil ved API-kall (forsøk {attempt+1}): {e}")
            time.sleep(1)
    
    return None

def download_image(url, filepath):
    """Last ned bilde til spesifisert sti"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filepath
    except Exception as e:
        print(f"⚠️  Kunne ikke laste ned bilde {url}: {e}")
    return None

def get_db_connection():
    """Opprett database-tilkobling"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"❌ Database-tilkoblingsfeil: {e}")
        return None

def store_collections_to_db(collections_data):
    """Lagre collections til database"""
    if not collections_data:
        return
    
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        
        # Forbered data for batch insert
        collection_records = []
        for collection in collections_data:
            collection_records.append((
                collection['id'],
                collection.get('handle', ''),
                collection.get('title', ''),
                collection.get('updated_at'),
                collection.get('body_html', ''),
                collection.get('published_at'),
                collection.get('sort_order', ''),
                collection.get('template_suffix', ''),
                collection.get('published_scope', ''),
                collection.get('admin_graphql_api_id', ''),
                Json(collection)  # Hele objektet som JSON
            ))
        
        # Batch insert
        execute_batch(cursor, """
            INSERT INTO collections (id, handle, title, updated_at, body_html, published_at, sort_order, template_suffix, published_scope, admin_graphql_api_id, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET 
                handle = EXCLUDED.handle,
                title = EXCLUDED.title,
                updated_at = EXCLUDED.updated_at,
                body_html = EXCLUDED.body_html,
                published_at = EXCLUDED.published_at,
                sort_order = EXCLUDED.sort_order,
                template_suffix = EXCLUDED.template_suffix,
                published_scope = EXCLUDED.published_scope,
                admin_graphql_api_id = EXCLUDED.admin_graphql_api_id,
                raw_data = EXCLUDED.raw_data
        """, collection_records)
        
        conn.commit()
        print(f"✅ Lagret {len(collection_records)} collections til database")
        
    except Exception as e:
        print(f"❌ Feil ved lagring av collections: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def store_products_to_db(products_data):
    """Lagre produkter til database"""
    if not products_data:
        return
    
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        
        # Forbered data for batch insert
        product_records = []
        for product in products_data:
            product_records.append((
                product['id'],
                product.get('title', ''),
                product.get('handle', ''),
                product.get('product_type', ''),
                product.get('vendor', ''),
                product.get('status', 'active'),
                product.get('created_at'),
                product.get('updated_at'),
                product.get('published_at'),
                product.get('published_scope', ''),
                product.get('tags', ''),
                Json(product.get('options', [])),
                Json(product.get('images', [])),
                product.get('image', {}).get('id') if product.get('image') else None,
                Json(product.get('variants', [])),
                Json(product)  # Hele objektet som JSON
            ))
        
        # Batch insert
        execute_batch(cursor, """
            INSERT INTO products (id, title, handle, product_type, vendor, status, created_at, updated_at, published_at, published_scope, tags, options, images, image_id, variants, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET 
                title = EXCLUDED.title,
                handle = EXCLUDED.handle,
                product_type = EXCLUDED.product_type,
                vendor = EXCLUDED.vendor,
                status = EXCLUDED.status,
                updated_at = EXCLUDED.updated_at,
                published_at = EXCLUDED.published_at,
                published_scope = EXCLUDED.published_scope,
                tags = EXCLUDED.tags,
                options = EXCLUDED.options,
                images = EXCLUDED.images,
                image_id = EXCLUDED.image_id,
                variants = EXCLUDED.variants,
                raw_data = EXCLUDED.raw_data
        """, product_records)
        
        conn.commit()
        print(f"✅ Lagret {len(product_records)} produkter til database")
        
    except Exception as e:
        print(f"❌ Feil ved lagring av produkter: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def store_orders_to_db(orders_data):
    """Lagre ordrer til database"""
    if not orders_data:
        return
    
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        
        # Forbered data for batch insert
        order_records = []
        for order in orders_data:
            order_records.append((
                order['id'],
                order.get('order_number'),
                order.get('created_at'),
                order.get('updated_at'),
                order.get('processed_at'),
                order.get('closed_at'),
                order.get('financial_status'),
                order.get('fulfillment_status'),
                float(order.get('total_price', 0)) if order.get('total_price') else 0,
                float(order.get('subtotal_price', 0)) if order.get('subtotal_price') else 0,
                float(order.get('total_tax', 0)) if order.get('total_tax') else 0,
                order.get('currency', 'NOK'),
                order.get('email', ''),
                order.get('phone'),
                order.get('note'),
                Json(order)  # Hele objektet som JSON
            ))
        
        # Batch insert
        execute_batch(cursor, """
            INSERT INTO orders (id, order_number, created_at, updated_at, processed_at, closed_at, 
                               financial_status, fulfillment_status, total_price, subtotal_price, 
                               total_tax, currency, customer_email, phone, note, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET 
                updated_at = EXCLUDED.updated_at,
                processed_at = EXCLUDED.processed_at,
                closed_at = EXCLUDED.closed_at,
                financial_status = EXCLUDED.financial_status,
                fulfillment_status = EXCLUDED.fulfillment_status,
                total_price = EXCLUDED.total_price,
                subtotal_price = EXCLUDED.subtotal_price,
                total_tax = EXCLUDED.total_tax,
                currency = EXCLUDED.currency,
                customer_email = EXCLUDED.customer_email,
                phone = EXCLUDED.phone,
                note = EXCLUDED.note,
                raw_data = EXCLUDED.raw_data
        """, order_records)
        
        conn.commit()
        print(f"✅ Lagret {len(order_records)} ordrer til database")
        
    except Exception as e:
        print(f"❌ Feil ved lagring av ordrer: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def fetch_and_organize_collections():
    """Hent og organiser alle collections i mappestruktur"""
    print("\n📁 === ORGANISERER COLLECTIONS ===")
    
    collections_data = {}
    
    # Custom collections
    print("🔄 Henter custom collections...")
    response = safe_request(f"{SHOPIFY_BASE_URL}/custom_collections.json?limit=250")
    if response:
        custom_collections = response.json().get('custom_collections', [])
        collections_data['custom'] = custom_collections
        
        for collection in custom_collections:
            collection_name = safe_filename(collection.get('title', 'unknown'))
            collection_dir = os.path.join(STRUCTURE['collections'], 'custom', collection_name)
            os.makedirs(collection_dir, exist_ok=True)
            
            # Lagre collection info
            with open(os.path.join(collection_dir, 'collection_info.json'), 'w', encoding='utf-8') as f:
                json.dump(collection, f, indent=2, default=str)
            
            # Last ned collection-bilde hvis det finnes
            if collection.get('image') and collection['image'].get('src'):
                img_url = collection['image']['src']
                img_ext = img_url.split('.')[-1].split('?')[0] or 'jpg'
                img_path = os.path.join(collection_dir, f'collection_image.{img_ext}')
                download_image(img_url, img_path)
            
            print(f"   📁 Lagret: {collection_name}")
    
    # Smart collections
    print("🔄 Henter smart collections...")
    response = safe_request(f"{SHOPIFY_BASE_URL}/smart_collections.json?limit=250")
    if response:
        smart_collections = response.json().get('smart_collections', [])
        collections_data['smart'] = smart_collections
        
        for collection in smart_collections:
            collection_name = safe_filename(collection.get('title', 'unknown'))
            collection_dir = os.path.join(STRUCTURE['collections'], 'smart', collection_name)
            os.makedirs(collection_dir, exist_ok=True)
            
            # Lagre collection info
            with open(os.path.join(collection_dir, 'collection_info.json'), 'w', encoding='utf-8') as f:
                json.dump(collection, f, indent=2, default=str)
            
            # Last ned collection-bilde hvis det finnes
            if collection.get('image') and collection['image'].get('src'):
                img_url = collection['image']['src']
                img_ext = img_url.split('.')[-1].split('?')[0] or 'jpg'
                img_path = os.path.join(collection_dir, f'collection_image.{img_ext}')
                download_image(img_url, img_path)
            
            print(f"   📁 Lagret: {collection_name}")
    
    # Lagre oversikt
    with open(os.path.join(STRUCTURE['collections'], '_collections_overview.json'), 'w', encoding='utf-8') as f:
        json.dump(collections_data, f, indent=2, default=str)
    
    # Lagre til database
    all_collections = collections_data.get('custom', []) + collections_data.get('smart', [])
    if all_collections:
        store_collections_to_db(all_collections)
    
    print(f"✅ Organisert {len(collections_data.get('custom', []))} custom + {len(collections_data.get('smart', []))} smart collections")
    return collections_data

def fetch_and_organize_products(collections_data):
    """Hent og organiser alle produkter etter kategorier"""
    print("\n🏷️  === ORGANISERER PRODUKTER ===")
    
    # Opprett mapper for forskjellige kategoriseringer
    product_dirs = {
        'by_vendor': os.path.join(STRUCTURE['products'], 'by_vendor'),
        'by_type': os.path.join(STRUCTURE['products'], 'by_type'),
        'by_collection': os.path.join(STRUCTURE['products'], 'by_collection'),
        'all_products': os.path.join(STRUCTURE['products'], 'all_products'),
        'uncategorized': os.path.join(STRUCTURE['products'], 'uncategorized')
    }
    
    for dir_path in product_dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    # Bygg collection-map for rask oppslag
    collection_map = {}
    for collection in collections_data.get('custom', []):
        collection_map[collection['id']] = safe_filename(collection.get('title', 'unknown'))
    for collection in collections_data.get('smart', []):
        collection_map[collection['id']] = safe_filename(collection.get('title', 'unknown'))
    
    print("🔄 Henter alle produkter...")
    all_products = []
    page_count = 0
    next_page_info = None
    
    while page_count < 100:  # Sikkerhetsbremse
        page_count += 1
        
        if next_page_info:
            url = f"{SHOPIFY_BASE_URL}/products.json?limit=50&page_info={next_page_info}"
        else:
            url = f"{SHOPIFY_BASE_URL}/products.json?limit=50"
        
        response = safe_request(url)
        if not response:
            break
            
        data = response.json()
        products = data.get('products', [])
        
        if not products:
            break
            
        all_products.extend(products)
        print(f"   Side {page_count}: hentet {len(products)} produkter, totalt {len(all_products)}")
        
        # Sjekk for neste side
        link_header = response.headers.get('Link')
        next_page_info = None
        
        if link_header and 'rel="next"' in link_header:
            for link in link_header.split(','):
                if 'rel="next"' in link:
                    url_part = link.split(';')[0].strip('<> ')
                    parsed = urllib.parse.urlparse(url_part)
                    query = urllib.parse.parse_qs(parsed.query)
                    if "page_info" in query:
                        next_page_info = query["page_info"][0]
                    break
        
        if not next_page_info:
            break
            
        time.sleep(0.5)
    
    print(f"🔄 Organiserer {len(all_products)} produkter...")
    
    # Organiser hvert produkt
    for i, product in enumerate(all_products):
        if i % 50 == 0:
            print(f"   Organisert {i}/{len(all_products)} produkter...")
        
        product_id = product['id']
        product_title = safe_filename(product.get('title', 'untitled'))
        vendor = safe_filename(product.get('vendor', 'no_vendor'))
        product_type = safe_filename(product.get('product_type', 'no_type'))
        
        # 1. Lagre i "alle produkter"
        product_main_dir = os.path.join(product_dirs['all_products'], f"{product_id}_{product_title}")
        os.makedirs(product_main_dir, exist_ok=True)
        
        # Lagre produktinfo
        with open(os.path.join(product_main_dir, 'product_info.json'), 'w', encoding='utf-8') as f:
            json.dump(product, f, indent=2, default=str)
        
        # Last ned produktbilder
        images_dir = os.path.join(product_main_dir, 'images')
        if product.get('images'):
            os.makedirs(images_dir, exist_ok=True)
            for j, image in enumerate(product['images']):
                if image.get('src'):
                    img_url = image['src']
                    img_ext = img_url.split('.')[-1].split('?')[0] or 'jpg'
                    img_path = os.path.join(images_dir, f'image_{j+1}.{img_ext}')
                    download_image(img_url, img_path)
        
        # 2. Organiser etter vendor
        vendor_dir = os.path.join(product_dirs['by_vendor'], vendor)
        os.makedirs(vendor_dir, exist_ok=True)
        vendor_product_link = os.path.join(vendor_dir, f"{product_id}_{product_title}.json")
        with open(vendor_product_link, 'w', encoding='utf-8') as f:
            json.dump({
                "product_id": product_id,
                "title": product['title'],
                "main_directory": product_main_dir,
                "summary": {
                    "vendor": product.get('vendor'),
                    "type": product.get('product_type'),
                    "status": product.get('status'),
                    "variants_count": len(product.get('variants', [])),
                    "images_count": len(product.get('images', []))
                }
            }, f, indent=2)
        
        # 3. Organiser etter type
        if product_type != 'no_type':
            type_dir = os.path.join(product_dirs['by_type'], product_type)
            os.makedirs(type_dir, exist_ok=True)
            type_product_link = os.path.join(type_dir, f"{product_id}_{product_title}.json")
            with open(type_product_link, 'w', encoding='utf-8') as f:
                json.dump({
                    "product_id": product_id,
                    "title": product['title'],
                    "main_directory": product_main_dir
                }, f, indent=2)
        
        # 4. Organiser etter collections (må hente collection-medlemskap)
        # Dette krever ekstra API-kall, så vi gjør det for utvalgte produkter
        if i < 100:  # Kun for første 100 produkter for å ikke overbelaste API
            try:
                coll_response = safe_request(f"{SHOPIFY_BASE_URL}/products/{product_id}/collections.json")
                if coll_response:
                    product_collections = coll_response.json().get('collections', [])
                    for collection in product_collections:
                        coll_name = collection_map.get(collection['id'], f"collection_{collection['id']}")
                        coll_dir = os.path.join(product_dirs['by_collection'], coll_name)
                        os.makedirs(coll_dir, exist_ok=True)
                        coll_product_link = os.path.join(coll_dir, f"{product_id}_{product_title}.json")
                        with open(coll_product_link, 'w', encoding='utf-8') as f:
                            json.dump({
                                "product_id": product_id,
                                "title": product['title'],
                                "main_directory": product_main_dir,
                                "collection_info": collection
                            }, f, indent=2)
                time.sleep(0.2)  # Rate limiting for collection-kall
            except:
                pass  # Ignorer feil ved collection-oppslag
    
    # Lagre produktoversikt
    product_summary = {
        "total_products": len(all_products),
        "by_vendor": {},
        "by_type": {},
        "backup_date": BACKUP_DATE
    }
    
    # Tell produkter per vendor og type
    for product in all_products:
        vendor = product.get('vendor', 'Unknown')
        product_type = product.get('product_type', 'Unknown')
        
        product_summary["by_vendor"][vendor] = product_summary["by_vendor"].get(vendor, 0) + 1
        product_summary["by_type"][product_type] = product_summary["by_type"].get(product_type, 0) + 1
    
    with open(os.path.join(STRUCTURE['products'], '_products_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(product_summary, f, indent=2)
    
    # Lagre produkter til database
    if all_products:
        store_products_to_db(all_products)
    
    print(f"✅ Organisert {len(all_products)} produkter:")
    print(f"   📁 Vendors: {len(product_summary['by_vendor'])}")
    print(f"   📁 Typer: {len(product_summary['by_type'])}")
    
    return all_products

def fetch_and_organize_orders():
    """Hent og organiser ordrer etter dato og status"""
    print("\n🛒 === ORGANISERER ORDRER ===")
    
    # Opprett mapper for ordrer
    order_dirs = {
        'by_year': os.path.join(STRUCTURE['orders'], 'by_year'),
        'by_status': os.path.join(STRUCTURE['orders'], 'by_status'),
        'recent': os.path.join(STRUCTURE['orders'], 'recent'),
        'all_orders': os.path.join(STRUCTURE['orders'], 'all_orders')
    }
    
    for dir_path in order_dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    print("🔄 Henter ordrer (de første 500)...")
    response = safe_request(f"{SHOPIFY_BASE_URL}/orders.json?status=any&limit=250")
    if not response:
        return []
    
    orders = response.json().get('orders', [])
    
    # Organiser ordrer
    for order in orders:
        order_id = order['id']
        order_number = order.get('order_number', order_id)
        created_at = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
        year = created_at.year
        month = created_at.month
        status = order.get('financial_status', 'unknown')
        
        # Lagre i alle ordrer
        order_file = os.path.join(order_dirs['all_orders'], f"order_{order_number}_{order_id}.json")
        with open(order_file, 'w', encoding='utf-8') as f:
            json.dump(order, f, indent=2, default=str)
        
        # Organiser etter år og måned
        year_dir = os.path.join(order_dirs['by_year'], str(year), f"{month:02d}")
        os.makedirs(year_dir, exist_ok=True)
        year_order_link = os.path.join(year_dir, f"order_{order_number}.json")
        with open(year_order_link, 'w', encoding='utf-8') as f:
            json.dump({
                "order_id": order_id,
                "order_number": order_number,
                "created_at": order['created_at'],
                "total_price": order.get('total_price'),
                "financial_status": status,
                "full_order_file": order_file
            }, f, indent=2)
        
        # Organiser etter status
        status_dir = os.path.join(order_dirs['by_status'], status)
        os.makedirs(status_dir, exist_ok=True)
        status_order_link = os.path.join(status_dir, f"order_{order_number}.json")
        with open(status_order_link, 'w', encoding='utf-8') as f:
            json.dump({
                "order_id": order_id,
                "order_number": order_number,
                "created_at": order['created_at'],
                "total_price": order.get('total_price'),
                "full_order_file": order_file
            }, f, indent=2)
    
    print(f"✅ Organisert {len(orders)} ordrer")
    
    # Lagre ordrer til database
    if orders:
        store_orders_to_db(orders)
    
    return orders

def fetch_shop_settings():
    """Hent og organiser butikkinnstillinger"""
    print("\n🏪 === ORGANISERER BUTIKKINNSTILLINGER ===")
    
    settings_data = {}
    
    # Shop info
    response = safe_request(f"{SHOPIFY_BASE_URL}/shop.json")
    if response:
        shop_info = response.json().get('shop', {})
        settings_data['shop_info'] = shop_info
        
        with open(os.path.join(STRUCTURE['shop_settings'], 'shop_info.json'), 'w', encoding='utf-8') as f:
            json.dump(shop_info, f, indent=2, default=str)
        
        # Last ned logo hvis det finnes
        if shop_info.get('logo'):
            download_image(shop_info['logo'], os.path.join(STRUCTURE['media'], 'shop_logo.png'))
    
    # Policies
    response = safe_request(f"{SHOPIFY_BASE_URL}/policies.json")
    if response:
        policies = response.json().get('policies', [])
        settings_data['policies'] = policies
        
        with open(os.path.join(STRUCTURE['shop_settings'], 'policies.json'), 'w', encoding='utf-8') as f:
            json.dump(policies, f, indent=2, default=str)
    
    # Shipping zones
    response = safe_request(f"{SHOPIFY_BASE_URL}/shipping_zones.json")
    if response:
        shipping_zones = response.json().get('shipping_zones', [])
        settings_data['shipping_zones'] = shipping_zones
        
        with open(os.path.join(STRUCTURE['shop_settings'], 'shipping_zones.json'), 'w', encoding='utf-8') as f:
            json.dump(shipping_zones, f, indent=2, default=str)
    
    # Locations
    response = safe_request(f"{SHOPIFY_BASE_URL}/locations.json")
    if response:
        locations = response.json().get('locations', [])
        settings_data['locations'] = locations
        
        with open(os.path.join(STRUCTURE['shop_settings'], 'locations.json'), 'w', encoding='utf-8') as f:
            json.dump(locations, f, indent=2, default=str)
    
    print("✅ Butikkinnstillinger organisert")
    return settings_data

def generate_backup_report():
    """Generer oversiktsrapport for backupen"""
    print("\n📊 === GENERERER BACKUP-RAPPORT ===")
    
    report = {
        "backup_info": {
            "date": BACKUP_DATE,
            "timestamp": datetime.now().isoformat(),
            "backup_directory": BACKUP_BASE_DIR
        },
        "structure": {},
        "file_counts": {},
        "total_size_mb": 0
    }
    
    # Tell filer og mapper i hver hovedkategori
    for category, path in STRUCTURE.items():
        if os.path.exists(path):
            file_count = 0
            folder_count = 0
            total_size = 0
            
            for root, dirs, files in os.walk(path):
                folder_count += len(dirs)
                file_count += len(files)
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        pass
            
            report["structure"][category] = {
                "path": path,
                "files": file_count,
                "folders": folder_count,
                "size_mb": round(total_size / (1024*1024), 2)
            }
            
            report["total_size_mb"] += report["structure"][category]["size_mb"]
    
    # Lagre rapport
    report_file = os.path.join(STRUCTURE['metadata'], 'backup_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    # Skriv ut rapport
    print(f"📊 BACKUP-RAPPORT ({BACKUP_DATE}):")
    print("=" * 50)
    for category, data in report["structure"].items():
        print(f"{category:15}: {data['files']:4} filer, {data['folders']:3} mapper, {data['size_mb']:6.1f} MB")
    print(f"{'TOTALT':15}: {report['total_size_mb']:.1f} MB")
    print(f"Rapport lagret: {report_file}")
    
    return report

def main():
    """Hovedfunksjon - kjør strukturert backup"""
    start_time = datetime.now()
    print(f"🚀 STARTER STRUKTURERT SHOPIFY BACKUP - {start_time}")
    print(f"📁 Backup-mappe: {BACKUP_BASE_DIR}")
    print("=" * 80)
    
    try:
        # Hent og organiser alt
        collections = fetch_and_organize_collections()
        products = fetch_and_organize_products(collections)
        orders = fetch_and_organize_orders()
        settings = fetch_shop_settings()
        
        # Generer rapport
        report = generate_backup_report()
        
        # Lag symbolsk lenke til siste backup
        latest_link = os.path.join(os.path.dirname(BACKUP_BASE_DIR), 'latest')
        if os.path.exists(latest_link):
            os.unlink(latest_link)
        os.symlink(BACKUP_BASE_DIR, latest_link)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("=" * 80)
        print(f"🎉 STRUKTURERT BACKUP FULLFØRT!")
        print(f"⏱️  Varighet: {duration}")
        print(f"📁 Lokasjon: {BACKUP_BASE_DIR}")
        print(f"🔗 Latest: {latest_link}")
        print(f"💾 Total størrelse: {report['total_size_mb']:.1f} MB")
        
    except Exception as e:
        print(f"❌ KRITISK FEIL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()