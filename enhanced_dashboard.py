#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 Улучшенный расширенный дашборд Оримэкс - фокус на менеджеров и контрагентов
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from datetime import datetime, timedelta
import numpy as np
import warnings
import os
import time
import hashlib
warnings.filterwarnings('ignore')

# Импортируем функцию для работы с CSV
from csv_to_db import parse_csv_to_database

# Настройка страницы
st.set_page_config(
    page_title="🎯 Улучшенный дашборд Оримэкс",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Улучшенные стили
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        background: linear-gradient(90deg, #2E86AB, #A23B72, #F18F01);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .enhanced-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .manager-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
    }
    
    .contractor-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 6px 20px rgba(240, 147, 251, 0.3);
    }
    
    .metric-highlight {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin: 0.5rem;
        box-shadow: 0 5px 15px rgba(79, 172, 254, 0.3);
    }
    
    .trend-up {
        color: #51cf66;
        font-weight: bold;
    }
    
    .trend-down {
        color: #ff6b6b;
        font-weight: bold;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
    }
    
    .filter-section {
        background: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_data():
    """Загрузка данных из базы данных"""
    try:
        # Проверяем существование базы данных
        if not os.path.exists('orimex_orders.db'):
            st.warning("⚠️ База данных не найдена. Создаем базу данных из исходного файла...")
            
            # Пытаемся создать базу данных из исходного CSV файла
            csv_file = "Заказы Оримэкс - TDSheet.csv"
            if os.path.exists(csv_file):
                from csv_to_db import parse_csv_to_database
                success = parse_csv_to_database(csv_file, 'orimex_orders.db')
                if not success:
                    st.error("❌ Не удалось создать базу данных из исходного файла.")
                    return pd.DataFrame()
            else:
                st.error("❌ Исходный CSV файл не найден. Пожалуйста, загрузите данные через интерфейс.")
                return pd.DataFrame()
        
        conn = sqlite3.connect('orimex_orders.db')
        
        # Проверяем существование таблиц
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        if 'orders' not in table_names or 'contractors' not in table_names or 'products' not in table_names:
            st.error("❌ База данных не содержит необходимых таблиц. Пожалуйста, пересоздайте базу данных.")
            conn.close()
            return pd.DataFrame()
        
        query = '''
        SELECT 
            o.id,
            o.order_date,
            o.quantity,
            o.amount,
            c.head_contractor,
            c.buyer,
            c.manager,
            c.region,
            p.name as product_name,
            p.characteristics,
            p.category
        FROM orders o
        JOIN contractors c ON o.contractor_id = c.id
        JOIN products p ON o.product_id = p.id
        WHERE o.amount IS NOT NULL AND o.amount > 0
        '''
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            st.error("❌ База данных пуста. Убедитесь, что данные были загружены.")
            conn.close()
            return pd.DataFrame()
        
        df['order_date'] = pd.to_datetime(df['order_date'])
        df['month'] = df['order_date'].dt.to_period('M')
        df['week'] = df['order_date'].dt.to_period('W')
        df['day_of_week'] = df['order_date'].dt.day_name()
        df['quarter'] = df['order_date'].dt.to_period('Q')
        
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()

def create_manager_detailed_analysis(df):
    """Детальный анализ менеджеров"""
    
    # Основная статистика по менеджерам
    manager_stats = df.groupby('manager').agg({
        'amount': ['sum', 'mean', 'count', 'std'],
        'buyer': 'nunique',
        'head_contractor': 'nunique',
        'region': 'nunique',
        'product_name': 'nunique',
        'category': 'nunique',
        'order_date': ['min', 'max']
    }).round(2)
    
    manager_stats.columns = [
        'Общая сумма', 'Средний заказ', 'Количество заказов', 'Стандартное отклонение',
        'Уникальных покупателей', 'Уникальных контрагентов', 'Регионов', 
        'Товаров', 'Категорий', 'Первый заказ', 'Последний заказ'
    ]
    
    manager_stats = manager_stats.reset_index()
    
    # Расчет дополнительных метрик (с защитой от деления на ноль)
    manager_stats['Выручка на покупателя'] = manager_stats['Общая сумма'] / manager_stats['Уникальных покупателей'].replace(0, 1)
    manager_stats['Заказов на покупателя'] = manager_stats['Количество заказов'] / manager_stats['Уникальных покупателей'].replace(0, 1)
    manager_stats['Дней работы'] = (
        pd.to_datetime(manager_stats['Последний заказ']) - 
        pd.to_datetime(manager_stats['Первый заказ'])
    ).dt.days + 1
    manager_stats['Выручка в день'] = manager_stats['Общая сумма'] / manager_stats['Дней работы'].replace(0, 1)
    manager_stats['Стабильность'] = manager_stats['Средний заказ'] / manager_stats['Стандартное отклонение'].replace(0, 1)
    
    # Динамика менеджеров по месяцам
    manager_dynamics = df.groupby(['manager', df['order_date'].dt.to_period('M')])['amount'].sum().unstack(fill_value=0)
    
    # Топ-10 менеджеров для детального анализа
    top_managers = manager_stats.nlargest(10, 'Общая сумма')
    
    # График производительности менеджеров
    fig_manager_performance = px.scatter(
        manager_stats,
        x='Количество заказов',
        y='Средний заказ',
        size='Общая сумма',
        color='Выручка на покупателя',
        hover_name='manager',
        title="💼 Производительность менеджеров",
        labels={
            'Количество заказов': 'Активность (количество заказов)',
            'Средний заказ': 'Эффективность (средний чек)',
            'Выручка на покупателя': 'CLV менеджера'
        },
        color_continuous_scale='viridis'
    )
    fig_manager_performance.update_layout(height=600)
    
    # Динамика топ менеджеров
    fig_manager_dynamics = go.Figure()
    
    colors = px.colors.qualitative.Set3
    for i, manager in enumerate(top_managers['manager'].head(5)):
        if manager in manager_dynamics.index:
            monthly_data = manager_dynamics.loc[manager]
            fig_manager_dynamics.add_trace(go.Scatter(
                x=[str(month) for month in monthly_data.index],
                y=monthly_data.values,
                mode='lines+markers',
                name=manager,
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=8)
            ))
    
    fig_manager_dynamics.update_layout(
        title="📈 Динамика топ-5 менеджеров по месяцам",
        xaxis_title="Месяц",
        yaxis_title="Выручка (руб.)",
        height=500
    )
    
    # Рейтинг менеджеров
    manager_stats_sorted = manager_stats.sort_values('Общая сумма', ascending=False)
    manager_stats_sorted['Рейтинг'] = range(1, len(manager_stats_sorted) + 1)
    
    return fig_manager_performance, fig_manager_dynamics, manager_stats_sorted

def create_contractor_detailed_analysis(df):
    """Детальный анализ контрагентов"""
    
    # Анализ головных контрагентов
    contractor_stats = df.groupby('head_contractor').agg({
        'amount': ['sum', 'mean', 'count', 'std'],
        'buyer': 'nunique',
        'manager': 'nunique',
        'region': 'nunique',
        'product_name': 'nunique',
        'category': 'nunique',
        'order_date': ['min', 'max']
    }).round(2)
    
    contractor_stats.columns = [
        'Общая сумма', 'Средний заказ', 'Количество заказов', 'Стандартное отклонение',
        'Покупателей', 'Менеджеров', 'Регионов', 'Товаров', 'Категорий',
        'Первый заказ', 'Последний заказ'
    ]
    
    contractor_stats = contractor_stats.reset_index()
    
    # Расчет метрик лояльности
    contractor_stats['Дней сотрудничества'] = (
        pd.to_datetime(contractor_stats['Последний заказ']) - 
        pd.to_datetime(contractor_stats['Первый заказ'])
    ).dt.days + 1
    
    contractor_stats['Интенсивность'] = contractor_stats['Количество заказов'] / contractor_stats['Дней сотрудничества'].replace(0, 1)
    contractor_stats['Диверсификация товаров'] = contractor_stats['Товаров'] / contractor_stats['Количество заказов'].replace(0, 1)
    contractor_stats['Средний чек на покупателя'] = contractor_stats['Общая сумма'] / contractor_stats['Покупателей'].replace(0, 1)
    
    # Анализ покупателей (детальный уровень)
    buyer_stats = df.groupby(['head_contractor', 'buyer']).agg({
        'amount': ['sum', 'mean', 'count'],
        'manager': 'first',
        'region': 'first',
        'order_date': ['min', 'max']
    }).round(2)
    
    buyer_stats.columns = [
        'Общая сумма', 'Средний заказ', 'Количество заказов',
        'Менеджер', 'Регион', 'Первый заказ', 'Последний заказ'
    ]
    buyer_stats = buyer_stats.reset_index()
    
    # Динамика контрагентов
    contractor_dynamics = df.groupby(['head_contractor', df['order_date'].dt.to_period('M')])['amount'].sum().unstack(fill_value=0)
    
    # Топ контрагенты
    top_contractors = contractor_stats.nlargest(10, 'Общая сумма')
    
    # График сегментации контрагентов
    fig_contractor_segments = px.scatter(
        contractor_stats,
        x='Количество заказов',
        y='Средний заказ',
        size='Общая сумма',
        color='Интенсивность',
        hover_name='head_contractor',
        title="🏢 Сегментация контрагентов",
        labels={
            'Количество заказов': 'Объем сотрудничества',
            'Средний заказ': 'Размер среднего заказа',
            'Интенсивность': 'Заказов в день'
        },
        color_continuous_scale='plasma'
    )
    fig_contractor_segments.update_layout(height=600)
    
    # Динамика ВСЕХ контрагентов с возможностью выбора
    fig_contractor_dynamics = go.Figure()
    
    # Селектор для выбора контрагентов
    all_contractors = contractor_dynamics.index.tolist()
    
    # Показываем топ-10 по умолчанию, но даем возможность выбрать других
    default_contractors = top_contractors['head_contractor'].head(10).tolist()
    
    colors = px.colors.qualitative.Set3
    for i, contractor in enumerate(default_contractors):
        if contractor in contractor_dynamics.index:
            monthly_data = contractor_dynamics.loc[contractor]
            fig_contractor_dynamics.add_trace(go.Scatter(
                x=[str(month) for month in monthly_data.index],
                y=monthly_data.values,
                mode='lines+markers',
                name=contractor[:25] + "..." if len(contractor) > 25 else contractor,
                line=dict(width=3, color=colors[i % len(colors)]),
                marker=dict(size=8)
            ))
    
    fig_contractor_dynamics.update_layout(
        title="📊 Динамика топ-10 контрагентов по месяцам (можно выбрать других ниже)",
        xaxis_title="Месяц",
        yaxis_title="Выручка (руб.)",
        height=500
    )
    
    # Анализ лояльности контрагентов
    contractor_stats['Лояльность'] = contractor_stats['Дней сотрудничества'] / 30  # в месяцах
    contractor_stats['Категория лояльности'] = pd.cut(
        contractor_stats['Лояльность'],
        bins=[0, 1, 3, 6, float('inf')],
        labels=['Новые', 'Развивающиеся', 'Стабильные', 'Долгосрочные']
    )
    
    return fig_contractor_segments, fig_contractor_dynamics, contractor_stats, buyer_stats, all_contractors, contractor_dynamics

def create_manager_contractor_matrix(df):
    """Матрица взаимодействия менеджер-контрагент"""
    
    # Создаем матрицу менеджер × контрагент
    interaction_matrix = df.groupby(['manager', 'head_contractor'])['amount'].sum().unstack(fill_value=0)
    
    # Топ взаимодействия
    manager_contractor_pairs = df.groupby(['manager', 'head_contractor']).agg({
        'amount': 'sum',
        'id': 'count',
        'buyer': 'nunique'
    }).reset_index()
    
    manager_contractor_pairs = manager_contractor_pairs.sort_values('amount', ascending=False)
    
    # Heatmap топ взаимодействий
    top_pairs = manager_contractor_pairs.head(50)
    
    # Создаем сводную таблицу для heatmap
    heatmap_data = top_pairs.pivot_table(
        index='manager', 
        columns='head_contractor', 
        values='amount', 
        fill_value=0
    )
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=[name[:15] + "..." if len(name) > 15 else name for name in heatmap_data.columns],
        y=[name[:20] + "..." if len(name) > 20 else name for name in heatmap_data.index],
        colorscale='Blues',
        hoverongaps=False
    ))
    
    fig_heatmap.update_layout(
        title="🔥 Тепловая карта: менеджер × контрагент (топ-50 пар)",
        xaxis_title="Контрагенты",
        yaxis_title="Менеджеры",
        height=600
    )
    
    # Эффективность пар
    manager_contractor_pairs['Эффективность'] = manager_contractor_pairs['amount'] / manager_contractor_pairs['id']
    
    return fig_heatmap, manager_contractor_pairs

def create_temporal_analysis(df, entity_type='manager', grouping_period='Месяцы'):
    """Временной анализ для менеджеров или контрагентов с разными периодами группировки"""

    entity_col = 'manager' if entity_type == 'manager' else 'head_contractor'

    # Определяем период группировки
    if grouping_period == 'Дни':
        period_freq = 'D'
        period_name = 'дням'
        growth_period = 'D'
    elif grouping_period == 'Недели':
        period_freq = 'W'
        period_name = 'неделям'
        growth_period = 'W'
    else:  # Месяцы
        period_freq = 'M'
        period_name = 'месяцам'
        growth_period = 'M'

    # Анализ по выбранному периоду
    period_data = df.groupby([entity_col, df['order_date'].dt.to_period(period_freq)])['amount'].sum().unstack(fill_value=0)

    # Рост по периодам
    period_growth = period_data.pct_change(axis=1) * 100

    # Топ-5 для детального анализа
    top_entities = df.groupby(entity_col)['amount'].sum().nlargest(5).index

    # График роста по периодам
    fig_growth = go.Figure()

    colors = px.colors.qualitative.Set1
    for i, entity in enumerate(top_entities):
        if entity in period_growth.index:
            growth_data = period_growth.loc[entity].dropna()
            fig_growth.add_trace(go.Scatter(
                x=[str(p) for p in growth_data.index],
                y=growth_data.values,
                mode='lines+markers',
                name=entity[:20] + "..." if len(entity) > 20 else entity,
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=10)
            ))

    fig_growth.update_layout(
        title=f"📈 Рост по {period_name} топ-5 {'менеджеров' if entity_type == 'manager' else 'контрагентов'} (%)",
        xaxis_title=grouping_period,
        yaxis_title="Рост (%)",
        height=500
    )

    # Анализ паттернов (сезонный или недельный в зависимости от периода)
    if grouping_period == 'Дни':
        # Дневной паттерн по часам или дням недели
        pattern_data = df.groupby([entity_col, df['order_date'].dt.dayofweek])['amount'].mean().unstack(fill_value=0)
        pattern_labels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        pattern_title = "Дневной паттерн"
    elif grouping_period == 'Недели':
        # Недельный паттерн по дням недели
        pattern_data = df.groupby([entity_col, df['order_date'].dt.dayofweek])['amount'].mean().unstack(fill_value=0)
        pattern_labels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        pattern_title = "Недельный паттерн"
    else:  # Месяцы
        # Месячный паттерн
        pattern_data = df.groupby([entity_col, df['order_date'].dt.month])['amount'].mean().unstack(fill_value=0)
        pattern_labels = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
                         'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
        pattern_title = "Месячный паттерн"

    # Heatmap паттернов
    pattern_top = pattern_data.loc[top_entities] if len(top_entities) > 0 else pattern_data

    fig_pattern = go.Figure(data=go.Heatmap(
        z=pattern_top.values,
        x=pattern_labels,
        y=[name[:15] + "..." if len(name) > 15 else name for name in pattern_top.index],
        colorscale='RdYlBu_r',
        hoverongaps=False
    ))

    fig_pattern.update_layout(
        title=f"🌡️ {pattern_title} {'менеджеров' if entity_type == 'manager' else 'контрагентов'}",
        xaxis_title="Период",
        yaxis_title=f"{'Менеджеры' if entity_type == 'manager' else 'Контрагенты'}",
        height=400
    )

    return fig_growth, fig_pattern

def create_advanced_kpi_dashboard(df):
    """Расширенная панель KPI"""
    
    # Базовые метрики
    total_revenue = df['amount'].sum()
    total_orders = len(df)
    unique_customers = df['buyer'].nunique()
    unique_managers = df['manager'].nunique()
    unique_contractors = df['head_contractor'].nunique()
    
    # Продвинутые метрики
    avg_order_value = df['amount'].mean()
    median_order_value = df['amount'].median()
    
    # Концентрация (индекс Херфиндаля-Хиршмана)
    manager_shares = df.groupby('manager')['amount'].sum() / total_revenue
    hhi_managers = (manager_shares ** 2).sum() * 10000  # HHI индекс
    
    contractor_shares = df.groupby('head_contractor')['amount'].sum() / total_revenue  
    hhi_contractors = (contractor_shares ** 2).sum() * 10000
    
    # Эффективность менеджеров
    manager_efficiency = df.groupby('manager').agg({
        'amount': 'sum',
        'buyer': 'nunique'
    })
    avg_manager_efficiency = (manager_efficiency['amount'] / manager_efficiency['buyer'].replace(0, 1)).mean()
    
    # Retention rate (упрощенный)
    customer_orders = df.groupby('buyer')['id'].count()
    repeat_customers = len(customer_orders[customer_orders > 1])
    retention_rate = repeat_customers / unique_customers * 100 if unique_customers > 0 else 0
    
    # Рост (месяц к месяцу)
    monthly_revenue = df.groupby(df['order_date'].dt.to_period('M'))['amount'].sum()
    if len(monthly_revenue) > 1:
        mom_growth = (monthly_revenue.iloc[-1] - monthly_revenue.iloc[-2]) / monthly_revenue.iloc[-2] * 100
    else:
        mom_growth = 0
    
    return {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'unique_customers': unique_customers,
        'unique_managers': unique_managers,
        'unique_contractors': unique_contractors,
        'avg_order_value': avg_order_value,
        'median_order_value': median_order_value,
        'hhi_managers': hhi_managers,
        'hhi_contractors': hhi_contractors,
        'avg_manager_efficiency': avg_manager_efficiency,
        'retention_rate': retention_rate,
        'mom_growth': mom_growth
    }

def create_product_detailed_analysis(df):
    """Детальный анализ товаров"""
    
    # Основная статистика по товарам
    product_stats = df.groupby(['product_name', 'category']).agg({
        'amount': ['sum', 'mean', 'count', 'std'],
        'quantity': ['sum', 'mean'],
        'buyer': 'nunique',
        'head_contractor': 'nunique',
        'manager': 'nunique',
        'region': 'nunique',
        'order_date': ['min', 'max']
    }).round(2)
    
    product_stats.columns = [
        'Общая выручка', 'Средняя цена', 'Количество заказов', 'Стандартное отклонение',
        'Общее количество', 'Среднее количество', 'Покупателей', 'Контрагентов', 
        'Менеджеров', 'Регионов', 'Первая продажа', 'Последняя продажа'
    ]
    
    product_stats = product_stats.reset_index()
    
    # Расчет дополнительных метрик
    product_stats['Дней на рынке'] = (
        pd.to_datetime(product_stats['Последняя продажа']) - 
        pd.to_datetime(product_stats['Первая продажа'])
    ).dt.days + 1
    
    product_stats['Скорость продаж'] = product_stats['Общее количество'] / product_stats['Дней на рынке'].replace(0, 1)
    product_stats['Проникновение'] = product_stats['Покупателей'] / product_stats['Количество заказов'].replace(0, 1)
    product_stats['Географическое покрытие'] = product_stats['Регионов']
    product_stats['Популярность'] = product_stats['Покупателей'] * product_stats['Количество заказов']
    
    # Классификация товаров по ABC
    total_revenue = product_stats['Общая выручка'].sum()
    product_stats_sorted = product_stats.sort_values('Общая выручка', ascending=False)
    product_stats_sorted['Доля выручки'] = product_stats_sorted['Общая выручка'] / total_revenue * 100
    product_stats_sorted['Накопительная доля'] = product_stats_sorted['Доля выручки'].cumsum()
    
    def abc_classification(cumulative_share):
        if cumulative_share <= 80:
            return 'A'
        elif cumulative_share <= 95:
            return 'B'
        else:
            return 'C'
    
    product_stats_sorted['ABC класс'] = product_stats_sorted['Накопительная доля'].apply(abc_classification)
    
    # Динамика товаров по месяцам
    product_dynamics = df.groupby(['product_name', df['order_date'].dt.to_period('M')])['amount'].sum().unstack(fill_value=0)
    
    # График популярности vs прибыльности
    fig_product_matrix = px.scatter(
        product_stats.head(100),  # Топ-100 товаров
        x='Покупателей',
        y='Средняя цена',
        size='Общая выручка',
        color='category',
        hover_name='product_name',
        title="📦 Матрица товаров: Популярность vs Прибыльность",
        labels={
            'Покупателей': 'Популярность (уникальных покупателей)',
            'Средняя цена': 'Прибыльность (средняя цена)'
        }
    )
    fig_product_matrix.update_layout(height=600)
    
    # Динамика топ товаров
    top_products = product_stats.nlargest(8, 'Общая выручка')['product_name']
    
    fig_product_dynamics = go.Figure()
    colors = px.colors.qualitative.Set3
    
    for i, product in enumerate(top_products):
        if product in product_dynamics.index:
            monthly_data = product_dynamics.loc[product]
            fig_product_dynamics.add_trace(go.Scatter(
                x=[str(month) for month in monthly_data.index],
                y=monthly_data.values,
                mode='lines+markers',
                name=product[:25] + "..." if len(product) > 25 else product,
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=8)
            ))
    
    fig_product_dynamics.update_layout(
        title="📈 Динамика топ-8 товаров по месяцам",
        xaxis_title="Месяц",
        yaxis_title="Выручка (руб.)",
        height=500
    )
    
    # Динамика по категориям
    category_dynamics = df.groupby(['category', df['order_date'].dt.to_period('M')])['amount'].sum().unstack(fill_value=0)
    
    fig_category_dynamics = go.Figure()
    
    category_colors = px.colors.qualitative.Plotly
    for i, category in enumerate(category_dynamics.index):
        monthly_data = category_dynamics.loc[category]
        fig_category_dynamics.add_trace(go.Scatter(
            x=[str(month) for month in monthly_data.index],
            y=monthly_data.values,
            mode='lines+markers',
            name=category,
            line=dict(width=4, color=category_colors[i % len(category_colors)]),
            marker=dict(size=10)
        ))
    
    fig_category_dynamics.update_layout(
        title="📊 Динамика продаж по категориям товаров",
        xaxis_title="Месяц",
        yaxis_title="Выручка (руб.)",
        height=500
    )
    
    # Создаем отдельные графики для каждой категории
    category_product_charts = {}
    
    for category in df['category'].unique():
        category_data = df[df['category'] == category]
        
        # Динамика товаров в этой категории
        category_product_dynamics = category_data.groupby(['product_name', category_data['order_date'].dt.to_period('M')])['amount'].sum().unstack(fill_value=0)
        
        # Берем топ-10 товаров в категории
        category_top_products = category_data.groupby('product_name')['amount'].sum().nlargest(10).index
        
        fig_category_products = go.Figure()
        
        colors = px.colors.qualitative.Pastel
        for i, product in enumerate(category_top_products):
            if product in category_product_dynamics.index:
                monthly_data = category_product_dynamics.loc[product]
                fig_category_products.add_trace(go.Scatter(
                    x=[str(month) for month in monthly_data.index],
                    y=monthly_data.values,
                    mode='lines+markers',
                    name=product[:30] + "..." if len(product) > 30 else product,
                    line=dict(width=3, color=colors[i % len(colors)]),
                    marker=dict(size=8)
                ))
        
        fig_category_products.update_layout(
            title=f"📦 Динамика товаров в категории '{category}' (топ-10)",
            xaxis_title="Месяц",
            yaxis_title="Выручка (руб.)",
            height=500,
            showlegend=True
        )
        
        category_product_charts[category] = fig_category_products
    
    return fig_product_matrix, fig_product_dynamics, product_stats_sorted, fig_category_dynamics, category_product_charts

def create_contractor_product_analysis(df):
    """Анализ связки контрагент-товар"""
    
    # Анализ предпочтений контрагентов по товарам
    contractor_product_matrix = df.groupby(['head_contractor', 'product_name'])['amount'].sum().unstack(fill_value=0)
    
    # Топ связки контрагент-товар
    contractor_product_pairs = df.groupby(['head_contractor', 'product_name', 'category']).agg({
        'amount': 'sum',
        'quantity': 'sum',
        'id': 'count',
        'buyer': 'nunique'
    }).reset_index()
    
    contractor_product_pairs = contractor_product_pairs.sort_values('amount', ascending=False)
    
    # Специализация контрагентов по категориям
    contractor_category_specialization = df.groupby(['head_contractor', 'category'])['amount'].sum().unstack(fill_value=0)
    contractor_category_pct = contractor_category_specialization.div(
        contractor_category_specialization.sum(axis=1), axis=0
    ) * 100
    
    # Heatmap специализации топ контрагентов
    top_contractors_spec = df.groupby('head_contractor')['amount'].sum().nlargest(15).index
    
    fig_contractor_specialization = go.Figure(data=go.Heatmap(
        z=contractor_category_pct.loc[top_contractors_spec].values,
        x=contractor_category_pct.columns,
        y=[name[:20] + "..." if len(name) > 20 else name for name in top_contractors_spec],
        colorscale='Viridis',
        hoverongaps=False,
        text=np.round(contractor_category_pct.loc[top_contractors_spec].values, 1),
        texttemplate="%{text}%",
        textfont={"size": 10}
    ))
    
    fig_contractor_specialization.update_layout(
        title="🎯 Специализация контрагентов по категориям (%)",
        xaxis_title="Категории товаров",
        yaxis_title="Контрагенты",
        height=600
    )
    
    # Анализ диверсификации товаров у контрагентов
    contractor_diversity = df.groupby('head_contractor').agg({
        'product_name': 'nunique',
        'category': 'nunique',
        'amount': 'sum',
        'id': 'count'
    }).reset_index()
    
    contractor_diversity.columns = ['head_contractor', 'Уникальных товаров', 'Категорий', 'Общая сумма', 'Заказов']
    contractor_diversity['Диверсификация'] = contractor_diversity['Уникальных товаров'] / contractor_diversity['Заказов']
    contractor_diversity['Широта ассортимента'] = contractor_diversity['Категорий']
    
    # Bubble chart диверсификации
    fig_diversity = px.scatter(
        contractor_diversity.head(50),
        x='Диверсификация',
        y='Широта ассортимента',
        size='Общая сумма',
        color='Уникальных товаров',
        hover_name='head_contractor',
        title="🌈 Диверсификация товаров у контрагентов",
        labels={
            'Диверсификация': 'Товаров на заказ',
            'Широта ассортимента': 'Количество категорий'
        },
        color_continuous_scale='plasma'
    )
    fig_diversity.update_layout(height=600)
    
    # Динамика топ пар контрагент-товар
    top_pairs = contractor_product_pairs.head(10)
    
    # Создаем временную динамику для топ пар
    pairs_dynamics = []
    for _, pair in top_pairs.iterrows():
        pair_data = df[
            (df['head_contractor'] == pair['head_contractor']) & 
            (df['product_name'] == pair['product_name'])
        ].groupby(df['order_date'].dt.to_period('M'))['amount'].sum()
        
        for month, amount in pair_data.items():
            pairs_dynamics.append({
                'Месяц': str(month),
                'Пара': f"{pair['head_contractor'][:15]}—{pair['product_name'][:15]}",
                'Выручка': amount,
                'Контрагент': pair['head_contractor'],
                'Товар': pair['product_name']
            })
    
    pairs_df = pd.DataFrame(pairs_dynamics)
    
    fig_pairs_dynamics = px.line(
        pairs_df,
        x='Месяц',
        y='Выручка',
        color='Пара',
        title="📊 Динамика топ-10 пар контрагент-товар",
        height=500
    )
    
    return fig_contractor_specialization, fig_diversity, fig_pairs_dynamics, contractor_product_pairs, contractor_diversity

def create_product_deep_dive(df, selected_product):
    """Глубокий анализ конкретного товара"""
    
    product_data = df[df['product_name'] == selected_product]
    
    if product_data.empty:
        return None, None, None
    
    # Динамика товара по месяцам
    monthly_product = product_data.groupby(product_data['order_date'].dt.to_period('M')).agg({
        'amount': 'sum',
        'quantity': 'sum',
        'id': 'count',
        'buyer': 'nunique'
    }).reset_index()
    
    fig_product_trend = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Выручка по месяцам', 'Количество продаж', 'Количество заказов', 'Уникальные покупатели'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Выручка
    fig_product_trend.add_trace(
        go.Scatter(x=[str(m) for m in monthly_product['order_date']], y=monthly_product['amount'],
                  mode='lines+markers', name='Выручка', line=dict(color='blue', width=3)),
        row=1, col=1
    )
    
    # Количество
    fig_product_trend.add_trace(
        go.Bar(x=[str(m) for m in monthly_product['order_date']], y=monthly_product['quantity'],
               name='Количество', marker_color='lightgreen'),
        row=1, col=2
    )
    
    # Заказы
    fig_product_trend.add_trace(
        go.Scatter(x=[str(m) for m in monthly_product['order_date']], y=monthly_product['id'],
                  mode='lines+markers', name='Заказы', line=dict(color='orange')),
        row=2, col=1
    )
    
    # Покупатели
    fig_product_trend.add_trace(
        go.Scatter(x=[str(m) for m in monthly_product['order_date']], y=monthly_product['buyer'],
                  mode='lines+markers', name='Покупатели', line=dict(color='red')),
        row=2, col=2
    )
    
    fig_product_trend.update_layout(height=600, showlegend=False, title_text=f"📊 Детальная динамика товара: {selected_product}")
    
    # Топ контрагенты для этого товара
    product_contractors = product_data.groupby('head_contractor').agg({
        'amount': 'sum',
        'quantity': 'sum',
        'id': 'count',
        'buyer': 'nunique'
    }).sort_values('amount', ascending=False).reset_index()
    
    # Региональное распределение товара
    product_regions = product_data.groupby('region')['amount'].sum().sort_values(ascending=False)
    
    return fig_product_trend, product_contractors, product_regions

def create_contractor_product_deep_dive(df, selected_contractor, selected_product):
    """Глубокий анализ пары контрагент-товар"""
    
    pair_data = df[
        (df['head_contractor'] == selected_contractor) & 
        (df['product_name'] == selected_product)
    ]
    
    if pair_data.empty:
        return None, None
    
    # Временная динамика пары
    pair_monthly = pair_data.groupby(pair_data['order_date'].dt.to_period('M')).agg({
        'amount': 'sum',
        'quantity': 'sum',
        'id': 'count',
        'buyer': 'nunique'
    }).reset_index()
    
    fig_pair_dynamics = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Выручка по месяцам', 'Объемы продаж'),
        vertical_spacing=0.1
    )
    
    # Выручка
    fig_pair_dynamics.add_trace(
        go.Scatter(x=[str(m) for m in pair_monthly['order_date']], y=pair_monthly['amount'],
                  mode='lines+markers', name='Выручка', 
                  line=dict(color='purple', width=4), marker=dict(size=10)),
        row=1, col=1
    )
    
    # Количество
    fig_pair_dynamics.add_trace(
        go.Bar(x=[str(m) for m in pair_monthly['order_date']], y=pair_monthly['quantity'],
               name='Количество', marker_color='lightcoral'),
        row=2, col=1
    )
    
    fig_pair_dynamics.update_layout(
        height=500, 
        showlegend=False,
        title_text=f"📈 Динамика пары: {selected_contractor} × {selected_product}"
    )
    
    # Статистика пары
    pair_stats = {
        'total_revenue': pair_data['amount'].sum(),
        'total_quantity': pair_data['quantity'].sum(),
        'total_orders': len(pair_data),
        'unique_buyers': pair_data['buyer'].nunique(),
        'avg_order': pair_data['amount'].mean(),
        'first_order': pair_data['order_date'].min(),
        'last_order': pair_data['order_date'].max(),
        'days_active': (pair_data['order_date'].max() - pair_data['order_date'].min()).days + 1
    }
    
    return fig_pair_dynamics, pair_stats

def create_period_comparison(df, period1_start, period1_end, period2_start, period2_end):
    """Сравнение двух периодов"""
    
    # Фильтрация данных по периодам
    period1_data = df[
        (df['order_date'].dt.date >= period1_start) & 
        (df['order_date'].dt.date <= period1_end)
    ]
    
    period2_data = df[
        (df['order_date'].dt.date >= period2_start) & 
        (df['order_date'].dt.date <= period2_end)
    ]
    
    # Основные метрики сравнения
    comparison_metrics = {
        'Выручка': {
            'Период 1': period1_data['amount'].sum(),
            'Период 2': period2_data['amount'].sum()
        },
        'Заказы': {
            'Период 1': len(period1_data),
            'Период 2': len(period2_data)
        },
        'Средний чек': {
            'Период 1': period1_data['amount'].mean(),
            'Период 2': period2_data['amount'].mean()
        },
        'Клиенты': {
            'Период 1': period1_data['buyer'].nunique(),
            'Период 2': period2_data['buyer'].nunique()
        },
        'Контрагенты': {
            'Период 1': period1_data['head_contractor'].nunique(),
            'Период 2': period2_data['head_contractor'].nunique()
        }
    }
    
    # График сравнения основных метрик
    metrics_df = pd.DataFrame(comparison_metrics).T
    metrics_df['Изменение'] = ((metrics_df['Период 2'] - metrics_df['Период 1']) / metrics_df['Период 1'] * 100).round(1)
    
    fig_comparison = go.Figure()
    
    fig_comparison.add_trace(go.Bar(
        x=metrics_df.index,
        y=metrics_df['Период 1'],
        name=f'Период 1 ({period1_start} - {period1_end})',
        marker_color='lightblue',
        opacity=0.8
    ))
    
    fig_comparison.add_trace(go.Bar(
        x=metrics_df.index,
        y=metrics_df['Период 2'],
        name=f'Период 2 ({period2_start} - {period2_end})',
        marker_color='lightcoral',
        opacity=0.8
    ))
    
    fig_comparison.update_layout(
        title="📊 Сравнение ключевых метрик между периодами",
        barmode='group',
        height=500
    )
    
    # Сравнение по категориям
    cat1_data = period1_data.groupby('category')['amount'].sum()
    cat2_data = period2_data.groupby('category')['amount'].sum()
    
    # Объединяем данные по категориям
    cat_comparison = pd.DataFrame({
        'Период 1': cat1_data,
        'Период 2': cat2_data
    }).fillna(0)
    
    cat_comparison['Изменение %'] = ((cat_comparison['Период 2'] - cat_comparison['Период 1']) / cat_comparison['Период 1'] * 100).round(1)
    cat_comparison['Изменение %'] = cat_comparison['Изменение %'].replace([np.inf, -np.inf], 0)
    
    fig_category_comparison = go.Figure()
    
    fig_category_comparison.add_trace(go.Bar(
        x=cat_comparison.index,
        y=cat_comparison['Период 1'],
        name=f'Период 1 ({period1_start} - {period1_end})',
        marker_color='skyblue',
        opacity=0.8
    ))

    fig_category_comparison.add_trace(go.Bar(
        x=cat_comparison.index,
        y=cat_comparison['Период 2'],
        name=f'Период 2 ({period2_start} - {period2_end})',
        marker_color='salmon',
        opacity=0.8
    ))
    
    fig_category_comparison.update_layout(
        title="📦 Сравнение выручки по категориям",
        barmode='group',
        height=500
    )
    
    # Сравнение топ менеджеров
    mgr1_data = period1_data.groupby('manager')['amount'].sum().nlargest(10)
    mgr2_data = period2_data.groupby('manager')['amount'].sum().nlargest(10)
    
    mgr_comparison = pd.DataFrame({
        'Период 1': mgr1_data,
        'Период 2': mgr2_data
    }).fillna(0)
    
    fig_manager_comparison = go.Figure()
    
    fig_manager_comparison.add_trace(go.Bar(
        x=[name[:20] + "..." if len(name) > 20 else name for name in mgr_comparison.index],
        y=mgr_comparison['Период 1'],
        name=f'Период 1 ({period1_start} - {period1_end})',
        marker_color='lightgreen',
        opacity=0.8
    ))

    fig_manager_comparison.add_trace(go.Bar(
        x=[name[:20] + "..." if len(name) > 20 else name for name in mgr_comparison.index],
        y=mgr_comparison['Период 2'],
        name=f'Период 2 ({period2_start} - {period2_end})',
        marker_color='orange',
        opacity=0.8
    ))
    
    fig_manager_comparison.update_layout(
        title="👨‍💼 Сравнение топ менеджеров между периодами",
        barmode='group',
        height=500
    )
    
    # Сравнение всех контрагентов
    contr1_data = period1_data.groupby('head_contractor')['amount'].sum()
    contr2_data = period2_data.groupby('head_contractor')['amount'].sum()
    
    contr_comparison = pd.DataFrame({
        'Период 1': contr1_data,
        'Период 2': contr2_data
    }).fillna(0)
    
    fig_contractor_comparison = go.Figure()
    
    fig_contractor_comparison.add_trace(go.Bar(
        x=[name[:20] + "..." if len(name) > 20 else name for name in contr_comparison.index],
        y=contr_comparison['Период 1'],
        name=f'Период 1 ({period1_start} - {period1_end})',
        marker_color='mediumpurple',
        opacity=0.8
    ))

    fig_contractor_comparison.add_trace(go.Bar(
        x=[name[:20] + "..." if len(name) > 20 else name for name in contr_comparison.index],
        y=contr_comparison['Период 2'],
        name=f'Период 2 ({period2_start} - {period2_end})',
        marker_color='gold',
        opacity=0.8
    ))
    
    fig_contractor_comparison.update_layout(
        title="🏢 Сравнение всех контрагентов между периодами",
        barmode='group',
        height=800  # Еще больше высоты для лучшей читаемости
    )

    # Анализ выручки товаров по категориям между периодами
    product1_data = period1_data.groupby(['product_name', 'category'])['amount'].sum().reset_index()
    product2_data = period2_data.groupby(['product_name', 'category'])['amount'].sum().reset_index()

    # Объединяем данные по товарам
    product_comparison = pd.merge(
        product1_data,
        product2_data,
        on=['product_name', 'category'],
        suffixes=('_p1', '_p2'),
        how='outer'
    ).fillna(0)

    # Рассчитываем изменение выручки
    product_comparison['Изменение выручки'] = product_comparison['amount_p2'] - product_comparison['amount_p1']
    product_comparison['Изменение %'] = ((product_comparison['amount_p2'] - product_comparison['amount_p1']) / product_comparison['amount_p1'] * 100).replace([np.inf, -np.inf], 0)

    # Топ-10 товаров по росту выручки для каждой категории
    top_products_by_category = {}
    categories = product_comparison['category'].unique()

    for category in categories:
        category_data = product_comparison[product_comparison['category'] == category]
        # Фильтруем только товары с положительным ростом и сортируем по изменению выручки
        top_10 = category_data[category_data['Изменение выручки'] > 0].nlargest(10, 'Изменение выручки')
        if not top_10.empty:
            top_products_by_category[category] = top_10

    # Создаем графики для топ товаров по категориям
    product_comparison_charts = []
    for category, data in top_products_by_category.items():
        fig = go.Figure()

        # Столбцы для периода 1
        fig.add_trace(go.Bar(
            x=[name[:25] + "..." if len(name) > 25 else name for name in data['product_name']],
            y=data['amount_p1'],
            name=f'Период 1 ({period1_start} - {period1_end})',
            marker_color='lightblue',
            opacity=0.8,
            text=[f"{val:,.0f} ₽" for val in data['amount_p1']],
            textposition='auto'
        ))

        # Столбцы для периода 2
        fig.add_trace(go.Bar(
            x=[name[:25] + "..." if len(name) > 25 else name for name in data['product_name']],
            y=data['amount_p2'],
            name=f'Период 2 ({period2_start} - {period2_end})',
            marker_color='lightcoral',
            opacity=0.8,
            text=[f"{val:,.0f} ₽" for val in data['amount_p2']],
            textposition='auto'
        ))

        fig.update_layout(
            title=f"💰 Сравнение выручки товаров: {category}",
            xaxis_title="Товар",
            yaxis_title="Выручка (руб.)",
            barmode='group',
            height=400
        )

        product_comparison_charts.append(fig)

    return (fig_comparison, fig_category_comparison, fig_manager_comparison,
            fig_contractor_comparison, metrics_df, cat_comparison, product_comparison_charts)

def create_cross_analysis(df):
    """Кросс-анализ менеджеров и контрагентов"""
    
    # Анализ покрытия: какие менеджеры работают с какими контрагентами
    coverage_matrix = df.groupby(['manager', 'head_contractor']).size().unstack(fill_value=0)
    coverage_matrix = (coverage_matrix > 0).astype(int)  # Бинарная матрица покрытия
    
    # Специализация менеджеров по категориям
    manager_specialization = df.groupby(['manager', 'category'])['amount'].sum().unstack(fill_value=0)
    
    # Нормализуем по строкам для получения долей
    manager_specialization_pct = manager_specialization.div(manager_specialization.sum(axis=1), axis=0) * 100
    
    # Топ менеджеры для анализа специализации
    top_managers_spec = df.groupby('manager')['amount'].sum().nlargest(8).index
    
    fig_specialization = go.Figure()
    
    for category in manager_specialization_pct.columns:
        fig_specialization.add_trace(go.Bar(
            x=[m[:15] + "..." if len(m) > 15 else m for m in top_managers_spec],
            y=[manager_specialization_pct.loc[m, category] if m in manager_specialization_pct.index else 0 for m in top_managers_spec],
            name=category
        ))
    
    fig_specialization.update_layout(
        title="🎯 Специализация менеджеров по категориям (%)",
        xaxis_title="Менеджеры",
        yaxis_title="Доля от выручки менеджера (%)",
        barmode='stack',
        height=500
    )
    
    # Анализ конкуренции между менеджерами
    shared_customers = df.groupby('buyer')['manager'].nunique()
    competitive_customers = shared_customers[shared_customers > 1]
    
    competition_data = df[df['buyer'].isin(competitive_customers.index)]
    manager_competition = competition_data.groupby(['buyer', 'manager'])['amount'].sum().unstack(fill_value=0)
    
    return fig_specialization, len(competitive_customers), manager_specialization_pct

def upload_and_update_data():
    """Функция загрузки и обновления данных из CSV файла"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 Обновление данных")
    
    # Кнопка для сброса кеша
    if st.sidebar.button("🔄 Сбросить кеш загруженных файлов", key="reset_cache_main"):
        if 'last_uploaded_file_hash' in st.session_state:
            del st.session_state.last_uploaded_file_hash
        st.sidebar.success("✅ Кеш сброшен!")
        st.rerun()
    
    uploaded_file = st.sidebar.file_uploader(
        "Загрузите новый CSV файл для обновления данных:",
        type=['csv'],
        help="Выберите CSV файл с данными заказов для обновления базы данных"
    )
    
    if uploaded_file is not None:
        # Показываем информацию о загруженном файле
        st.sidebar.write(f"📄 Файл: {uploaded_file.name}")
        st.sidebar.write(f"📏 Размер: {uploaded_file.size:,} байт")
        
        # Проверяем, не загружался ли уже этот файл
        file_hash = hashlib.md5(uploaded_file.getbuffer()).hexdigest()
        if 'last_uploaded_file_hash' in st.session_state and st.session_state.last_uploaded_file_hash == file_hash:
            st.sidebar.warning("⚠️ Этот файл уже был загружен ранее!")
            st.sidebar.write("💡 Если вы хотите загрузить файл повторно, нажмите кнопку ниже:")
            if st.sidebar.button("🔄 Сбросить кеш загруженных файлов", key="reset_cache_duplicate"):
                if 'last_uploaded_file_hash' in st.session_state:
                    del st.session_state.last_uploaded_file_hash
                st.sidebar.success("✅ Кеш сброшен! Теперь можете загрузить файл повторно.")
                st.rerun()
            return False
        
        try:
            # Сохраняем загруженный файл
            with open("temp_upload.csv", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Сохраняем хеш файла в сессии
            st.session_state.last_uploaded_file_hash = file_hash
            
            st.sidebar.info("🔄 Начинаем обработку файла...")
            
            # Обновляем базу данных
            with st.spinner("🔄 Обновление базы данных..."):
                # Проверяем, что временный файл создан
                if not os.path.exists("temp_upload.csv"):
                    raise Exception("Временный файл не был создан")
                
                st.sidebar.write(f"📁 Размер временного файла: {os.path.getsize('temp_upload.csv'):,} байт")
                
                # Добавляем данные к существующей БД
                st.sidebar.write("📊 Добавление данных к существующей БД...")
                result = parse_csv_to_database("temp_upload.csv", "orimex_orders.db")
                
                if not result:
                    raise Exception("Ошибка при добавлении данных в базу данных")
                
                # Проверяем обновленную базу данных
                if os.path.exists("orimex_orders.db"):
                    db_size = os.path.getsize("orimex_orders.db")
                    st.sidebar.write(f"📊 Размер обновленной БД: {db_size:,} байт")
                    
                    # Проверяем содержимое базы данных
                    try:
                        conn = sqlite3.connect("orimex_orders.db")
                        cursor = conn.cursor()
                        
                        # Получаем статистику
                        cursor.execute("SELECT COUNT(*) FROM contractors")
                        contractors_count = cursor.fetchone()[0]
                        
                        cursor.execute("SELECT COUNT(*) FROM products")
                        products_count = cursor.fetchone()[0]
                        
                        cursor.execute("SELECT COUNT(*) FROM orders")
                        orders_count = cursor.fetchone()[0]
                        
                        cursor.execute("SELECT SUM(amount) FROM orders")
                        total_amount = cursor.fetchone()[0] or 0
                        
                        cursor.execute("SELECT MIN(order_date), MAX(order_date) FROM orders")
                        date_range = cursor.fetchone()
                        min_date, max_date = date_range[0], date_range[1]
                        
                        conn.close()
                        
                        st.sidebar.write(f"📈 Контрагентов: {contractors_count}")
                        st.sidebar.write(f"📦 Продуктов: {products_count}")
                        st.sidebar.write(f"📋 Заказов: {orders_count}")
                        st.sidebar.write(f"💰 Общая сумма: {total_amount:,.2f} руб.")
                        st.sidebar.write(f"📅 Период: {min_date} - {max_date}")
                        
                        st.sidebar.success("✅ Данные успешно добавлены к существующей БД!")
                        
                        # Автоматически перезагружаем дашборд через 2 секунды
                        st.sidebar.info("🔄 Перезагрузка дашборда через 2 секунды...")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.sidebar.error(f"❌ Ошибка при проверке БД: {str(e)}")
                        return False
                else:
                    st.sidebar.error("❌ БД не найдена")
                    return False
                
                # Удаляем временный файл
                os.remove("temp_upload.csv")
                st.sidebar.write("🧹 Временный файл удален")
                
        except Exception as e:
            st.sidebar.error(f"❌ Ошибка при обновлении данных: {str(e)}")
            st.sidebar.exception(e)
            
            # Удаляем временный файл в случае ошибки
            if os.path.exists("temp_upload.csv"):
                os.remove("temp_upload.csv")
            return False
    
    return False

def main():
    # Заголовок
    st.markdown('<h1 class="main-header">🎯 Улучшенный дашборд анализа Оримэкс</h1>', unsafe_allow_html=True)
    
    # Функция загрузки файла
    file_uploaded = upload_and_update_data()
    
    # Загрузка данных
    with st.spinner('📊 Загрузка и обработка данных...'):
        df = load_data()
    
    # Если файл был загружен, показываем уведомление
    if file_uploaded:
        st.success("🎉 Данные успешно обновлены! Информация в дашборде актуальна.")
    
    if df.empty:
        st.error("❌ Не удалось загрузить данные. Убедитесь, что база данных создана.")
        return
    
    # Информация о текущих данных
    st.sidebar.markdown("## 📊 Информация о данных")
    
    # Время последнего обновления базы данных
    if os.path.exists('orimex_orders.db'):
        db_time = os.path.getmtime('orimex_orders.db')
        db_datetime = datetime.fromtimestamp(db_time)
        st.sidebar.write(f"🕒 Обновлено: {db_datetime.strftime('%d.%m.%Y %H:%M')}")
    
    st.sidebar.write(f"📅 Период данных: {df['order_date'].min().strftime('%d.%m.%Y')} - {df['order_date'].max().strftime('%d.%m.%Y')}")
    st.sidebar.write(f"📊 Всего записей: {len(df):,}")
    st.sidebar.write(f"💰 Общая выручка: {df['amount'].sum():,.0f} ₽")
    st.sidebar.write(f"🏢 Контрагентов: {df['head_contractor'].nunique():,}")
    st.sidebar.write(f"👨‍💼 Менеджеров: {df['manager'].nunique():,}")
    st.sidebar.write(f"📦 Товаров: {df['product_name'].nunique():,}")
    
    # Кнопка обновления данных
    if st.sidebar.button("🔄 Обновить данные", help="Перезагрузить данные из базы"):
        st.rerun()
    
    # Расширенная боковая панель с фильтрами
    st.sidebar.markdown("## 🔧 Детальные фильтры")
    
    # Фильтр по датам с пресетами
    st.sidebar.markdown('<div class="filter-section">', unsafe_allow_html=True)
    date_preset = st.sidebar.selectbox(
        "📅 Быстрый выбор периода",
        ["Весь период", "Последние 30 дней", "Последние 90 дней", 
         "Текущий месяц", "Предыдущий месяц", "Текущий квартал", "Пользовательский"],
        index=0  # По умолчанию "Весь период"
    )
    
    # Логика выбора дат
    if date_preset == "Последние 30 дней":
        end_date = df['order_date'].max().date()
        start_date = end_date - timedelta(days=30)
    elif date_preset == "Последние 90 дней":
        end_date = df['order_date'].max().date()
        start_date = end_date - timedelta(days=90)
    elif date_preset == "Текущий месяц":
        end_date = df['order_date'].max().date()
        start_date = end_date.replace(day=1)
    elif date_preset == "Предыдущий месяц":
        current_month = df['order_date'].max().date().replace(day=1)
        start_date = (current_month - timedelta(days=1)).replace(day=1)
        end_date = current_month - timedelta(days=1)
    elif date_preset == "Текущий квартал":
        end_date = df['order_date'].max().date()
        quarter_start_month = ((end_date.month - 1) // 3) * 3 + 1
        start_date = end_date.replace(month=quarter_start_month, day=1)
    elif date_preset == "Весь период":
        start_date = df['order_date'].min().date()
        end_date = df['order_date'].max().date()
    else:
        # По умолчанию весь период
        start_date = df['order_date'].min().date()
        end_date = df['order_date'].max().date()
    
    # Показываем селектор дат только для пользовательского режима
    if date_preset == "Пользовательский":
        date_range = st.sidebar.date_input(
            "Точный период",
            value=(start_date, end_date),
            min_value=df['order_date'].min().date(),
            max_value=df['order_date'].max().date()
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
    else:
        st.sidebar.info(f"📅 Выбранный период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Фильтры по сущностям
    st.sidebar.markdown('<div class="filter-section">', unsafe_allow_html=True)
    st.sidebar.markdown("### 🎯 Основные фильтры")
    
    # Регионы
    regions = sorted(df['region'].unique().tolist())
    selected_regions = st.sidebar.multiselect(
        "🗺️ Регионы", 
        regions, 
        default=[],  # По умолчанию пустой = все регионы
        help="Оставьте пустым для анализа всех регионов"
    )
    
    # Категории
    categories = sorted(df['category'].unique().tolist()) 
    selected_categories = st.sidebar.multiselect(
        "📦 Категории товаров",
        categories,
        default=[],  # По умолчанию пустой = все категории
        help="Оставьте пустым для анализа всех категорий"
    )
    
    # Контрагенты
    contractors = sorted(df['head_contractor'].unique().tolist())
    selected_contractors = st.sidebar.multiselect(
        "🏢 Головные контрагенты",
        contractors,
        default=[],  # По умолчанию пустой = все контрагенты
        help="Оставьте пустым для анализа всех контрагентов"
    )
    
    # Менеджеры  
    managers = sorted(df['manager'].unique().tolist())
    selected_managers = st.sidebar.multiselect(
        "👨‍💼 Менеджеры",
        managers,
        default=[],  # По умолчанию пустой = все менеджеры
        help="Оставьте пустым для анализа всех менеджеров"
    )
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Дополнительные фильтры
    st.sidebar.markdown('<div class="filter-section">', unsafe_allow_html=True)
    st.sidebar.markdown("### ⚙️ Дополнительные фильтры")
    
    # Размер заказа (убираем верхний лимит)
    min_amount = st.sidebar.number_input(
        "💰 Минимальный размер заказа (руб.)",
        min_value=0,
        max_value=int(df['amount'].max()),
        value=0,
        help="Минимальная сумма заказа (0 = без ограничений)"
    )
    
    # Количество товара (убираем ограничения)
    min_quantity = st.sidebar.number_input(
        "📦 Минимальное количество товара",
        min_value=0,
        max_value=int(df['quantity'].max()),
        value=0,
        help="Минимальное количество товара (0 = без ограничений)"
    )
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Применение фильтров
    filtered_df = df.copy()
    
    # Фильтр по датам
    filtered_df = filtered_df[
        (filtered_df['order_date'].dt.date >= start_date) & 
        (filtered_df['order_date'].dt.date <= end_date)
    ]
    
    # Применяем остальные фильтры (только если что-то выбрано)
    if selected_regions:  # Если список не пустой
        filtered_df = filtered_df[filtered_df['region'].isin(selected_regions)]
    
    if selected_categories:  # Если список не пустой
        filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]
        
    if selected_contractors:  # Если список не пустой
        filtered_df = filtered_df[filtered_df['head_contractor'].isin(selected_contractors)]
        
    if selected_managers:  # Если список не пустой
        filtered_df = filtered_df[filtered_df['manager'].isin(selected_managers)]
    
    # Фильтр по сумме и количеству (только если заданы ограничения)
    if min_amount > 0:
        filtered_df = filtered_df[filtered_df['amount'] >= min_amount]
    
    if min_quantity > 0:
        filtered_df = filtered_df[filtered_df['quantity'] >= min_quantity]
    
    # Отладочная информация
    st.sidebar.markdown("### 🔍 Отладочная информация")
    st.sidebar.write(f"📊 Исходных записей: {len(df):,}")
    st.sidebar.write(f"📊 После фильтрации: {len(filtered_df):,}")
    st.sidebar.write(f"💰 Исходная сумма: {df['amount'].sum():,.0f} ₽")
    st.sidebar.write(f"💰 Отфильтрованная сумма: {filtered_df['amount'].sum():,.0f} ₽")
    
    # Расширенные KPI
    kpis = create_advanced_kpi_dashboard(filtered_df)
    
    # Панель KPI
    st.markdown("## 💎 Ключевые показатели эффективности")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>💰 Общий доход</h3>
            <h2>{kpis['total_revenue']:,.0f} ₽</h2>
            <p>{'📈' if kpis['mom_growth'] > 0 else '📉'} {kpis['mom_growth']:+.1f}% к пред. месяцу</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>👨‍💼 Менеджеров</h3>
            <h2>{kpis['unique_managers']}</h2>
            <p>Средняя эффективность: {kpis['avg_manager_efficiency']:,.0f} ₽</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>🏢 Контрагентов</h3>
            <h2>{kpis['unique_contractors']}</h2>
            <p>HHI: {kpis['hhi_contractors']:.0f} {'(высокая концентрация)' if kpis['hhi_contractors'] > 2500 else '(низкая концентрация)'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>👥 Клиентов</h3>
            <h2>{kpis['unique_customers']}</h2>
            <p>🔄 Retention: {kpis['retention_rate']:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>📊 Средний чек</h3>
            <h2>{kpis['avg_order_value']:,.0f} ₽</h2>
            <p>Медиана: {kpis['median_order_value']:,.0f} ₽</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Основные вкладки
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "👨‍💼 Детальный анализ менеджеров",
        "🏢 Глубокий анализ контрагентов", 
        "📦 Анализ товаров",
        "🔗 Контрагент-Товар анализ",
        "⚖️ Сравнение периодов",
        "🔗 Матрица взаимодействий",
        "📈 Временная динамика",
        "🎯 Кросс-анализ",
        "📊 Сводные отчеты"
    ])
    
    with tab1:
        st.markdown('<div class="enhanced-card">', unsafe_allow_html=True)
        st.subheader("👨‍💼 Детальный анализ менеджеров")
        
        if not filtered_df.empty:
            fig_manager_perf, fig_manager_dyn, manager_data = create_manager_detailed_analysis(filtered_df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig_manager_perf, use_container_width=True)
            with col2:
                st.plotly_chart(fig_manager_dyn, use_container_width=True)
            
            # Детальная таблица менеджеров
            st.subheader("📋 Рейтинг менеджеров")
            
            # Добавляем цветовое кодирование
            def highlight_performance(val, col_name):
                if isinstance(val, (int, float)) and col_name in manager_data.columns:
                    if val > manager_data[col_name].quantile(0.8):
                        return 'background-color: #d4edda; color: #155724'  # Зеленый
                    elif val < manager_data[col_name].quantile(0.2):
                        return 'background-color: #f8d7da; color: #721c24'  # Красный
                return ''
            
            display_columns = [
                'Рейтинг', 'manager', 'Общая сумма', 'Средний заказ', 
                'Количество заказов', 'Уникальных покупателей', 'Выручка на покупателя',
                'Выручка в день', 'Стабильность'
            ]
            
            # Упрощенное отображение без стилизации для избежания ошибок
            display_data = manager_data[display_columns].head(15).copy()
            
            # Форматирование вручную
            for col in ['Общая сумма', 'Средний заказ', 'Выручка на покупателя', 'Выручка в день']:
                if col in display_data.columns:
                    display_data[col] = display_data[col].apply(lambda x: f"{x:,.0f} ₽" if pd.notna(x) else "0 ₽")
            
            if 'Стабильность' in display_data.columns:
                display_data['Стабильность'] = display_data['Стабильность'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "0.00")
            
            st.dataframe(display_data, use_container_width=True)
            
            # Экспорт данных менеджеров
            csv_managers = manager_data.to_csv(index=False, encoding='utf-8')
            st.download_button(
                "📥 Скачать данные по менеджерам",
                data=csv_managers,
                file_name=f"managers_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="enhanced-card">', unsafe_allow_html=True)
        st.subheader("🏢 Глубокий анализ контрагентов")
        
        if not filtered_df.empty:
            fig_contr_segments, fig_contr_dyn, contractor_data, buyer_data, all_contractors, contractor_dynamics = create_contractor_detailed_analysis(filtered_df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig_contr_segments, use_container_width=True)
            with col2:
                st.plotly_chart(fig_contr_dyn, use_container_width=True)
            
            # Селектор для просмотра динамики других контрагентов
            st.subheader("🔍 Выберите контрагентов для анализа динамики")
            
            # Безопасно формируем список опций и значений по умолчанию,
            # чтобы исключить None/NaN и значения, отсутствующие в опциях
            contractors_options = [c for c in all_contractors if isinstance(c, str) and c.strip() != ""]
            # Подстрахуемся на случай нестроковых типов
            if not contractors_options and all_contractors:
                contractors_options = [str(c) for c in all_contractors if pd.notna(c)]
            
            if len(contractors_options) >= 5:
                default_contractors_options = contractors_options[:5]
            else:
                default_contractors_options = contractors_options[:min(3, len(contractors_options))]
            
            # Гарантируем, что default — подмножество options
            default_contractors_options = [c for c in default_contractors_options if c in contractors_options]

            selected_contractors_dynamics = st.multiselect(
                "Выберите контрагентов для отображения динамики:",
                contractors_options,
                default=default_contractors_options,
                help="Выберите до 10 контрагентов для сравнения динамики"
            )
            
            if selected_contractors_dynamics:
                fig_custom_dynamics = go.Figure()
                
                colors = px.colors.qualitative.Set1
                for i, contractor in enumerate(selected_contractors_dynamics[:10]):  # Максимум 10
                    if contractor in contractor_dynamics.index:
                        monthly_data = contractor_dynamics.loc[contractor]
                        fig_custom_dynamics.add_trace(go.Scatter(
                            x=[str(month) for month in monthly_data.index],
                            y=monthly_data.values,
                            mode='lines+markers',
                            name=contractor[:30] + "..." if len(contractor) > 30 else contractor,
                            line=dict(width=3, color=colors[i % len(colors)]),
                            marker=dict(size=8)
                        ))
                
                fig_custom_dynamics.update_layout(
                    title=f"📈 Динамика выбранных контрагентов ({len(selected_contractors_dynamics)} шт.)",
                    xaxis_title="Месяц",
                    yaxis_title="Выручка (руб.)",
                    height=500
                )
                
                st.plotly_chart(fig_custom_dynamics, use_container_width=True)
            
            # Анализ лояльности
            st.subheader("💎 Анализ лояльности контрагентов")
            loyalty_stats = contractor_data['Категория лояльности'].value_counts()
            
            col3, col4 = st.columns(2)
            with col3:
                fig_loyalty = px.pie(
                    values=loyalty_stats.values,
                    names=loyalty_stats.index,
                    title="🔄 Распределение по лояльности"
                )
                st.plotly_chart(fig_loyalty, use_container_width=True)
            
            with col4:
                st.write("**📊 Статистика лояльности:**")
                for category, count in loyalty_stats.items():
                    percentage = count / len(contractor_data) * 100
                    st.write(f"• **{category}**: {count} ({percentage:.1f}%)")
                
                # Средние показатели по категориям лояльности
                loyalty_metrics = contractor_data.groupby('Категория лояльности')[
                    ['Общая сумма', 'Средний заказ', 'Интенсивность']
                ].mean().round(0)
                
                st.write("**💰 Средние показатели:**")
                st.dataframe(loyalty_metrics)
            
            # Топ контрагенты
            st.subheader("🏆 Топ-20 контрагентов")
            top_contractors_display = contractor_data.nlargest(20, 'Общая сумма')[
                ['head_contractor', 'Общая сумма', 'Средний заказ', 'Количество заказов', 
                 'Покупателей', 'Интенсивность', 'Категория лояльности']
            ]
            
            st.dataframe(
                top_contractors_display.style.format({
                    'Общая сумма': '{:,.0f} ₽',
                    'Средний заказ': '{:,.0f} ₽',
                    'Интенсивность': '{:.2f}'
                }),
                use_container_width=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="enhanced-card">', unsafe_allow_html=True)
        st.subheader("📦 Детальный анализ товаров")
        
        if not filtered_df.empty:
            fig_product_matrix, fig_product_dynamics, product_data, fig_category_dynamics, category_charts = create_product_detailed_analysis(filtered_df)
            
            # Сначала показываем динамику по категориям
            st.plotly_chart(fig_category_dynamics, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig_product_matrix, use_container_width=True)
            with col2:
                st.plotly_chart(fig_product_dynamics, use_container_width=True)
            
            # Отдельные графики по каждой категории
            st.subheader("📊 Детальная динамика товаров по категориям")
            
            # Селектор категории для детального просмотра
            selected_category_detail = st.selectbox(
                "Выберите категорию для детального анализа:",
                list(category_charts.keys()),
                help="Посмотрите динамику товаров внутри выбранной категории"
            )
            
            if selected_category_detail and selected_category_detail in category_charts:
                st.plotly_chart(category_charts[selected_category_detail], use_container_width=True)
                
                # Статистика по категории
                category_info = filtered_df[filtered_df['category'] == selected_category_detail]
                
                col_cat1, col_cat2, col_cat3, col_cat4 = st.columns(4)
                
                with col_cat1:
                    st.metric("💰 Выручка категории", f"{category_info['amount'].sum():,.0f} ₽")
                
                with col_cat2:
                    st.metric("📦 Товаров в категории", f"{category_info['product_name'].nunique():,}")
                
                with col_cat3:
                    st.metric("🛒 Заказов", f"{len(category_info):,}")
                
                with col_cat4:
                    st.metric("🏢 Контрагентов", f"{category_info['head_contractor'].nunique():,}")
            
            # Показать все категории одновременно (опционально)
            show_all_categories = st.checkbox("📊 Показать графики всех категорий одновременно")
            
            if show_all_categories:
                st.subheader("📊 Все категории")
                
                # Показываем по 2 графика в ряд
                categories_list = list(category_charts.keys())
                for i in range(0, len(categories_list), 2):
                    col_cat_left, col_cat_right = st.columns(2)
                    
                    with col_cat_left:
                        if i < len(categories_list):
                            st.plotly_chart(category_charts[categories_list[i]], use_container_width=True)
                    
                    with col_cat_right:
                        if i + 1 < len(categories_list):
                            st.plotly_chart(category_charts[categories_list[i + 1]], use_container_width=True)
            
            # ABC анализ товаров
            st.subheader("🎯 ABC классификация товаров")
            abc_stats = product_data['ABC класс'].value_counts()
            
            col3, col4 = st.columns(2)
            with col3:
                fig_abc = px.pie(
                    values=abc_stats.values,
                    names=abc_stats.index,
                    title="📊 Распределение товаров по ABC",
                    color_discrete_map={'A': '#2E8B57', 'B': '#FFD700', 'C': '#DC143C'}
                )
                st.plotly_chart(fig_abc, use_container_width=True)
            
            with col4:
                st.write("**📊 ABC статистика:**")
                total_products = len(product_data)
                for abc_class, count in abc_stats.items():
                    percentage = count / total_products * 100
                    revenue_share = product_data[product_data['ABC класс'] == abc_class]['Доля выручки'].sum()
                    
                    if abc_class == 'A':
                        st.success(f"🟢 **Класс A**: {count} товаров ({percentage:.1f}%) = {revenue_share:.1f}% выручки")
                    elif abc_class == 'B':
                        st.warning(f"🟡 **Класс B**: {count} товаров ({percentage:.1f}%) = {revenue_share:.1f}% выручки")
                    else:
                        st.error(f"🔴 **Класс C**: {count} товаров ({percentage:.1f}%) = {revenue_share:.1f}% выручки")
            
            # Детальный анализ конкретного товара
            st.subheader("🔍 Детальный анализ товара")
            
            # Селектор товара
            products_list = sorted(filtered_df['product_name'].unique())
            selected_product = st.selectbox(
                "Выберите товар для детального анализа:",
                products_list,
                help="Выберите товар чтобы увидеть его детальную динамику"
            )
            
            if selected_product:
                fig_product_deep, product_contractors, product_regions = create_product_deep_dive(filtered_df, selected_product)
                
                if fig_product_deep is not None:
                    st.plotly_chart(fig_product_deep, use_container_width=True)
                    
                    # Статистика по товару
                    col_prod1, col_prod2, col_prod3 = st.columns(3)
                    
                    product_info = filtered_df[filtered_df['product_name'] == selected_product]
                    
                    with col_prod1:
                        st.metric("💰 Общая выручка", f"{product_info['amount'].sum():,.0f} ₽")
                        st.metric("📦 Общее количество", f"{product_info['quantity'].sum():,.0f}")
                    
                    with col_prod2:
                        st.metric("🛒 Заказов", f"{len(product_info):,}")
                        st.metric("👥 Покупателей", f"{product_info['buyer'].nunique():,}")
                    
                    with col_prod3:
                        st.metric("🏢 Контрагентов", f"{product_info['head_contractor'].nunique():,}")
                        st.metric("🗺️ Регионов", f"{product_info['region'].nunique():,}")
                    
                    # Топ контрагенты для товара
                    st.write("**🏢 Топ-10 контрагентов для этого товара:**")
                    st.dataframe(product_contractors.head(10), use_container_width=True)
                else:
                    st.warning("⚠️ Нет данных для выбранного товара в текущем фильтре")
            
            # Топ товары с детализацией
            st.subheader("🏆 Топ-20 товаров")
            top_products_display = product_data.head(20)[
                ['product_name', 'category', 'ABC класс', 'Общая выручка', 'Средняя цена', 
                 'Количество заказов', 'Покупателей', 'Скорость продаж', 'Географическое покрытие']
            ]
            
            st.dataframe(top_products_display, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        st.markdown('<div class="enhanced-card">', unsafe_allow_html=True)
        st.subheader("🔗 Анализ связки контрагент-товар")
        
        if not filtered_df.empty:
            fig_contr_spec, fig_diversity, fig_pairs_dyn, pairs_data, diversity_data = create_contractor_product_analysis(filtered_df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig_contr_spec, use_container_width=True)
            with col2:
                st.plotly_chart(fig_diversity, use_container_width=True)
            
            # Динамика пар
            st.plotly_chart(fig_pairs_dyn, use_container_width=True)
            
            # Детальный анализ конкретной пары
            st.subheader("🔍 Детальный анализ пары контрагент-товар")
            
            col_select1, col_select2 = st.columns(2)
            
            with col_select1:
                # Селектор контрагента
                contractors_list = sorted(filtered_df['head_contractor'].unique())
                selected_contractor_pair = st.selectbox(
                    "🏢 Выберите контрагента:",
                    contractors_list,
                    help="Выберите контрагента для анализа"
                )
            
            with col_select2:
                # Селектор товара (фильтруем по выбранному контрагенту)
                if selected_contractor_pair:
                    contractor_products = filtered_df[
                        filtered_df['head_contractor'] == selected_contractor_pair
                    ]['product_name'].unique()
                    
                    selected_product_pair = st.selectbox(
                        "📦 Выберите товар:",
                        sorted(contractor_products),
                        help="Выберите товар этого контрагента"
                    )
                else:
                    selected_product_pair = None
            
            # Анализ выбранной пары
            if selected_contractor_pair and selected_product_pair:
                fig_pair_deep, pair_stats = create_contractor_product_deep_dive(
                    filtered_df, selected_contractor_pair, selected_product_pair
                )
                
                if fig_pair_deep is not None:
                    st.plotly_chart(fig_pair_deep, use_container_width=True)
                    
                    # Статистика пары
                    st.subheader(f"📊 Статистика пары: {selected_contractor_pair} × {selected_product_pair}")
                    
                    col_pair1, col_pair2, col_pair3, col_pair4 = st.columns(4)
                    
                    with col_pair1:
                        st.metric("💰 Общая выручка", f"{pair_stats['total_revenue']:,.0f} ₽")
                        st.metric("📦 Общее количество", f"{pair_stats['total_quantity']:,.0f}")
                    
                    with col_pair2:
                        st.metric("🛒 Заказов", f"{pair_stats['total_orders']:,}")
                        st.metric("👥 Покупателей", f"{pair_stats['unique_buyers']:,}")
                    
                    with col_pair3:
                        st.metric("📊 Средний заказ", f"{pair_stats['avg_order']:,.0f} ₽")
                        st.metric("📅 Дней активности", f"{pair_stats['days_active']:,}")
                    
                    with col_pair4:
                        st.metric("📅 Первый заказ", pair_stats['first_order'].strftime('%d.%m.%Y'))
                        st.metric("📅 Последний заказ", pair_stats['last_order'].strftime('%d.%m.%Y'))
                    
                    # Интенсивность сотрудничества
                    intensity = pair_stats['total_orders'] / pair_stats['days_active'] if pair_stats['days_active'] > 0 else 0
                    
                    if intensity > 0.5:
                        st.success(f"🔥 Высокая интенсивность: {intensity:.2f} заказов в день")
                    elif intensity > 0.1:
                        st.info(f"📊 Средняя интенсивность: {intensity:.2f} заказов в день")
                    else:
                        st.warning(f"⚠️ Низкая интенсивность: {intensity:.2f} заказов в день")
                
                else:
                    st.warning("⚠️ Нет данных для выбранной пары в текущем фильтре")
            
            # Топ пары контрагент-товар
            st.subheader("⭐ Топ-15 пар контрагент-товар")
            top_pairs_display = pairs_data.head(15)[
                ['head_contractor', 'product_name', 'category', 'amount', 'quantity', 'id', 'buyer']
            ]
            
            st.dataframe(
                top_pairs_display.style.format({
                    'amount': '{:,.0f} ₽',
                    'quantity': '{:,.0f} шт.'
                }),
                use_container_width=True,
                column_config={
                    "head_contractor": st.column_config.TextColumn("🏢 Контрагент"),
                    "product_name": st.column_config.TextColumn("📦 Товар"),
                    "category": st.column_config.TextColumn("📂 Категория"),
                    "amount": st.column_config.NumberColumn("💰 Выручка"),
                    "quantity": st.column_config.NumberColumn("📦 Количество"),
                    "id": st.column_config.NumberColumn("🛒 Заказов"),
                    "buyer": st.column_config.NumberColumn("👥 Покупателей")
                }
            )
            
            # Анализ диверсификации
            st.subheader("🌈 Диверсификация товаров у контрагентов")
            
            col5, col6 = st.columns(2)
            with col5:
                st.write("**🏆 Самые диверсифицированные:**")
                top_diversified = diversity_data.nlargest(5, 'Диверсификация')
                for _, row in top_diversified.iterrows():
                    st.write(f"• **{row['head_contractor'][:30]}**: {row['Диверсификация']:.2f} товаров/заказ")
            
            with col6:
                st.write("**📊 Средняя диверсификация по категориям:**")
                # Объединяем с данными о категориях
                contractor_main_category = df.groupby('head_contractor')['category'].agg(
                    lambda x: x.value_counts().index[0]
                ).reset_index()
                contractor_main_category.columns = ['head_contractor', 'Основная категория']
                
                diversity_with_category = diversity_data.merge(contractor_main_category, on='head_contractor')
                avg_diversity_by_category = diversity_with_category.groupby('Основная категория')['Диверсификация'].mean().round(2)
                
                for category, avg_div in avg_diversity_by_category.items():
                    st.write(f"• **{category}**: {avg_div:.2f}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab5:
        st.markdown('<div class="enhanced-card">', unsafe_allow_html=True)
        st.subheader("⚖️ Сравнение периодов")
        
        st.write("**Сравните любые два периода для анализа роста, сезонности и изменений в бизнесе**")
        
        # Селекторы периодов
        col_period1, col_period2 = st.columns(2)
        
        with col_period1:
            st.markdown("### 📅 Период 1")
            period1_preset = st.selectbox(
                "Быстрый выбор периода 1:",
                ["Пользовательский", "Текущий месяц", "Предыдущий месяц", "Последние 30 дней", "Последние 90 дней"],
                key="period1"
            )
            
            if period1_preset == "Текущий месяц":
                p1_end = df['order_date'].max().date()
                p1_start = p1_end.replace(day=1)
            elif period1_preset == "Предыдущий месяц":
                current_month = df['order_date'].max().date().replace(day=1)
                p1_start = (current_month - timedelta(days=1)).replace(day=1)
                p1_end = current_month - timedelta(days=1)
            elif period1_preset == "Последние 30 дней":
                p1_end = df['order_date'].max().date()
                p1_start = p1_end - timedelta(days=30)
            elif period1_preset == "Последние 90 дней":
                p1_end = df['order_date'].max().date()
                p1_start = p1_end - timedelta(days=90)
            else:
                p1_start = df['order_date'].min().date()
                p1_end = df['order_date'].max().date()
            
            period1_range = st.date_input(
                "Выберите период 1:",
                value=(p1_start, p1_end),
                min_value=df['order_date'].min().date(),
                max_value=df['order_date'].max().date(),
                key="period1_dates"
            )
        
        with col_period2:
            st.markdown("### 📅 Период 2")
            period2_preset = st.selectbox(
                "Быстрый выбор периода 2:",
                ["Пользовательский", "Текущий месяц", "Предыдущий месяц", "Последние 30 дней", "Последние 90 дней"],
                key="period2"
            )
            
            if period2_preset == "Текущий месяц":
                p2_end = df['order_date'].max().date()
                p2_start = p2_end.replace(day=1)
            elif period2_preset == "Предыдущий месяц":
                current_month = df['order_date'].max().date().replace(day=1)
                p2_start = (current_month - timedelta(days=1)).replace(day=1)
                p2_end = current_month - timedelta(days=1)
            elif period2_preset == "Последние 30 дней":
                p2_end = df['order_date'].max().date()
                p2_start = p2_end - timedelta(days=30)
            elif period2_preset == "Последние 90 дней":
                p2_end = df['order_date'].max().date()
                p2_start = p2_end - timedelta(days=90)
            else:
                # По умолчанию предыдущий месяц для сравнения
                current_month = df['order_date'].max().date().replace(day=1)
                p2_start = (current_month - timedelta(days=1)).replace(day=1)
                p2_end = current_month - timedelta(days=1)
            
            period2_range = st.date_input(
                "Выберите период 2:",
                value=(p2_start, p2_end),
                min_value=df['order_date'].min().date(),
                max_value=df['order_date'].max().date(),
                key="period2_dates"
            )
        
        # Проводим сравнение если выбраны оба периода
        if len(period1_range) == 2 and len(period2_range) == 2:
            p1_start, p1_end = period1_range
            p2_start, p2_end = period2_range
            
            # Создаем сравнительный анализ
            (fig_main_comparison, fig_cat_comparison, fig_mgr_comparison,
             fig_contr_comparison, metrics_comparison, cat_comparison, product_comparison_charts) = create_period_comparison(
                df, p1_start, p1_end, p2_start, p2_end
            )
            
            # Отображаем результаты
            st.plotly_chart(fig_main_comparison, use_container_width=True)
            
            # Таблица с изменениями
            st.subheader("📊 Детальное сравнение метрик")
            
            # Добавляем цветовое кодирование для изменений
            def format_change(val):
                if val > 0:
                    return f"🟢 +{val:.1f}%"
                elif val < 0:
                    return f"🔴 {val:.1f}%"
                else:
                    return f"⚪ {val:.1f}%"
            
            metrics_display = metrics_comparison.copy()
            metrics_display['Изменение'] = metrics_display['Изменение'].apply(format_change)
            
            st.dataframe(
                metrics_display.style.format({
                    'Период 1': '{:,.0f}',
                    'Период 2': '{:,.0f}'
                }),
                use_container_width=True
            )
            
            # Графики по категориям, менеджерам и контрагентам
            col_comp1, col_comp2 = st.columns(2)
            
            with col_comp1:
                st.plotly_chart(fig_cat_comparison, use_container_width=True)
                st.plotly_chart(fig_mgr_comparison, use_container_width=True)

            with col_comp2:
                # Сводка изменений по категориям
                st.subheader("📈 Изменения по категориям")
                for category, change in cat_comparison['Изменение %'].items():
                    if not pd.isna(change) and change != 0:
                        if change > 0:
                            st.success(f"📦 **{category}**: +{change:.1f}%")
                        else:
                            st.error(f"📦 **{category}**: {change:.1f}%")

            # График контрагентов на всю ширину
            st.subheader("🏢 Детальное сравнение контрагентов")
            st.plotly_chart(fig_contr_comparison, use_container_width=True)

            # Графики сравнения товаров по категориям
            if product_comparison_charts:
                st.subheader("💰 Сравнение выручки товаров по категориям")
                st.write("**Показаны топ товаров по росту выручки с разбивкой по периодам**")

                chart_index = 0
                for i, chart in enumerate(product_comparison_charts):
                    if i % 2 == 0:
                        if i > 0:
                            st.markdown("---")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.plotly_chart(chart, use_container_width=True, key=f"product_chart_{chart_index}")
                            chart_index += 1
                        if i + 1 < len(product_comparison_charts):
                            with col2:
                                st.plotly_chart(product_comparison_charts[i + 1], use_container_width=True, key=f"product_chart_{chart_index}")
                                chart_index += 1
                    elif i == len(product_comparison_charts) - 1:
                        st.plotly_chart(chart, use_container_width=True, key=f"product_chart_{chart_index}")

        else:
            st.info("📅 Выберите оба периода для проведения сравнения")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab6:
        st.markdown('<div class="enhanced-card">', unsafe_allow_html=True)
        st.subheader("🔗 Матрица взаимодействий")
        
        if not filtered_df.empty:
            fig_heatmap, interaction_data = create_manager_contractor_matrix(filtered_df)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # Топ взаимодействия
            st.subheader("⭐ Топ-15 пар менеджер-контрагент")
            top_interactions = interaction_data.head(15)[
                ['manager', 'head_contractor', 'amount', 'id', 'buyer', 'Эффективность']
            ]
            
            st.dataframe(
                top_interactions.style.format({
                    'amount': '{:,.0f} ₽',
                    'Эффективность': '{:,.0f} ₽'
                }),
                use_container_width=True,
                column_config={
                    "manager": st.column_config.TextColumn("👨‍💼 Менеджер"),
                    "head_contractor": st.column_config.TextColumn("🏢 Контрагент"),
                    "amount": st.column_config.NumberColumn("💰 Сумма"),
                    "id": st.column_config.NumberColumn("📊 Заказов"),
                    "buyer": st.column_config.NumberColumn("👥 Покупателей"),
                    "Эффективность": st.column_config.NumberColumn("⚡ Эффективность")
                }
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab7:
        st.markdown('<div class="enhanced-card">', unsafe_allow_html=True)
        st.subheader("📈 Временная динамика")
        
        if not filtered_df.empty:
            # Выбор типа анализа
            analysis_type = st.radio(
                "Выберите тип анализа:",
                ["👨‍💼 Менеджеры", "🏢 Контрагенты"],
                horizontal=True
            )

            # Выбор периода группировки
            grouping_period = st.selectbox(
                "📅 Выберите период группировки:",
                ["Дни", "Недели", "Месяцы"],
                index=2  # По умолчанию месяцы
            )

            entity_type = 'manager' if analysis_type == "👨‍💼 Менеджеры" else 'contractor'
            fig_quarterly, fig_seasonal = create_temporal_analysis(filtered_df, entity_type, grouping_period)
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig_quarterly, use_container_width=True)
            with col2:
                st.plotly_chart(fig_seasonal, use_container_width=True)
            
            # Трендовый анализ
            st.subheader("📊 Трендовый анализ")

            entity_col = 'manager' if entity_type == 'manager' else 'head_contractor'

            # Выбор конкретного менеджера/контрагента для детального анализа
            entities_list = filtered_df[entity_col].unique()
            selected_entity = st.selectbox(
                f"Выберите {'менеджера' if entity_type == 'manager' else 'контрагента'} для детального анализа:",
                entities_list
            )

            if selected_entity:
                entity_data = filtered_df[filtered_df[entity_col] == selected_entity]

                # Динамика по выбранному периоду группировки
                if grouping_period == 'Дни':
                    # Группировка по дням
                    period_entity = entity_data.groupby('order_date').agg({
                        'amount': 'sum',
                        'id': 'count',
                        'buyer': 'nunique'
                    }).reset_index()
                    x_title = "Дата (дни)"
                elif grouping_period == 'Недели':
                    # Группировка по неделям
                    period_entity = entity_data.groupby(entity_data['order_date'].dt.to_period('W')).agg({
                        'amount': 'sum',
                        'id': 'count',
                        'buyer': 'nunique'
                    }).reset_index()
                    period_entity['order_date'] = period_entity['order_date'].dt.start_time
                    x_title = "Дата (недели)"
                else:  # Месяцы
                    # Группировка по месяцам
                    period_entity = entity_data.groupby(entity_data['order_date'].dt.to_period('M')).agg({
                        'amount': 'sum',
                        'id': 'count',
                        'buyer': 'nunique'
                    }).reset_index()
                    period_entity['order_date'] = period_entity['order_date'].dt.start_time
                    x_title = "Дата (месяцы)"
                
                fig_entity_trend = go.Figure()

                fig_entity_trend.add_trace(go.Scatter(
                    x=period_entity['order_date'],
                    y=period_entity['amount'],
                    mode='lines+markers',
                    name='Выручка',
                    line=dict(color='blue', width=2),
                    yaxis='y1'
                ))

                fig_entity_trend.add_trace(go.Bar(
                    x=period_entity['order_date'],
                    y=period_entity['id'],
                    name='Количество заказов',
                    marker_color='lightblue',
                    opacity=0.6,
                    yaxis='y2'
                ))

                fig_entity_trend.update_layout(
                    title=f"📈 Детальная динамика: {selected_entity} (по {grouping_period.lower()})",
                    xaxis_title=x_title,
                    yaxis=dict(title="Выручка (руб.)", side="left"),
                    yaxis2=dict(title="Количество заказов", side="right", overlaying="y"),
                    height=500
                )
                
                st.plotly_chart(fig_entity_trend, use_container_width=True)
                
                # Статистика по выбранному объекту
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                
                with col_stat1:
                    st.metric("💰 Общая выручка", f"{entity_data['amount'].sum():,.0f} ₽")
                    st.metric("📊 Средний заказ", f"{entity_data['amount'].mean():,.0f} ₽")
                
                with col_stat2:
                    st.metric("🛒 Всего заказов", f"{len(entity_data):,}")
                    st.metric("👥 Уникальных клиентов", f"{entity_data['buyer'].nunique():,}")
                
                with col_stat3:
                    st.metric("📦 Товарных позиций", f"{entity_data['product_name'].nunique():,}")
                    st.metric("🗺️ Регионов", f"{entity_data['region'].nunique():,}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab8:
        st.markdown('<div class="enhanced-card">', unsafe_allow_html=True)
        st.subheader("🎯 Кросс-анализ")
        
        if not filtered_df.empty:
            fig_specialization, competitive_customers_count, specialization_data = create_cross_analysis(filtered_df)
            st.plotly_chart(fig_specialization, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🤝 Конкуренция за клиентов")
                st.info(f"📊 Клиентов с несколькими менеджерами: **{competitive_customers_count}**")
                
                if competitive_customers_count > 0:
                    competition_rate = competitive_customers_count / filtered_df['buyer'].nunique() * 100
                    st.write(f"📈 Доля конкурентных клиентов: **{competition_rate:.1f}%**")
                    
                    if competition_rate > 20:
                        st.warning("⚠️ Высокая конкуренция между менеджерами за клиентов")
                    else:
                        st.success("✅ Низкая конкуренция, четкое разделение клиентов")
            
            with col2:
                st.subheader("🎯 Специализация менеджеров")
                
                # Индекс специализации (насколько менеджер сфокусирован на одной категории)
                specialization_index = specialization_data.max(axis=1).sort_values(ascending=False)
                
                st.write("**🏆 Топ-5 самых специализированных:**")
                for manager, spec_level in specialization_index.head(5).items():
                    main_category = specialization_data.loc[manager].idxmax()
                    st.write(f"• **{manager[:25]}**: {spec_level:.1f}% в категории '{main_category}'")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab9:
        st.markdown('<div class="enhanced-card">', unsafe_allow_html=True)
        st.subheader("📊 Сводные отчеты и экспорт")
        
        if not filtered_df.empty:
            # Сводный отчет по менеджерам и контрагентам
            summary_report = filtered_df.groupby(['manager', 'head_contractor']).agg({
                'amount': ['sum', 'mean', 'count'],
                'buyer': 'nunique',
                'product_name': 'nunique',
                'order_date': ['min', 'max']
            }).round(2)
            
            summary_report.columns = [
                'Общая сумма', 'Средний заказ', 'Количество заказов',
                'Покупателей', 'Товаров', 'Первый заказ', 'Последний заказ'
            ]
            summary_report = summary_report.reset_index()
            
            # Фильтр для отчета
            report_filter = st.selectbox(
                "Показать отчет:",
                ["Все пары", "Только активные (>5 заказов)", "Только крупные (>100k ₽)", "VIP (>500k ₽)"]
            )
            
            if report_filter == "Только активные (>5 заказов)":
                display_report = summary_report[summary_report['Количество заказов'] > 5]
            elif report_filter == "Только крупные (>100k ₽)":
                display_report = summary_report[summary_report['Общая сумма'] > 100000]
            elif report_filter == "VIP (>500k ₽)":
                display_report = summary_report[summary_report['Общая сумма'] > 500000]
            else:
                display_report = summary_report
            
            st.dataframe(
                display_report.head(50).style.format({
                    'Общая сумма': '{:,.0f} ₽',
                    'Средний заказ': '{:,.0f} ₽'
                }),
                use_container_width=True
            )
            
            st.info(f"📊 Показано {len(display_report)} пар из {len(summary_report)} общих")
            
            # Множественный экспорт
            col_exp1, col_exp2, col_exp3 = st.columns(3)
            
            with col_exp1:
                csv_summary = display_report.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    "📥 Сводный отчет (CSV)",
                    data=csv_summary,
                    file_name=f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col_exp2:
                csv_buyers = buyer_data.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    "📥 Детализация по покупателям (CSV)",
                    data=csv_buyers,
                    file_name=f"buyers_detail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col_exp3:
                csv_contractors = contractor_data.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    "📥 Анализ контрагентов (CSV)",
                    data=csv_contractors,
                    file_name=f"contractors_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Боковая панель со статистикой фильтрации
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📊 Статистика фильтрации")
    
    if not filtered_df.empty:
        total_filtered_revenue = filtered_df['amount'].sum()
        total_revenue = df['amount'].sum()
        filter_coverage = total_filtered_revenue / total_revenue * 100
        
        st.sidebar.metric("🎯 Покрытие фильтром", f"{filter_coverage:.1f}%")
        st.sidebar.metric("📊 Записей отфильтровано", f"{len(filtered_df):,} из {len(df):,}")
        
        # Быстрая статистика по фильтрам
        st.sidebar.write("**🔍 Активные фильтры:**")
        if selected_regions:
            st.sidebar.write(f"• Регионов: {len(selected_regions)}")
        if selected_categories:
            st.sidebar.write(f"• Категорий: {len(selected_categories)}")
        if selected_contractors:
            st.sidebar.write(f"• Контрагентов: {len(selected_contractors)}")
        if selected_managers:
            st.sidebar.write(f"• Менеджеров: {len(selected_managers)}")
    
    # Футер с информацией
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white;">
        <h3>🎯 Улучшенный дашборд Оримэкс v2.0</h3>
        <p>Детальный анализ менеджеров и контрагентов с расширенными фильтрами</p>
        <p>📊 Обработано: {len(filtered_df):,} записей | 🕐 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
        <p>🎯 Менеджеров в анализе: {filtered_df['manager'].nunique()} | 🏢 Контрагентов: {filtered_df['head_contractor'].nunique()}</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
