#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Дополнительные инструменты аналитики для дашборда Оримэкс
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import json

# Настройка страницы
st.set_page_config(
    page_title="🛠️ Инструменты аналитики Оримэкс",
    page_icon="🛠️",
    layout="wide"
)

def load_data():
    """Загрузка данных"""
    try:
        conn = sqlite3.connect('orimex_orders.db')
        query = '''
        SELECT 
            o.id, o.order_date, o.quantity, o.amount,
            c.head_contractor, c.buyer, c.manager, c.region,
            p.name as product_name, p.characteristics, p.category
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
        st.error(f"Ошибка загрузки: {e}")
        return pd.DataFrame()

def create_custom_report():
    """Создание пользовательского отчета"""
    st.header("📋 Конструктор отчетов")
    
    df = load_data()
    if df.empty:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Настройки отчета")
        
        # Выбор метрик
        metrics = st.multiselect(
            "Выберите метрики:",
            ['Сумма продаж', 'Количество заказов', 'Средний чек', 'Уникальные клиенты'],
            default=['Сумма продаж', 'Количество заказов']
        )
        
        # Группировка
        group_by = st.selectbox(
            "Группировать по:",
            ['Дата', 'Регион', 'Категория', 'Менеджер', 'Клиент']
        )
        
        # Период
        date_range = st.date_input(
            "Период:",
            value=(df['order_date'].min().date(), df['order_date'].max().date())
        )
        
        # Фильтры
        selected_regions = st.multiselect(
            "Регионы:",
            df['region'].unique(),
            default=df['region'].unique()[:5]
        )
        
        # Кнопка генерации
        if st.button("📊 Создать отчет"):
            # Фильтрация данных
            filtered_df = df[
                (df['order_date'].dt.date >= date_range[0]) &
                (df['order_date'].dt.date <= date_range[1]) &
                (df['region'].isin(selected_regions))
            ]
            
            # Группировка
            group_mapping = {
                'Дата': 'order_date',
                'Регион': 'region', 
                'Категория': 'category',
                'Менеджер': 'manager',
                'Клиент': 'buyer'
            }
            
            group_col = group_mapping[group_by]
            
            if group_by == 'Дата':
                grouped = filtered_df.groupby(filtered_df['order_date'].dt.date)
            else:
                grouped = filtered_df.groupby(group_col)
            
            # Расчет метрик
            report_data = {}
            
            if 'Сумма продаж' in metrics:
                report_data['Сумма продаж'] = grouped['amount'].sum()
            if 'Количество заказов' in metrics:
                report_data['Количество заказов'] = grouped['id'].count()
            if 'Средний чек' in metrics:
                report_data['Средний чек'] = grouped['amount'].mean()
            if 'Уникальные клиенты' in metrics:
                report_data['Уникальные клиенты'] = grouped['buyer'].nunique()
            
            report_df = pd.DataFrame(report_data).round(2)
            
            with col2:
                st.subheader("📊 Результат")
                st.dataframe(report_df, width='stretch')
                
                # Экспорт
                csv = report_df.to_csv(encoding='utf-8')
                st.download_button(
                    "📥 Скачать отчет",
                    data=csv,
                    file_name=f"custom_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )

def create_what_if_analysis():
    """What-if анализ"""
    st.header("🔮 What-If анализ")
    
    df = load_data()
    if df.empty:
        return
    
    st.write("**Смоделируйте различные сценарии развития бизнеса:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚙️ Параметры сценария")
        
        # Изменение цен
        price_change = st.slider(
            "Изменение цен (%)",
            min_value=-50,
            max_value=100,
            value=0,
            help="Положительные значения = рост цен, отрицательные = скидки"
        )
        
        # Изменение спроса
        demand_change = st.slider(
            "Изменение спроса (%)",
            min_value=-50,
            max_value=100,
            value=0,
            help="Как изменится количество заказов"
        )
        
        # Сезонный фактор
        seasonal_factor = st.slider(
            "Сезонный фактор",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="1.0 = обычный сезон, >1.0 = высокий сезон"
        )
        
        # Выбор категории для анализа
        selected_category = st.selectbox(
            "Категория для анализа:",
            ['Все категории'] + list(df['category'].unique())
        )
    
    with col2:
        st.subheader("📊 Результаты моделирования")
        
        # Применяем сценарий
        scenario_df = df.copy()
        
        if selected_category != 'Все категории':
            scenario_df = scenario_df[scenario_df['category'] == selected_category]
        
        # Базовые показатели
        base_revenue = scenario_df['amount'].sum()
        base_orders = len(scenario_df)
        
        # Моделирование
        new_price_multiplier = 1 + price_change / 100
        new_demand_multiplier = 1 + demand_change / 100
        
        # Эластичность спроса (упрощенная модель)
        elasticity = -0.5  # При росте цен на 10% спрос падает на 5%
        demand_price_effect = 1 + (price_change * elasticity / 100)
        
        total_demand_change = new_demand_multiplier * demand_price_effect * seasonal_factor
        
        # Новые показатели
        new_revenue = base_revenue * new_price_multiplier * total_demand_change
        new_orders = base_orders * total_demand_change
        
        # Отображение результатов
        revenue_change = (new_revenue - base_revenue) / base_revenue * 100
        orders_change = (new_orders - base_orders) / base_orders * 100
        
        st.metric("💰 Выручка", f"{new_revenue:,.0f} ₽", f"{revenue_change:+.1f}%")
        st.metric("🛒 Заказы", f"{new_orders:,.0f}", f"{orders_change:+.1f}%")
        st.metric("📊 Средний чек", f"{new_revenue/new_orders:,.0f} ₽" if new_orders > 0 else "0 ₽")
        
        # Визуализация сценария
        fig = go.Figure()
        
        scenarios = ['Текущий', 'Новый сценарий']
        revenues = [base_revenue, new_revenue]
        colors = ['blue', 'red' if revenue_change < 0 else 'green']
        
        fig.add_trace(go.Bar(
            x=scenarios,
            y=revenues,
            marker_color=colors,
            text=[f"{r:,.0f} ₽" for r in revenues],
            textposition='auto'
        ))
        
        fig.update_layout(
            title="📈 Сравнение сценариев",
            yaxis_title="Выручка (руб.)",
            height=400
        )
        
        st.plotly_chart(fig, width='stretch')

def create_advanced_filters():
    """Продвинутые фильтры и поиск"""
    st.header("🔍 Продвинутый поиск и фильтрация")
    
    df = load_data()
    if df.empty:
        return
    
    # SQL-подобный интерфейс
    st.subheader("💾 SQL-запросы")
    
    predefined_queries = {
        "Топ-10 клиентов": """
        SELECT buyer, SUM(amount) as total_amount, COUNT(*) as order_count
        FROM data 
        GROUP BY buyer 
        ORDER BY total_amount DESC 
        LIMIT 10
        """,
        "Продажи по месяцам": """
        SELECT strftime('%Y-%m', order_date) as month, 
               SUM(amount) as revenue,
               COUNT(*) as orders
        FROM data 
        GROUP BY month 
        ORDER BY month
        """,
        "Анализ категорий": """
        SELECT category, 
               SUM(amount) as revenue,
               AVG(amount) as avg_order,
               COUNT(*) as orders
        FROM data 
        GROUP BY category 
        ORDER BY revenue DESC
        """
    }
    
    selected_query = st.selectbox("Выберите готовый запрос:", list(predefined_queries.keys()))
    
    custom_query = st.text_area(
        "Или введите свой SQL-запрос:",
        value=predefined_queries[selected_query],
        height=150,
        help="Используйте 'data' как название таблицы"
    )
    
    if st.button("▶️ Выполнить запрос"):
        try:
            # Создаем временную таблицу
            conn = sqlite3.connect(':memory:')
            df.to_sql('data', conn, index=False)
            
            result = pd.read_sql_query(custom_query, conn)
            
            st.success(f"✅ Запрос выполнен успешно! Найдено {len(result)} записей")
            st.dataframe(result, width='stretch')
            
            # Экспорт результата
            csv = result.to_csv(index=False, encoding='utf-8')
            st.download_button(
                "📥 Скачать результат",
                data=csv,
                file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            conn.close()
            
        except Exception as e:
            st.error(f"❌ Ошибка выполнения запроса: {e}")

def create_data_quality_check():
    """Проверка качества данных"""
    st.header("🔍 Анализ качества данных")
    
    df = load_data()
    if df.empty:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Общая статистика")
        
        total_records = len(df)
        
        # Проверка на пропуски
        missing_data = df.isnull().sum()
        missing_percent = missing_data / len(df) * 100
        
        quality_df = pd.DataFrame({
            'Поле': missing_data.index,
            'Пропуски': missing_data.values,
            'Процент': missing_percent.values
        })
        
        st.dataframe(quality_df, width='stretch')
        
        # Дубликаты
        duplicates = df.duplicated().sum()
        st.metric("🔄 Дубликаты", duplicates)
        
        # Выбросы в суммах
        Q1 = df['amount'].quantile(0.25)
        Q3 = df['amount'].quantile(0.75)
        IQR = Q3 - Q1
        outliers = len(df[(df['amount'] < Q1 - 1.5 * IQR) | (df['amount'] > Q3 + 1.5 * IQR)])
        st.metric("⚡ Выбросы в суммах", outliers)
    
    with col2:
        st.subheader("📈 Распределения")
        
        # Гистограмма сумм заказов
        fig_hist = px.histogram(
            df[df['amount'] < df['amount'].quantile(0.95)],
            x='amount',
            nbins=50,
            title="Распределение сумм заказов"
        )
        st.plotly_chart(fig_hist, width='stretch')
        
        # Статистика по категориям
        category_stats = df.groupby('category').agg({
            'amount': ['count', 'mean', 'std', 'min', 'max']
        }).round(2)
        
        st.write("**📦 Статистика по категориям:**")
        st.dataframe(category_stats, width='stretch')

def create_export_center():
    """Центр экспорта данных"""
    st.header("📤 Центр экспорта и отчетов")
    
    df = load_data()
    if df.empty:
        return
    
    export_options = st.multiselect(
        "Выберите данные для экспорта:",
        [
            "Полные данные заказов",
            "Сводка по клиентам", 
            "Сводка по товарам",
            "Сводка по регионам",
            "Сводка по менеджерам",
            "Временные ряды (по дням)",
            "ABC анализ"
        ],
        default=["Полные данные заказов"]
    )
    
    export_format = st.radio(
        "Формат экспорта:",
        ["CSV", "Excel", "JSON"],
        horizontal=True
    )
    
    if st.button("📥 Подготовить экспорт"):
        export_data = {}
        
        if "Полные данные заказов" in export_options:
            export_data['orders'] = df
        
        if "Сводка по клиентам" in export_options:
            client_summary = df.groupby('buyer').agg({
                'amount': ['sum', 'mean', 'count'],
                'order_date': ['min', 'max']
            }).round(2)
            export_data['client_summary'] = client_summary
        
        if "Сводка по товарам" in export_options:
            product_summary = df.groupby(['product_name', 'category']).agg({
                'amount': ['sum', 'mean', 'count'],
                'quantity': 'sum'
            }).round(2)
            export_data['product_summary'] = product_summary
        
        if "Сводка по регионам" in export_options:
            region_summary = df.groupby('region').agg({
                'amount': ['sum', 'mean', 'count'],
                'buyer': 'nunique'
            }).round(2)
            export_data['region_summary'] = region_summary
        
        if "Сводка по менеджерам" in export_options:
            manager_summary = df.groupby('manager').agg({
                'amount': ['sum', 'mean', 'count'],
                'buyer': 'nunique'
            }).round(2)
            export_data['manager_summary'] = manager_summary
        
        if "Временные ряды (по дням)" in export_options:
            daily_data = df.groupby('order_date').agg({
                'amount': 'sum',
                'id': 'count'
            }).reset_index()
            export_data['daily_timeseries'] = daily_data
        
        if "ABC анализ" in export_options:
            # ABC для товаров
            product_abc = df.groupby('product_name')['amount'].sum().sort_values(ascending=False)
            product_abc_cum = (product_abc.cumsum() / product_abc.sum() * 100).reset_index()
            product_abc_cum['ABC_category'] = pd.cut(
                product_abc_cum['amount'], 
                bins=[0, 80, 95, 100], 
                labels=['A', 'B', 'C']
            )
            export_data['abc_analysis'] = product_abc_cum
        
        # Создание файлов для экспорта
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if export_format == "CSV":
            for name, data in export_data.items():
                csv = data.to_csv(index=True, encoding='utf-8')
                st.download_button(
                    f"📥 {name}.csv",
                    data=csv,
                    file_name=f"{name}_{timestamp}.csv",
                    mime="text/csv"
                )
        
        elif export_format == "JSON":
            for name, data in export_data.items():
                json_data = data.to_json(orient='records', date_format='iso')
                st.download_button(
                    f"📥 {name}.json",
                    data=json_data,
                    file_name=f"{name}_{timestamp}.json",
                    mime="application/json"
                )
        
        st.success(f"✅ Подготовлено {len(export_data)} файлов для экспорта")

def create_real_time_monitor():
    """Мониторинг в реальном времени"""
    st.header("📡 Мониторинг в реальном времени")
    
    df = load_data()
    if df.empty:
        return
    
    # Автообновление
    auto_refresh = st.checkbox("🔄 Автообновление (каждые 30 сек)")
    
    if auto_refresh:
        st.rerun()
    
    # Последние данные
    latest_date = df['order_date'].max()
    today_data = df[df['order_date'].dt.date == latest_date.date()]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Продажи сегодня",
            f"{today_data['amount'].sum():,.0f} ₽",
            f"{len(today_data)} заказов"
        )
    
    with col2:
        avg_today = today_data['amount'].mean() if len(today_data) > 0 else 0
        avg_overall = df['amount'].mean()
        change = (avg_today - avg_overall) / avg_overall * 100 if avg_overall > 0 else 0
        st.metric(
            "📊 Средний чек сегодня", 
            f"{avg_today:,.0f} ₽",
            f"{change:+.1f}% к среднему"
        )
    
    with col3:
        if len(today_data) > 0:
            top_manager_today = today_data.groupby('manager')['amount'].sum().idxmax()
            top_amount = today_data.groupby('manager')['amount'].sum().max()
            st.metric(
                "👨‍💼 Топ менеджер сегодня",
                top_manager_today[:15] + "..." if len(top_manager_today) > 15 else top_manager_today,
                f"{top_amount:,.0f} ₽"
            )
        else:
            st.metric("👨‍💼 Топ менеджер сегодня", "Нет данных", "0 ₽")
    
    with col4:
        if len(today_data) > 0:
            top_product_today = today_data.groupby('product_name')['amount'].sum().idxmax()
            st.metric(
                "🏆 Топ товар сегодня",
                top_product_today[:15] + "..." if len(top_product_today) > 15 else top_product_today,
                f"{today_data.groupby('product_name')['amount'].sum().max():,.0f} ₽"
            )
        else:
            st.metric("🏆 Топ товар сегодня", "Нет данных", "0 ₽")
    
    # График в реальном времени
    last_7_days = df[df['order_date'] >= (latest_date - timedelta(days=7))]
    daily_trend = last_7_days.groupby(last_7_days['order_date'].dt.date)['amount'].sum().reset_index()
    
    fig = px.line(
        daily_trend,
        x='order_date',
        y='amount',
        title="📈 Тренд продаж за последние 7 дней",
        markers=True
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, width='stretch')

def main():
    # Заголовок
    st.markdown('<h1 class="main-header">🛠️ Инструменты аналитики Оримэкс</h1>', unsafe_allow_html=True)
    
    # Навигация
    tool = st.selectbox(
        "🔧 Выберите инструмент:",
        [
            "📋 Конструктор отчетов",
            "🔮 What-If анализ", 
            "🔍 Продвинутые фильтры",
            "📊 Проверка качества данных",
            "📤 Центр экспорта",
            "📡 Мониторинг в реальном времени"
        ]
    )
    
    st.markdown("---")
    
    if tool == "📋 Конструктор отчетов":
        create_custom_report()
    elif tool == "🔮 What-If анализ":
        create_what_if_analysis()
    elif tool == "🔍 Продвинутые фильтры":
        create_advanced_filters()
    elif tool == "📊 Проверка качества данных":
        create_data_quality_check()
    elif tool == "📤 Центр экспорта":
        create_export_center()
    elif tool == "📡 Мониторинг в реальном времени":
        create_real_time_monitor()

if __name__ == "__main__":
    main()
