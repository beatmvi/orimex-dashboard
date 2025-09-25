#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Интерактивный дашборд для анализа заказов Оримэкс
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# Настройка страницы
st.set_page_config(
    page_title="📊 Дашборд Оримэкс",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомные стили
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Загрузка данных из базы данных"""
    try:
        conn = sqlite3.connect('orimex_orders.db')
        
        # Основной запрос с джойнами
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
        df['order_date'] = pd.to_datetime(df['order_date'])
        
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()

@st.cache_data
def get_summary_stats(df):
    """Получение сводной статистики"""
    if df.empty:
        return {}
    
    return {
        'total_orders': len(df),
        'total_amount': df['amount'].sum(),
        'avg_order_amount': df['amount'].mean(),
        'unique_products': df['product_name'].nunique(),
        'unique_contractors': df['head_contractor'].nunique(),
        'unique_regions': df['region'].nunique(),
        'date_range': (df['order_date'].min(), df['order_date'].max())
    }

def create_time_series_chart(df):
    """Создание графика временных рядов"""
    daily_stats = df.groupby('order_date').agg({
        'amount': 'sum',
        'quantity': 'sum',
        'id': 'count'
    }).reset_index()
    daily_stats.columns = ['date', 'total_amount', 'total_quantity', 'order_count']
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Сумма заказов по дням', 'Количество заказов по дням'),
        vertical_spacing=0.1
    )
    
    # График суммы
    fig.add_trace(
        go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['total_amount'],
            mode='lines+markers',
            name='Сумма заказов',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=4)
        ),
        row=1, col=1
    )
    
    # График количества
    fig.add_trace(
        go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['order_count'],
            mode='lines+markers',
            name='Количество заказов',
            line=dict(color='#ff7f0e', width=2),
            marker=dict(size=4)
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        showlegend=False,
        title_text="Динамика заказов во времени"
    )
    
    fig.update_xaxes(title_text="Дата")
    fig.update_yaxes(title_text="Сумма (руб.)", row=1, col=1)
    fig.update_yaxes(title_text="Количество", row=2, col=1)
    
    return fig

def create_region_analysis(df):
    """Анализ по регионам"""
    region_stats = df.groupby('region').agg({
        'amount': ['sum', 'mean', 'count']
    }).round(2)
    
    region_stats.columns = ['Общая сумма', 'Средняя сумма', 'Количество заказов']
    region_stats = region_stats.reset_index()
    
    # Pie chart для суммы по регионам
    fig_pie = px.pie(
        region_stats, 
        values='Общая сумма', 
        names='region',
        title="Распределение продаж по регионам"
    )
    
    # Bar chart для количества заказов
    fig_bar = px.bar(
        region_stats,
        x='region',
        y='Количество заказов',
        title="Количество заказов по регионам",
        color='Количество заказов',
        color_continuous_scale='viridis'
    )
    
    return fig_pie, fig_bar, region_stats

def create_product_analysis(df):
    """Анализ по товарам"""
    product_stats = df.groupby(['category', 'product_name']).agg({
        'amount': 'sum',
        'quantity': 'sum',
        'id': 'count'
    }).reset_index()
    
    product_stats.columns = ['Категория', 'Товар', 'Общая сумма', 'Общее количество', 'Количество заказов']
    product_stats = product_stats.sort_values('Общая сумма', ascending=False)
    
    # Топ-20 товаров
    top_products = product_stats.head(20)
    
    fig = px.bar(
        top_products,
        x='Общая сумма',
        y='Товар',
        color='Категория',
        orientation='h',
        title="Топ-20 товаров по сумме продаж"
    )
    fig.update_layout(height=800)
    
    return fig, product_stats

def create_contractor_analysis(df):
    """Анализ по контрагентам"""
    contractor_stats = df.groupby(['head_contractor', 'buyer']).agg({
        'amount': 'sum',
        'id': 'count'
    }).reset_index()
    
    contractor_stats.columns = ['Головной контрагент', 'Покупатель', 'Общая сумма', 'Количество заказов']
    contractor_stats = contractor_stats.sort_values('Общая сумма', ascending=False)
    
    # Топ-15 контрагентов
    top_contractors = contractor_stats.head(15)
    
    fig = px.bar(
        top_contractors,
        x='Общая сумма',
        y='Покупатель',
        orientation='h',
        title="Топ-15 покупателей по сумме заказов",
        color='Общая сумма',
        color_continuous_scale='plasma'
    )
    fig.update_layout(height=600)
    
    return fig, contractor_stats

def main():
    # Заголовок
    st.markdown('<h1 class="main-header">📊 Дашборд анализа заказов Оримэкс</h1>', unsafe_allow_html=True)
    
    # Загрузка данных
    with st.spinner('Загрузка данных...'):
        df = load_data()
    
    if df.empty:
        st.error("❌ Не удалось загрузить данные. Убедитесь, что база данных создана.")
        st.info("💡 Запустите сначала скрипт csv_to_db.py для создания базы данных.")
        return
    
    # Боковая панель с фильтрами
    st.sidebar.header("🔧 Фильтры")
    
    # Фильтр по датам
    date_range = st.sidebar.date_input(
        "Выберите период",
        value=(df['order_date'].min().date(), df['order_date'].max().date()),
        min_value=df['order_date'].min().date(),
        max_value=df['order_date'].max().date()
    )
    
    # Фильтр по регионам
    regions = ['Все'] + sorted(df['region'].unique().tolist())
    selected_region = st.sidebar.selectbox("Регион", regions)
    
    # Фильтр по категориям
    categories = ['Все'] + sorted(df['category'].unique().tolist())
    selected_category = st.sidebar.selectbox("Категория товаров", categories)
    
    # Применение фильтров
    filtered_df = df.copy()
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['order_date'].dt.date >= start_date) & 
            (filtered_df['order_date'].dt.date <= end_date)
        ]
    
    if selected_region != 'Все':
        filtered_df = filtered_df[filtered_df['region'] == selected_region]
    
    if selected_category != 'Все':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    # Основные метрики
    stats = get_summary_stats(filtered_df)
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Общая сумма", f"{stats['total_amount']:,.0f} ₽")
        
        with col2:
            st.metric("📦 Количество заказов", f"{stats['total_orders']:,}")
        
        with col3:
            st.metric("📊 Средний заказ", f"{stats['avg_order_amount']:,.0f} ₽")
        
        with col4:
            st.metric("🏭 Уникальных товаров", stats['unique_products'])
    
    # Вкладки для разных видов анализа
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Динамика во времени", 
        "🗺️ Анализ по регионам", 
        "📦 Анализ товаров", 
        "🏢 Анализ контрагентов",
        "📋 Данные"
    ])
    
    with tab1:
        st.subheader("Динамика заказов во времени")
        if not filtered_df.empty:
            fig_time = create_time_series_chart(filtered_df)
            st.plotly_chart(fig_time, width='stretch')
            
            # Дополнительная статистика по месяцам
            monthly_stats = filtered_df.groupby(filtered_df['order_date'].dt.to_period('M')).agg({
                'amount': 'sum',
                'id': 'count'
            }).reset_index()
            monthly_stats['order_date'] = monthly_stats['order_date'].astype(str)
            monthly_stats.columns = ['Месяц', 'Сумма заказов', 'Количество заказов']
            
            st.subheader("📅 Статистика по месяцам")
            st.dataframe(monthly_stats, width='stretch')
    
    with tab2:
        st.subheader("Анализ по регионам")
        if not filtered_df.empty:
            fig_pie, fig_bar, region_stats = create_region_analysis(filtered_df)
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig_pie, width='stretch')
            with col2:
                st.plotly_chart(fig_bar, width='stretch')
            
            st.subheader("📊 Детальная статистика по регионам")
            st.dataframe(region_stats, width='stretch')
    
    with tab3:
        st.subheader("Анализ товаров")
        if not filtered_df.empty:
            fig_products, product_stats = create_product_analysis(filtered_df)
            st.plotly_chart(fig_products, width='stretch')
            
            st.subheader("📦 Детальная статистика по товарам")
            st.dataframe(product_stats, width='stretch')
    
    with tab4:
        st.subheader("Анализ контрагентов")
        if not filtered_df.empty:
            fig_contractors, contractor_stats = create_contractor_analysis(filtered_df)
            st.plotly_chart(fig_contractors, width='stretch')
            
            st.subheader("🏢 Детальная статистика по контрагентам")
            st.dataframe(contractor_stats, width='stretch')
    
    with tab5:
        st.subheader("Исходные данные")
        st.info(f"Показано {len(filtered_df)} записей из {len(df)} общих")
        
        # Возможность экспорта
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False, encoding='utf-8')
            st.download_button(
                label="📥 Скачать отфильтрованные данные (CSV)",
                data=csv,
                file_name=f"orimex_orders_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        st.dataframe(filtered_df, width='stretch')
    
    # Футер
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "📊 Дашборд создан для анализа данных заказов Оримэкс | "
        f"Последнее обновление: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
