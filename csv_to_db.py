#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для конвертации CSV файла с заказами Оримэкс в SQLite базу данных
"""

import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime
import re
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_numeric_value(value, debug=False):
    """Очистка числовых значений от пробелов и кавычек"""
    if pd.isna(value) or value == '' or value is None:
        return None
    
    original_value = value
    
    # Преобразуем в строку если это не строка
    if not isinstance(value, str):
        value = str(value)
    
    # Проверяем на NaN
    if value.lower() == 'nan':
        return None
        
    # Удаляем кавычки и пробелы в начале/конце
    cleaned = value.replace('"', '').strip()
    
    # Если пустая строка после очистки
    if not cleaned:
        return None
    
    # Удаляем все пробелы (включая неразрывные пробелы)
    cleaned = cleaned.replace(' ', '').replace('\u00A0', '').replace('\u2009', '')
    
    # Обрабатываем запятые
    if ',' in cleaned:
        # Проверяем, есть ли после последней запятой 1-2 цифры (десятичная дробь)
        parts = cleaned.split(',')
        if len(parts) >= 2 and len(parts[-1]) <= 2 and parts[-1].isdigit():
            # Последняя запятая - десятичный разделитель
            # Все предыдущие запятые - разделители тысяч
            decimal_part = parts[-1]
            integer_part = ''.join(parts[:-1])
            cleaned = integer_part + '.' + decimal_part
        else:
            # Все запятые - разделители тысяч
            cleaned = cleaned.replace(',', '')
    
    try:
        result = float(cleaned)
        if debug:  # Отладка для первых записей
            logger.info(f"Успешно преобразовано: '{original_value}' -> '{cleaned}' -> {result}")
        return result
    except ValueError:
        logger.warning(f"Не удалось преобразовать в число: '{original_value}' -> '{cleaned}'")
        return None

def parse_csv_to_database(csv_file_path, db_path='orimex_orders.db'):
    """
    Парсинг CSV файла и создание нормализованной базы данных
    """
    logger.info(f"Начинаем обработку файла: {csv_file_path}")
    
    # Вычисляем хеш файла для предотвращения дублирования
    import hashlib
    with open(csv_file_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    logger.info(f"Хеш файла: {file_hash}")
    
    # Читаем CSV файл
    try:
        # Читаем первые несколько строк для понимания структуры
        df_header = pd.read_csv(csv_file_path, nrows=2, encoding='utf-8')
        logger.info(f"Заголовки файла: {df_header.columns.tolist()}")
        
        # Проверяем, есть ли даты в заголовках
        has_dates = any('2025' in str(col) for col in df_header.columns)
        logger.info(f"Найдены даты в заголовках: {has_dates}")
        
        if has_dates:
            # Если есть даты в заголовках, пропускаем первые 2 строки
            df = pd.read_csv(csv_file_path, skiprows=2, encoding='utf-8', low_memory=False)
        else:
            # Если дат нет, читаем весь файл
            df = pd.read_csv(csv_file_path, encoding='utf-8', low_memory=False)
            
        logger.info(f"Загружено строк данных: {len(df)}")
        
        # Если загружено мало строк, попробуем другой подход
        if len(df) < 1000:
            logger.warning(f"Загружено мало строк ({len(df)}), пробуем другой подход...")
            # Пробуем читать без пропуска строк
            df_alt = pd.read_csv(csv_file_path, encoding='utf-8', low_memory=False)
            logger.info(f"Альтернативное чтение: {len(df_alt)} строк")
            
            # Если альтернативное чтение дало больше строк, используем его
            if len(df_alt) > len(df):
                df = df_alt
                logger.info("Используем альтернативное чтение")
        
    except Exception as e:
        logger.error(f"Ошибка при чтении CSV файла: {e}")
        return False
    
    # Создаем соединение с базой данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Создаем таблицы
        create_tables(cursor)
        
        # Проверяем, не был ли уже обработан этот файл
        cursor.execute("SELECT COUNT(*) FROM orders WHERE file_hash = ?", (file_hash,))
        existing_records = cursor.fetchone()[0]
        if existing_records > 0:
            logger.warning(f"Файл с хешем {file_hash} уже был обработан ранее! Пропускаем загрузку.")
            conn.close()
            return True
        
        # Получаем названия колонок из первых двух строк исходного файла
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip().split(',')
            second_line = f.readline().strip().split(',')
        
        # Определяем колонки с датами (начиная с 11-й колонки)
        # Структура: Дата, пустая колонка, следующая дата, пустая колонка...
        # Под каждой датой в строке 2: "Количество заказов", "Сумма заказов"
        # Исключаем последние 2 колонки (Итого)
        date_columns = []
        for i in range(10, len(first_line)-3, 2):  # Исключаем последние 3 колонки (Итого + 2 колонки данных)
            if i < len(first_line):
                date_str = first_line[i].strip()
                if re.match(r'\d{2}\.\d{2}\.\d{4}', date_str):
                    date_columns.append((i, date_str))
        
        logger.info(f"Найдено дат: {len(date_columns)}")
        
        # Обрабатываем каждую строку данных
        process_data_rows(df, cursor, date_columns, file_hash)
        
        # Сохраняем изменения
        conn.commit()
        logger.info("База данных успешно создана!")
        
        # Показываем статистику
        show_database_stats(cursor)
        
    except Exception as e:
        logger.error(f"Ошибка при создании базы данных: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

def create_tables(cursor):
    """Создание таблиц базы данных"""
    
    # Таблица контрагентов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contractors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        head_contractor TEXT,
        buyer TEXT,
        manager TEXT,
        region TEXT,
        UNIQUE(head_contractor, buyer, manager, region)
    )
    ''')
    
    # Таблица номенклатуры
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        characteristics TEXT,
        category TEXT,
        UNIQUE(name, characteristics, category)
    )
    ''')
    
    # Таблица заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contractor_id INTEGER,
            product_id INTEGER,
            order_date DATE,
            quantity REAL,
            amount REAL,
            file_hash TEXT,
            FOREIGN KEY (contractor_id) REFERENCES contractors (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Индексы для ускорения запросов
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_date ON orders (order_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_contractor ON orders (contractor_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_product ON orders (product_id)')

def process_data_rows(df, cursor, date_columns, file_hash):
    """Обработка строк данных"""
    
    processed_count = 0
    skipped_empty = 0
    skipped_total = 0
    
    for index, row in df.iterrows():
        if index % 1000 == 0:
            logger.info(f"Обработано строк: {index}, добавлено записей: {processed_count}")
        
        # Извлекаем основную информацию
        # Определяем индексы колонок динамически
        head_contractor = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''
        
        # Ищем колонку с покупателем (может быть на разных позициях)
        buyer = ''
        manager = ''
        region = ''
        product_name = ''
        characteristics = ''
        category = ''
        
        # Проверяем разные возможные позиции для buyer
        for i in [3, 4, 5]:
            if i < len(row) and pd.notna(row.iloc[i]) and str(row.iloc[i]).strip():
                buyer = str(row.iloc[i])
                break
        
        # Проверяем разные возможные позиции для manager
        for i in [4, 5, 6]:
            if i < len(row) and pd.notna(row.iloc[i]) and str(row.iloc[i]).strip():
                manager = str(row.iloc[i])
                break
        
        # Проверяем разные возможные позиции для region
        for i in [6, 7, 8]:
            if i < len(row) and pd.notna(row.iloc[i]) and str(row.iloc[i]).strip():
                region = str(row.iloc[i])
                break
        
        # Проверяем разные возможные позиции для product_name
        for i in [7, 8, 9]:
            if i < len(row) and pd.notna(row.iloc[i]) and str(row.iloc[i]).strip():
                product_name = str(row.iloc[i])
                break
        
        # Проверяем разные возможные позиции для characteristics
        for i in [8, 9, 10]:
            if i < len(row) and pd.notna(row.iloc[i]) and str(row.iloc[i]).strip():
                characteristics = str(row.iloc[i])
                break
        
        # Проверяем разные возможные позиции для category
        for i in [9, 10, 11]:
            if i < len(row) and pd.notna(row.iloc[i]) and str(row.iloc[i]).strip():
                category = str(row.iloc[i])
                break
        
        # Пропускаем пустые строки и строки итогов
        if not any([head_contractor, buyer, product_name]) or not head_contractor.strip() or not buyer.strip() or not product_name.strip():
            skipped_empty += 1
            continue
        
        # Пропускаем строки с итогами (где в названии товара есть "итого" или пустые значения)
        if 'итого' in product_name.lower() or 'итого' in head_contractor.lower():
            skipped_total += 1
            continue
        
        # Добавляем контрагента
        contractor_id = get_or_create_contractor(cursor, head_contractor, buyer, manager, region)
        
        # Добавляем продукт
        product_id = get_or_create_product(cursor, product_name, characteristics, category)
        
        # Обрабатываем данные по датам
        for col_index, date_str in date_columns:
            try:
                # Преобразуем дату
                order_date = datetime.strptime(date_str, '%d.%m.%Y').date()
                

                # В CSV структура: дата, пустая колонка, следующая дата...
                # В данных: количество в той же колонке что и дата, сумма в следующей
                quantity = None
                amount = None
                
                # Количество находится в той же колонке что и дата
                if col_index < len(row):
                    quantity = clean_numeric_value(row.iloc[col_index], debug=(index < 5))
                
                # Сумма находится в следующей колонке
                if col_index + 1 < len(row):
                    amount = clean_numeric_value(row.iloc[col_index + 1], debug=(index < 5))
                
                # Отладочная информация для первых нескольких записей
                if index < 5:
                    logger.info(f"Отладка строка {index}, дата {date_str}: col_index={col_index}, quantity_raw='{row.iloc[col_index] if col_index < len(row) else 'N/A'}', quantity={quantity}, amount_raw='{row.iloc[col_index + 1] if col_index + 1 < len(row) else 'N/A'}', amount={amount}")
                
                # Добавляем заказ только если есть данные о количестве
                if quantity is not None and quantity > 0:
                    cursor.execute('''
                    INSERT INTO orders (contractor_id, product_id, order_date, quantity, amount, file_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (contractor_id, product_id, order_date, quantity, amount, file_hash))
                    
            except (ValueError, IndexError) as e:
                continue  # Пропускаем некорректные данные
        
        processed_count += 1
    
    logger.info(f"=== ИТОГИ ОБРАБОТКИ ===")
    logger.info(f"Всего строк обработано: {len(df)}")
    logger.info(f"Добавлено записей: {processed_count}")
    logger.info(f"Пропущено пустых: {skipped_empty}")
    logger.info(f"Пропущено итогов: {skipped_total}")

def get_or_create_contractor(cursor, head_contractor, buyer, manager, region):
    """Получить или создать контрагента"""
    cursor.execute('''
    SELECT id FROM contractors 
    WHERE head_contractor = ? AND buyer = ? AND manager = ? AND region = ?
    ''', (head_contractor, buyer, manager, region))
    
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute('''
    INSERT INTO contractors (head_contractor, buyer, manager, region)
    VALUES (?, ?, ?, ?)
    ''', (head_contractor, buyer, manager, region))
    
    return cursor.lastrowid

def get_or_create_product(cursor, name, characteristics, category):
    """Получить или создать продукт"""
    cursor.execute('''
    SELECT id FROM products 
    WHERE name = ? AND characteristics = ? AND category = ?
    ''', (name, characteristics, category))
    
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute('''
    INSERT INTO products (name, characteristics, category)
    VALUES (?, ?, ?)
    ''', (name, characteristics, category))
    
    return cursor.lastrowid

def show_database_stats(cursor):
    """Показать статистику базы данных"""
    
    # Количество контрагентов
    cursor.execute('SELECT COUNT(*) FROM contractors')
    contractors_count = cursor.fetchone()[0]
    
    # Количество продуктов
    cursor.execute('SELECT COUNT(*) FROM products')
    products_count = cursor.fetchone()[0]
    
    # Количество заказов
    cursor.execute('SELECT COUNT(*) FROM orders')
    orders_count = cursor.fetchone()[0]
    
    # Общая сумма заказов
    cursor.execute('SELECT SUM(amount) FROM orders WHERE amount IS NOT NULL')
    total_amount = cursor.fetchone()[0] or 0
    
    # Период данных
    cursor.execute('SELECT MIN(order_date), MAX(order_date) FROM orders')
    date_range = cursor.fetchone()
    
    logger.info("=== СТАТИСТИКА БАЗЫ ДАННЫХ ===")
    logger.info(f"Контрагентов: {contractors_count}")
    logger.info(f"Продуктов: {products_count}")
    logger.info(f"Заказов: {orders_count}")
    logger.info(f"Общая сумма: {total_amount:,.2f} руб.")
    logger.info(f"Период: {date_range[0]} - {date_range[1]}")

if __name__ == "__main__":
    csv_file = "Заказы Оримэкс - TDSheet.csv"
    
    if parse_csv_to_database(csv_file):
        print("✅ База данных успешно создана!")
        print("📁 Файл: orimex_orders.db")
    else:
        print("❌ Ошибка при создании базы данных")
