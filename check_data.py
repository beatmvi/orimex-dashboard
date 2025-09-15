#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для быстрой проверки данных в базе
"""

import sqlite3
import pandas as pd
from datetime import datetime

def check_database():
    """Быстрая проверка содержимого базы данных"""
    
    try:
        conn = sqlite3.connect('orimex_orders.db')
        
        print("🔍 ПРОВЕРКА БАЗЫ ДАННЫХ ОРИМЭКС")
        print("=" * 50)
        
        # Общая статистика
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM contractors')
        contractors_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM products')
        products_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM orders')
        orders_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(amount), AVG(amount), MIN(amount), MAX(amount) FROM orders WHERE amount IS NOT NULL')
        amount_stats = cursor.fetchone()
        
        cursor.execute('SELECT MIN(order_date), MAX(order_date) FROM orders')
        date_range = cursor.fetchone()
        
        print(f"📊 Контрагентов: {contractors_count:,}")
        print(f"📦 Продуктов: {products_count:,}")
        print(f"🛒 Заказов: {orders_count:,}")
        print(f"💰 Общая сумма: {amount_stats[0]:,.2f} руб." if amount_stats[0] else "Нет данных о суммах")
        print(f"📈 Средний заказ: {amount_stats[1]:,.2f} руб." if amount_stats[1] else "Нет данных")
        print(f"📉 Мин. заказ: {amount_stats[2]:,.2f} руб." if amount_stats[2] else "Нет данных")
        print(f"📈 Макс. заказ: {amount_stats[3]:,.2f} руб." if amount_stats[3] else "Нет данных")
        print(f"📅 Период: {date_range[0]} - {date_range[1]}" if date_range[0] else "Нет данных о датах")
        
        print("\n🏢 ТОП-5 КОНТРАГЕНТОВ ПО СУММЕ:")
        print("-" * 40)
        top_contractors = pd.read_sql_query('''
        SELECT c.head_contractor, c.buyer, SUM(o.amount) as total_amount, COUNT(o.id) as order_count
        FROM orders o
        JOIN contractors c ON o.contractor_id = c.id
        WHERE o.amount IS NOT NULL
        GROUP BY c.head_contractor, c.buyer
        ORDER BY total_amount DESC
        LIMIT 5
        ''', conn)
        
        for idx, row in top_contractors.iterrows():
            print(f"{idx+1}. {row['buyer']} - {row['total_amount']:,.0f} руб. ({row['order_count']} заказов)")
        
        print("\n📦 ТОП-5 ТОВАРОВ ПО СУММЕ:")
        print("-" * 40)
        top_products = pd.read_sql_query('''
        SELECT p.name, p.category, SUM(o.amount) as total_amount, COUNT(o.id) as order_count
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.amount IS NOT NULL
        GROUP BY p.name, p.category
        ORDER BY total_amount DESC
        LIMIT 5
        ''', conn)
        
        for idx, row in top_products.iterrows():
            print(f"{idx+1}. {row['name']} ({row['category']}) - {row['total_amount']:,.0f} руб. ({row['order_count']} заказов)")
        
        print("\n🗺️ СТАТИСТИКА ПО РЕГИОНАМ:")
        print("-" * 40)
        regions = pd.read_sql_query('''
        SELECT c.region, SUM(o.amount) as total_amount, COUNT(o.id) as order_count
        FROM orders o
        JOIN contractors c ON o.contractor_id = c.id
        WHERE o.amount IS NOT NULL
        GROUP BY c.region
        ORDER BY total_amount DESC
        ''', conn)
        
        for idx, row in regions.iterrows():
            print(f"{row['region']}: {row['total_amount']:,.0f} руб. ({row['order_count']} заказов)")
        
        print("\n📈 ДИНАМИКА ПО МЕСЯЦАМ:")
        print("-" * 40)
        monthly = pd.read_sql_query('''
        SELECT 
            strftime('%Y-%m', order_date) as month,
            SUM(amount) as total_amount,
            COUNT(id) as order_count
        FROM orders 
        WHERE amount IS NOT NULL
        GROUP BY strftime('%Y-%m', order_date)
        ORDER BY month
        ''', conn)
        
        for idx, row in monthly.iterrows():
            print(f"{row['month']}: {row['total_amount']:,.0f} руб. ({row['order_count']} заказов)")
        
        conn.close()
        
        print("\n✅ Проверка завершена!")
        print("🌐 Дашборд доступен по адресу: http://localhost:8501")
        
    except Exception as e:
        print(f"❌ Ошибка при проверке базы данных: {e}")

if __name__ == "__main__":
    check_database()
