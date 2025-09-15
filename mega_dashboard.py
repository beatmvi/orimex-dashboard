#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌟 МЕГА-дашборд Оримэкс - абсолютный максимум функций и красоты
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
from scipy import stats
import json
import base64
from io import BytesIO

# Настройка страницы
st.set_page_config(
    page_title="🌟 МЕГА-дашборд Оримэкс",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Космические стили
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600;700&display=swap');
    
    .stApp {
        background: 
            radial-gradient(circle at 20% 80%, #120458 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, #ff006e 0%, transparent 50%),
            radial-gradient(circle at 40% 40%, #8338ec 0%, transparent 50%),
            linear-gradient(135deg, #000000 0%, #1a0033 25%, #330066 50%, #000000 100%);
        background-attachment: fixed;
        color: white;
        font-family: 'Exo 2', sans-serif;
    }
    
    .cosmic-header {
        font-family: 'Orbitron', monospace;
        font-size: 5rem;
        font-weight: 900;
        text-align: center;
        margin-bottom: 3rem;
        background: linear-gradient(45deg, #ff006e, #8338ec, #3a86ff, #06ffa5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 
            0 0 10px #ff006e,
            0 0 20px #8338ec,
            0 0 30px #3a86ff;
        animation: cosmic-glow 3s ease-in-out infinite alternate;
        position: relative;
    }
    
    @keyframes cosmic-glow {
        from { 
            filter: drop-shadow(0 0 20px #ff006e) drop-shadow(0 0 40px #8338ec);
            transform: scale(1);
        }
        to { 
            filter: drop-shadow(0 0 30px #8338ec) drop-shadow(0 0 60px #3a86ff);
            transform: scale(1.02);
        }
    }
    
    .hologram-card {
        background: linear-gradient(135deg, 
            rgba(255, 0, 110, 0.1) 0%, 
            rgba(131, 56, 236, 0.1) 50%, 
            rgba(58, 134, 255, 0.1) 100%);
        backdrop-filter: blur(20px);
        border-radius: 25px;
        padding: 2rem;
        margin: 1rem 0;
        border: 2px solid rgba(255, 255, 255, 0.1);
        box-shadow: 
            0 0 30px rgba(255, 0, 110, 0.3),
            0 0 60px rgba(131, 56, 236, 0.2),
            inset 0 0 30px rgba(255, 255, 255, 0.05);
        position: relative;
        overflow: hidden;
    }
    
    .hologram-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        animation: hologram-sweep 4s linear infinite;
    }
    
    @keyframes hologram-sweep {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    .quantum-metric {
        background: linear-gradient(135deg, #ff006e 0%, #8338ec 50%, #3a86ff 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        box-shadow: 
            0 0 40px rgba(255, 0, 110, 0.6),
            0 0 80px rgba(131, 56, 236, 0.4),
            0 20px 40px rgba(0, 0, 0, 0.3);
        animation: quantum-pulse 3s ease-in-out infinite;
        border: 3px solid rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    @keyframes quantum-pulse {
        0%, 100% { 
            box-shadow: 
                0 0 40px rgba(255, 0, 110, 0.6),
                0 0 80px rgba(131, 56, 236, 0.4);
        }
        50% { 
            box-shadow: 
                0 0 60px rgba(255, 0, 110, 0.8),
                0 0 120px rgba(131, 56, 236, 0.6),
                0 0 160px rgba(58, 134, 255, 0.4);
        }
    }
    
    .ai-insight {
        background: linear-gradient(135deg, #06ffa5 0%, #3a86ff 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 10px 30px rgba(6, 255, 165, 0.3);
        border-left: 5px solid #ffffff;
        animation: insight-glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes insight-glow {
        from { box-shadow: 0 10px 30px rgba(6, 255, 165, 0.3); }
        to { box-shadow: 0 15px 40px rgba(6, 255, 165, 0.5); }
    }
    
    .matrix-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
        opacity: 0.05;
    }
    
    .control-panel {
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .neon-button {
        background: linear-gradient(45deg, #ff006e, #8338ec);
        color: white;
        border: none;
        padding: 0.8rem 1.5rem;
        border-radius: 25px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 0 20px rgba(255, 0, 110, 0.5);
        transition: all 0.3s ease;
    }
    
    .neon-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 25px rgba(255, 0, 110, 0.7);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
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
        
        # Расширенные поля
        df['month'] = df['order_date'].dt.to_period('M')
        df['week'] = df['order_date'].dt.to_period('W')
        df['day_of_week'] = df['order_date'].dt.day_name()
        df['hour'] = df['order_date'].dt.hour
        df['is_weekend'] = df['order_date'].dt.dayofweek.isin([5, 6])
        df['price_per_unit'] = df['amount'] / df['quantity']
        
        # Сегментация заказов
        df['order_segment'] = pd.qcut(
            df['amount'], 
            q=5, 
            labels=['🥉 Бронза', '🥈 Серебро', '🥇 Золото', '💎 Платина', '👑 Элит']
        )
        
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()

def create_cosmic_visualizations(df):
    """Космические визуализации"""
    
    # 3D галактика продаж
    monthly_data = df.groupby([
        df['order_date'].dt.to_period('M'),
        'category',
        'region'
    ])['amount'].sum().reset_index()
    
    monthly_data['month_num'] = monthly_data['order_date'].apply(lambda x: x.month)
    monthly_data['category_num'] = pd.Categorical(monthly_data['category']).codes
    monthly_data['region_num'] = pd.Categorical(monthly_data['region']).codes
    
    fig_3d = go.Figure(data=go.Scatter3d(
        x=monthly_data['month_num'],
        y=monthly_data['category_num'],
        z=monthly_data['region_num'],
        mode='markers',
        marker=dict(
            size=np.sqrt(monthly_data['amount'] / 10000),
            color=monthly_data['amount'],
            colorscale='plasma',
            showscale=True,
            colorbar=dict(title="Выручка"),
            opacity=0.8
        ),
        text=monthly_data['amount'].apply(lambda x: f"{x:,.0f} ₽"),
        hovertemplate='<b>%{text}</b><br>' +
                     'Месяц: %{x}<br>' +
                     'Категория: %{y}<br>' +
                     'Регион: %{z}<extra></extra>'
    ))
    
    fig_3d.update_layout(
        title="🌌 3D Галактика продаж (месяц × категория × регион)",
        scene=dict(
            xaxis_title='Месяц',
            yaxis_title='Категория',
            zaxis_title='Регион',
            bgcolor='rgba(0,0,0,0.9)'
        ),
        height=700
    )
    
    return fig_3d

def create_ai_recommendations(df):
    """AI-рекомендации для бизнеса"""
    
    recommendations = []
    
    # Анализ падающих продаж
    monthly_sales = df.groupby(df['order_date'].dt.to_period('M'))['amount'].sum()
    if len(monthly_sales) >= 3:
        recent_trend = monthly_sales.tail(3).pct_change().mean() * 100
        if recent_trend < -10:
            recommendations.append({
                'type': 'warning',
                'title': '⚠️ Тревожный тренд',
                'text': f'Продажи снижаются на {abs(recent_trend):.1f}% в месяц. Рекомендуется пересмотреть стратегию.',
                'action': 'Провести анализ причин снижения'
            })
        elif recent_trend > 10:
            recommendations.append({
                'type': 'success',
                'title': '🚀 Отличная динамика',
                'text': f'Продажи растут на {recent_trend:.1f}% в месяц. Масштабируйте успешные практики.',
                'action': 'Увеличить инвестиции в рост'
            })
    
    # Анализ недоиспользованных регионов
    region_potential = df.groupby('region').agg({
        'amount': 'sum',
        'buyer': 'nunique',
        'manager': 'nunique'
    })
    
    region_potential['revenue_per_manager'] = region_potential['amount'] / region_potential['manager']
    underperforming_regions = region_potential[
        region_potential['revenue_per_manager'] < region_potential['revenue_per_manager'].median()
    ].head(3)
    
    if len(underperforming_regions) > 0:
        regions_list = ', '.join(underperforming_regions.index[:3])
        recommendations.append({
            'type': 'info',
            'title': '🎯 Возможности роста',
            'text': f'Регионы с потенциалом: {regions_list}',
            'action': 'Усилить работу с менеджерами в этих регионах'
        })
    
    # Анализ сезонности
    monthly_avg = df.groupby(df['order_date'].dt.month)['amount'].mean()
    seasonal_variation = monthly_avg.std() / monthly_avg.mean() * 100
    
    if seasonal_variation > 30:
        peak_months = monthly_avg.nlargest(2).index
        recommendations.append({
            'type': 'info', 
            'title': '📅 Сезонные возможности',
            'text': f'Высокая сезонность ({seasonal_variation:.0f}%). Пики в месяцах: {", ".join(map(str, peak_months))}',
            'action': 'Подготовиться к сезонным пикам заранее'
        })
    
    # Анализ концентрации клиентов
    client_concentration = df.groupby('buyer')['amount'].sum().sort_values(ascending=False)
    top_10_share = client_concentration.head(10).sum() / client_concentration.sum() * 100
    
    if top_10_share > 50:
        recommendations.append({
            'type': 'warning',
            'title': '⚠️ Концентрация рисков',
            'text': f'Топ-10 клиентов дают {top_10_share:.1f}% выручки',
            'action': 'Диверсифицировать клиентскую базу'
        })
    
    return recommendations

def create_interactive_simulator(df):
    """Интерактивный симулятор бизнеса"""
    
    st.subheader("🎮 Бизнес-симулятор")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🎛️ Панель управления")
        
        # Параметры симуляции
        price_change = st.slider("💰 Изменение цен (%)", -50, 100, 0)
        marketing_budget = st.slider("📢 Маркетинг бюджет (% от выручки)", 0, 20, 5)
        staff_change = st.slider("👥 Изменение штата (%)", -30, 50, 0)
        
        # Сезонный модификатор
        season_boost = st.selectbox(
            "🌟 Сезонный фактор",
            ["Обычный сезон", "Праздники (+30%)", "Распродажа (+50%)", "Кризис (-20%)"]
        )
        
        season_multipliers = {
            "Обычный сезон": 1.0,
            "Праздники (+30%)": 1.3,
            "Распродажа (+50%)": 1.5,
            "Кризис (-20%)": 0.8
        }
        
        season_factor = season_multipliers[season_boost]
        
        # Симуляция
        if st.button("🚀 Запустить симуляцию"):
            # Базовые показатели
            base_revenue = df['amount'].sum()
            base_orders = len(df)
            base_customers = df['buyer'].nunique()
            
            # Эластичность спроса
            price_elasticity = -0.8  # При росте цен на 10% спрос падает на 8%
            marketing_effectiveness = 0.3  # 1% маркетинга = 0.3% роста продаж
            
            # Расчет новых показателей
            demand_change = (
                1 + (price_change * price_elasticity / 100) +
                (marketing_budget * marketing_effectiveness / 100) +
                (staff_change / 100 * 0.5)  # Влияние штата
            ) * season_factor
            
            new_price_multiplier = 1 + price_change / 100
            new_revenue = base_revenue * new_price_multiplier * demand_change
            new_orders = base_orders * demand_change
            new_customers = base_customers * (1 + marketing_budget / 100 * 0.2)
            
            # Затраты
            marketing_cost = base_revenue * marketing_budget / 100
            staff_cost = base_revenue * 0.15 * (1 + staff_change / 100)  # 15% от выручки на зарплаты
            
            net_profit = new_revenue * 0.25 - marketing_cost - (staff_cost - base_revenue * 0.15)
            
            with col2:
                st.markdown("### 📊 Результаты симуляции")
                
                # Метрики результата
                revenue_change = (new_revenue - base_revenue) / base_revenue * 100
                orders_change = (new_orders - base_orders) / base_orders * 100
                
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    st.metric("💰 Выручка", f"{new_revenue:,.0f} ₽", f"{revenue_change:+.1f}%")
                
                with metric_col2:
                    st.metric("🛒 Заказы", f"{new_orders:,.0f}", f"{orders_change:+.1f}%")
                
                with metric_col3:
                    st.metric("💵 Чистая прибыль", f"{net_profit:,.0f} ₽")
                
                # График сравнения
                fig_simulation = go.Figure()
                
                categories = ['Выручка', 'Заказы', 'Клиенты']
                current_values = [base_revenue, base_orders, base_customers]
                new_values = [new_revenue, new_orders, new_customers]
                
                fig_simulation.add_trace(go.Bar(
                    x=categories,
                    y=current_values,
                    name='Текущее состояние',
                    marker_color='blue',
                    opacity=0.7
                ))
                
                fig_simulation.add_trace(go.Bar(
                    x=categories,
                    y=new_values,
                    name='После изменений',
                    marker_color='red',
                    opacity=0.7
                ))
                
                fig_simulation.update_layout(
                    title="📈 Сравнение сценариев",
                    barmode='group',
                    height=400
                )
                
                st.plotly_chart(fig_simulation, use_container_width=True)

def create_real_time_dashboard(df):
    """Дашборд реального времени"""
    
    # Имитация реального времени
    latest_date = df['order_date'].max()
    
    # Данные за последние периоды
    last_hour = df[df['order_date'] >= (latest_date - timedelta(hours=1))]
    last_day = df[df['order_date'] >= (latest_date - timedelta(days=1))]
    last_week = df[df['order_date'] >= (latest_date - timedelta(days=7))]
    
    # Реал-тайм метрики
    st.markdown("## ⚡ Реальное время")
    
    rt_col1, rt_col2, rt_col3, rt_col4 = st.columns(4)
    
    with rt_col1:
        st.markdown(f"""
        <div class="quantum-metric">
            <h3>💫 Последний час</h3>
            <h2>{len(last_hour)} заказов</h2>
            <p>{last_hour['amount'].sum():,.0f} ₽</p>
        </div>
        """, unsafe_allow_html=True)
    
    with rt_col2:
        st.markdown(f"""
        <div class="quantum-metric">
            <h3>🌟 Сегодня</h3>
            <h2>{len(last_day)} заказов</h2>
            <p>{last_day['amount'].sum():,.0f} ₽</p>
        </div>
        """, unsafe_allow_html=True)
    
    with rt_col3:
        st.markdown(f"""
        <div class="quantum-metric">
            <h3>⭐ За неделю</h3>
            <h2>{len(last_week)} заказов</h2>
            <p>{last_week['amount'].sum():,.0f} ₽</p>
        </div>
        """, unsafe_allow_html=True)
    
    with rt_col4:
        # Скорость продаж
        if len(last_day) > 0:
            sales_velocity = last_day['amount'].sum() / 24  # ₽ в час
        else:
            sales_velocity = 0
        
        st.markdown(f"""
        <div class="quantum-metric">
            <h3>⚡ Скорость</h3>
            <h2>{sales_velocity:,.0f} ₽/ч</h2>
            <p>Средняя скорость продаж</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Живой график (имитация)
    hourly_data = df.groupby(df['order_date'].dt.floor('H'))['amount'].sum().tail(24)
    
    fig_live = go.Figure()
    fig_live.add_trace(go.Scatter(
        x=hourly_data.index,
        y=hourly_data.values,
        mode='lines+markers',
        name='Продажи по часам',
        line=dict(color='#ff006e', width=3),
        marker=dict(size=8, color='#8338ec')
    ))
    
    fig_live.update_layout(
        title="📡 Живой график продаж (последние 24 часа)",
        xaxis_title="Время",
        yaxis_title="Выручка ₽",
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.1)'
    )
    
    return fig_live

def create_executive_summary(df):
    """Исполнительная сводка"""
    
    # Ключевые показатели для руководства
    total_revenue = df['amount'].sum()
    total_orders = len(df)
    unique_customers = df['buyer'].nunique()
    avg_order_value = df['amount'].mean()
    
    # Рост по сравнению с предыдущим периодом
    df_current = df[df['order_date'] >= df['order_date'].max() - timedelta(days=30)]
    df_previous = df[
        (df['order_date'] >= df['order_date'].max() - timedelta(days=60)) &
        (df['order_date'] < df['order_date'].max() - timedelta(days=30))
    ]
    
    current_revenue = df_current['amount'].sum()
    previous_revenue = df_previous['amount'].sum()
    revenue_growth = (current_revenue - previous_revenue) / previous_revenue * 100 if previous_revenue > 0 else 0
    
    # Топ-3 по всем категориям
    top_customers = df.groupby('buyer')['amount'].sum().nlargest(3)
    top_products = df.groupby('product_name')['amount'].sum().nlargest(3)
    top_regions = df.groupby('region')['amount'].sum().nlargest(3)
    top_managers = df.groupby('manager')['amount'].sum().nlargest(3)
    
    # Создание исполнительной сводки
    summary_data = {
        'period': f"{df['order_date'].min().strftime('%d.%m.%Y')} - {df['order_date'].max().strftime('%d.%m.%Y')}",
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'unique_customers': unique_customers,
        'avg_order_value': avg_order_value,
        'revenue_growth': revenue_growth,
        'top_customers': top_customers.to_dict(),
        'top_products': top_products.to_dict(),
        'top_regions': top_regions.to_dict(),
        'top_managers': top_managers.to_dict()
    }
    
    return summary_data

def main():
    # Космический заголовок
    st.markdown('<h1 class="cosmic-header">🌟 МЕГА-ДАШБОРД ОРИМЭКС</h1>', unsafe_allow_html=True)
    
    # Загрузка данных
    with st.spinner('🛸 Загрузка данных из космической базы...'):
        df = load_data()
    
    if df.empty:
        st.error("❌ Космическая база данных недоступна!")
        return
    
    # AI-рекомендации
    recommendations = create_ai_recommendations(df)
    
    if recommendations:
        st.markdown("## 🤖 AI-рекомендации")
        for rec in recommendations:
            if rec['type'] == 'warning':
                st.markdown(f"""
                <div class="ai-insight" style="background: linear-gradient(135deg, #ff006e 0%, #ff4757 100%);">
                    <h4>{rec['title']}</h4>
                    <p>{rec['text']}</p>
                    <small><b>Действие:</b> {rec['action']}</small>
                </div>
                """, unsafe_allow_html=True)
            elif rec['type'] == 'success':
                st.markdown(f"""
                <div class="ai-insight" style="background: linear-gradient(135deg, #06ffa5 0%, #00d2ff 100%);">
                    <h4>{rec['title']}</h4>
                    <p>{rec['text']}</p>
                    <small><b>Действие:</b> {rec['action']}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="ai-insight">
                    <h4>{rec['title']}</h4>
                    <p>{rec['text']}</p>
                    <small><b>Действие:</b> {rec['action']}</small>
                </div>
                """, unsafe_allow_html=True)
    
    # Основные разделы
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌌 Космические визуализации",
        "🎮 Бизнес-симулятор",
        "📡 Реальное время",
        "👔 Исполнительная сводка"
    ])
    
    with tab1:
        st.markdown('<div class="hologram-card">', unsafe_allow_html=True)
        if not df.empty:
            fig_3d = create_cosmic_visualizations(df)
            st.plotly_chart(fig_3d, use_container_width=True)
            
            st.markdown("""
            <div class="ai-insight">
                <h4>🌌 Интерпретация 3D галактики</h4>
                <p>Каждая точка представляет объем продаж в определенном месяце, категории и регионе.</p>
                <p>Размер точки = объем продаж, цвет = интенсивность выручки</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="hologram-card">', unsafe_allow_html=True)
        create_interactive_simulator(df)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="hologram-card">', unsafe_allow_html=True)
        if not df.empty:
            fig_live = create_real_time_dashboard(df)
            st.plotly_chart(fig_live, use_container_width=True)
            
            # Живые алерты
            st.markdown("### 🚨 Живые алерты")
            
            # Проверка на аномалии в последних данных
            recent_data = df.tail(100)
            recent_avg = recent_data['amount'].mean()
            overall_avg = df['amount'].mean()
            
            if recent_avg > overall_avg * 1.5:
                st.success("🔥 Всплеск активности! Продажи выше обычного на 50%+")
            elif recent_avg < overall_avg * 0.5:
                st.warning("⚠️ Снижение активности! Продажи ниже обычного на 50%+")
            else:
                st.info("✅ Нормальная активность продаж")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        st.markdown('<div class="hologram-card">', unsafe_allow_html=True)
        st.subheader("👔 Исполнительная сводка")
        
        if not df.empty:
            summary = create_executive_summary(df)
            
            # Основные показатели
            exec_col1, exec_col2, exec_col3 = st.columns(3)
            
            with exec_col1:
                st.markdown(f"""
                <div class="quantum-metric">
                    <h3>📈 Финансовые результаты</h3>
                    <h2>{summary['total_revenue']:,.0f} ₽</h2>
                    <p>Общая выручка</p>
                    <p style="color: {'lightgreen' if summary['revenue_growth'] > 0 else 'lightcoral'};">
                        {summary['revenue_growth']:+.1f}% к предыдущему периоду
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            with exec_col2:
                st.markdown(f"""
                <div class="quantum-metric">
                    <h3>🎯 Операционные показатели</h3>
                    <h2>{summary['total_orders']:,}</h2>
                    <p>Заказов обработано</p>
                    <p>Средний чек: {summary['avg_order_value']:,.0f} ₽</p>
                </div>
                """, unsafe_allow_html=True)
            
            with exec_col3:
                st.markdown(f"""
                <div class="quantum-metric">
                    <h3>👥 Клиентская база</h3>
                    <h2>{summary['unique_customers']:,}</h2>
                    <p>Уникальных клиентов</p>
                    <p>Заказов на клиента: {summary['total_orders']/summary['unique_customers']:.1f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Топ-списки
            st.markdown("### 🏆 Топ-рейтинги")
            
            top_col1, top_col2, top_col3, top_col4 = st.columns(4)
            
            with top_col1:
                st.markdown("**👥 Топ клиенты:**")
                for i, (client, amount) in enumerate(summary['top_customers'].items()):
                    medal = ["🥇", "🥈", "🥉"][i]
                    st.write(f"{medal} {client[:20]}: {amount:,.0f} ₽")
            
            with top_col2:
                st.markdown("**📦 Топ товары:**")
                for i, (product, amount) in enumerate(summary['top_products'].items()):
                    medal = ["🥇", "🥈", "🥉"][i]
                    st.write(f"{medal} {product[:20]}: {amount:,.0f} ₽")
            
            with top_col3:
                st.markdown("**🗺️ Топ регионы:**")
                for i, (region, amount) in enumerate(summary['top_regions'].items()):
                    medal = ["🥇", "🥈", "🥉"][i]
                    st.write(f"{medal} {region}: {amount:,.0f} ₽")
            
            with top_col4:
                st.markdown("**👨‍💼 Топ менеджеры:**")
                for i, (manager, amount) in enumerate(summary['top_managers'].items()):
                    medal = ["🥇", "🥈", "🥉"][i]
                    st.write(f"{medal} {manager[:20]}: {amount:,.0f} ₽")
            
            # Экспорт исполнительной сводки
            st.markdown("### 📋 Экспорт сводки")
            
            summary_json = json.dumps(summary, ensure_ascii=False, indent=2, default=str)
            
            col_export1, col_export2 = st.columns(2)
            
            with col_export1:
                st.download_button(
                    "📥 Скачать исполнительную сводку (JSON)",
                    data=summary_json,
                    file_name=f"executive_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col_export2:
                # Создание PDF-подобного отчета в HTML
                html_report = f"""
                <html>
                <head><title>Исполнительная сводка Оримэкс</title></head>
                <body style="font-family: Arial; margin: 40px;">
                    <h1>📊 Исполнительная сводка Оримэкс</h1>
                    <p><strong>Период:</strong> {summary['period']}</p>
                    <h2>Ключевые показатели</h2>
                    <ul>
                        <li>Общая выручка: {summary['total_revenue']:,.0f} ₽</li>
                        <li>Количество заказов: {summary['total_orders']:,}</li>
                        <li>Уникальных клиентов: {summary['unique_customers']:,}</li>
                        <li>Средний чек: {summary['avg_order_value']:,.0f} ₽</li>
                        <li>Рост выручки: {summary['revenue_growth']:+.1f}%</li>
                    </ul>
                    <h2>Топ-3 в каждой категории</h2>
                    <h3>Клиенты:</h3>
                    <ol>{"".join([f"<li>{k}: {v:,.0f} ₽</li>" for k, v in list(summary['top_customers'].items())[:3]])}</ol>
                    <h3>Товары:</h3>
                    <ol>{"".join([f"<li>{k}: {v:,.0f} ₽</li>" for k, v in list(summary['top_products'].items())[:3]])}</ol>
                    <h3>Регионы:</h3>
                    <ol>{"".join([f"<li>{k}: {v:,.0f} ₽</li>" for k, v in list(summary['top_regions'].items())[:3]])}</ol>
                </body>
                </html>
                """
                
                st.download_button(
                    "📄 Скачать HTML отчет",
                    data=html_report,
                    file_name=f"executive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html"
                )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Футер с космическим дизайном
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #ff006e 0%, #8338ec 50%, #3a86ff 100%);
        padding: 3rem;
        border-radius: 25px;
        text-align: center;
        color: white;
        margin-top: 3rem;
        box-shadow: 0 0 50px rgba(255, 0, 110, 0.5);
    ">
        <h2 style="font-family: 'Orbitron', monospace;">🌟 МЕГА-ДАШБОРД ОРИМЭКС</h2>
        <p style="font-size: 1.2rem;">Абсолютный максимум аналитических возможностей</p>
        <p>🚀 Версия: MEGA v4.0 | 📊 Записей: {len(df):,} | 🕐 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
        <p style="opacity: 0.8;">Создано с использованием передовых технологий AI и Data Science</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
