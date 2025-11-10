#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Супер-продвинутый дашборд с AI-аналитикой для заказов Оримэкс
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
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# Настройка страницы
st.set_page_config(
    page_title="🚀 AI-Дашборд Оримэкс",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Темная тема и продвинутые стили
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .main {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        color: white;
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-size: 4rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 3rem;
        background: linear-gradient(45deg, #00f5ff, #ff00ff, #ffff00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(0, 245, 255, 0.5);
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { filter: drop-shadow(0 0 20px #00f5ff); }
        to { filter: drop-shadow(0 0 30px #ff00ff); }
    }
    
    .ai-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        margin: 1rem 0;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .prediction-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 15px 35px rgba(0,0,0,0.2);
    }
    
    .stSelectbox > div > div {
        background-color: rgba(255,255,255,0.1);
        border-radius: 10px;
    }
    
    .stMultiSelect > div > div {
        background-color: rgba(255,255,255,0.1);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_data():
    """Загрузка данных из базы данных"""
    try:
        conn = sqlite3.connect('orimex_orders.db')
        
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
        df['month'] = df['order_date'].dt.to_period('M')
        df['week'] = df['order_date'].dt.to_period('W')
        df['day_of_week'] = df['order_date'].dt.day_name()
        df['quarter'] = df['order_date'].dt.to_period('Q')
        df['hour'] = df['order_date'].dt.hour
        
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()

def create_ai_anomaly_detection(df):
    """AI-детекция аномалий в заказах"""
    
    # Подготавливаем данные для модели
    features_df = df.groupby('order_date').agg({
        'amount': ['sum', 'mean', 'std', 'count'],
        'quantity': ['sum', 'mean']
    }).fillna(0)
    
    features_df.columns = ['amount_sum', 'amount_mean', 'amount_std', 'order_count', 'quantity_sum', 'quantity_mean']
    
    # Isolation Forest для детекции аномалий
    isolation_forest = IsolationForest(contamination=0.1, random_state=42)
    anomalies = isolation_forest.fit_predict(features_df)
    
    features_df['anomaly'] = anomalies
    features_df['date'] = features_df.index
    
    # Визуализация аномалий
    fig = go.Figure()
    
    # Нормальные дни
    normal_days = features_df[features_df['anomaly'] == 1]
    fig.add_trace(go.Scatter(
        x=normal_days['date'],
        y=normal_days['amount_sum'],
        mode='markers',
        name='Обычные дни',
        marker=dict(color='blue', size=8)
    ))
    
    # Аномальные дни
    anomaly_days = features_df[features_df['anomaly'] == -1]
    fig.add_trace(go.Scatter(
        x=anomaly_days['date'],
        y=anomaly_days['amount_sum'],
        mode='markers',
        name='Аномалии',
        marker=dict(color='red', size=12, symbol='diamond')
    ))
    
    fig.update_layout(
        title="🤖 AI-детекция аномалий в продажах",
        xaxis_title="Дата",
        yaxis_title="Сумма продаж",
        height=500
    )
    
    return fig, len(anomaly_days)

def create_customer_segmentation(df):
    """AI-сегментация клиентов"""
    
    # RFM анализ (Recency, Frequency, Monetary)
    current_date = df['order_date'].max()
    
    rfm = df.groupby('buyer').agg({
        'order_date': lambda x: (current_date - x.max()).days,  # Recency
        'id': 'count',  # Frequency
        'amount': 'sum'  # Monetary
    }).reset_index()
    
    rfm.columns = ['buyer', 'recency', 'frequency', 'monetary']
    
    # Нормализация для кластеризации
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm[['recency', 'frequency', 'monetary']])
    
    # K-means кластеризация
    kmeans = KMeans(n_clusters=4, random_state=42)
    rfm['cluster'] = kmeans.fit_predict(rfm_scaled)
    
    # Назначаем названия кластерам
    cluster_names = {
        0: '🌟 VIP клиенты',
        1: '💎 Лояльные клиенты', 
        2: '⚠️ Группа риска',
        3: '🆕 Новые клиенты'
    }
    
    rfm['cluster_name'] = rfm['cluster'].map(cluster_names)
    
    # 3D визуализация сегментов
    fig = go.Figure(data=go.Scatter3d(
        x=rfm['recency'],
        y=rfm['frequency'],
        z=rfm['monetary'],
        mode='markers',
        marker=dict(
            size=5,
            color=rfm['cluster'],
            colorscale='viridis',
            showscale=True,
            colorbar=dict(title="Сегменты")
        ),
        text=rfm['buyer'],
        hovertemplate='<b>%{text}</b><br>' +
                     'Дней с покупки: %{x}<br>' +
                     'Частота: %{y}<br>' +
                     'Сумма: %{z:,.0f} ₽<extra></extra>'
    ))
    
    fig.update_layout(
        title="🎯 3D сегментация клиентов (RFM анализ)",
        scene=dict(
            xaxis_title='Recency (дни)',
            yaxis_title='Frequency (заказы)',
            zaxis_title='Monetary (руб.)'
        ),
        height=600
    )
    
    return fig, rfm

def create_ml_sales_prediction(df):
    """Машинное обучение для предсказания продаж"""
    
    # Подготовка признаков
    daily_data = df.groupby('order_date').agg({
        'amount': 'sum',
        'quantity': 'sum',
        'id': 'count'
    }).reset_index()
    
    # Добавляем временные признаки
    daily_data['day_of_year'] = daily_data['order_date'].dt.dayofyear
    daily_data['month'] = daily_data['order_date'].dt.month
    daily_data['day_of_week'] = daily_data['order_date'].dt.dayofweek
    daily_data['is_weekend'] = daily_data['day_of_week'].isin([5, 6]).astype(int)
    
    # Лаговые признаки
    daily_data['amount_lag1'] = daily_data['amount'].shift(1)
    daily_data['amount_lag7'] = daily_data['amount'].shift(7)
    daily_data['amount_ma7'] = daily_data['amount'].rolling(window=7).mean()
    
    # Убираем NaN
    ml_data = daily_data.dropna()
    
    # Признаки и цель
    feature_columns = ['day_of_year', 'month', 'day_of_week', 'is_weekend', 
                      'amount_lag1', 'amount_lag7', 'amount_ma7', 'quantity', 'id']
    X = ml_data[feature_columns]
    y = ml_data['amount']
    
    # Разделяем на train/test
    split_date = ml_data['order_date'].quantile(0.8)
    train_mask = ml_data['order_date'] <= split_date
    
    X_train, X_test = X[train_mask], X[~train_mask]
    y_train, y_test = y[train_mask], y[~train_mask]
    
    # Обучаем Random Forest
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    
    # Предсказания
    y_pred = rf_model.predict(X_test)
    
    # Важность признаков
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    # Визуализация предсказаний
    fig_pred = go.Figure()
    
    test_dates = ml_data[~train_mask]['order_date']
    
    fig_pred.add_trace(go.Scatter(
        x=test_dates,
        y=y_test,
        mode='lines+markers',
        name='Реальные продажи',
        line=dict(color='blue')
    ))
    
    fig_pred.add_trace(go.Scatter(
        x=test_dates,
        y=y_pred,
        mode='lines+markers',
        name='ML предсказания',
        line=dict(color='red', dash='dash')
    ))
    
    fig_pred.update_layout(
        title="🤖 Машинное обучение: предсказание продаж",
        xaxis_title="Дата",
        yaxis_title="Сумма продаж",
        height=500
    )
    
    # График важности признаков
    fig_importance = px.bar(
        feature_importance,
        x='importance',
        y='feature',
        orientation='h',
        title="🎯 Важность признаков для предсказания продаж"
    )
    fig_importance.update_layout(height=400)
    
    # Точность модели
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
    
    return fig_pred, fig_importance, mape

def create_network_analysis(df):
    """Сетевой анализ связей клиент-товар"""
    
    # Создаем матрицу связей
    product_client_matrix = df.pivot_table(
        index='buyer', 
        columns='product_name', 
        values='amount', 
        aggfunc='sum', 
        fill_value=0
    )
    
    # Топ связи
    top_combinations = df.groupby(['buyer', 'product_name'])['amount'].sum().reset_index()
    top_combinations = top_combinations.sort_values('amount', ascending=False).head(20)
    
    # Создаем сетевой граф
    fig = go.Figure()
    
    # Добавляем узлы и связи
    for idx, row in top_combinations.iterrows():
        # Размер узла пропорционален сумме
        size = np.sqrt(row['amount'] / 10000)
        
        fig.add_trace(go.Scatter(
            x=[idx, idx + 0.5],
            y=[0, 1],
            mode='lines+markers+text',
            line=dict(width=size/2, color='rgba(100,100,100,0.5)'),
            marker=dict(size=[size, size/2], color=['blue', 'red']),
            text=[row['buyer'][:20], row['product_name'][:15]],
            textposition='middle center',
            name=f"{row['amount']:,.0f} ₽",
            showlegend=False
        ))
    
    fig.update_layout(
        title="🕸️ Сетевой анализ: связи клиент-товар",
        xaxis_title="Связи (топ-20 по сумме)",
        yaxis_title="Клиенты → Товары",
        height=600,
        showlegend=False
    )
    
    return fig

def create_sentiment_analysis(df):
    """Анализ 'настроения' продаж"""
    
    # Создаем индекс настроения на основе отклонений от среднего
    daily_sales = df.groupby('order_date')['amount'].sum().reset_index()
    daily_sales['ma_7'] = daily_sales['amount'].rolling(window=7).mean()
    daily_sales['ma_30'] = daily_sales['amount'].rolling(window=30).mean()
    
    # Индекс настроения
    daily_sales['sentiment'] = (
        (daily_sales['amount'] - daily_sales['ma_30']) / daily_sales['ma_30'] * 100
    )
    
    # Классификация настроения
    daily_sales['sentiment_category'] = pd.cut(
        daily_sales['sentiment'], 
        bins=[-np.inf, -20, -5, 5, 20, np.inf],
        labels=['😱 Очень плохо', '😟 Плохо', '😐 Нейтрально', '😊 Хорошо', '🚀 Отлично']
    )
    
    # Визуализация
    fig = go.Figure()
    
    colors = {'😱 Очень плохо': 'red', '😟 Плохо': 'orange', 
              '😐 Нейтрально': 'gray', '😊 Хорошо': 'lightgreen', '🚀 Отлично': 'green'}
    
    for category in daily_sales['sentiment_category'].cat.categories:
        data = daily_sales[daily_sales['sentiment_category'] == category]
        if not data.empty:
            fig.add_trace(go.Scatter(
                x=data['order_date'],
                y=data['sentiment'],
                mode='markers',
                name=category,
                marker=dict(color=colors[category], size=8)
            ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="white")
    fig.update_layout(
        title="😊 Индекс настроения продаж (отклонение от тренда)",
        xaxis_title="Дата",
        yaxis_title="Индекс настроения (%)",
        height=500
    )
    
    return fig, daily_sales['sentiment_category'].value_counts()

def create_competitive_analysis(df):
    """Конкурентный анализ товаров"""
    
    # Анализ конкурентоспособности по категориям
    category_performance = df.groupby(['category', 'product_name']).agg({
        'amount': 'sum',
        'quantity': 'sum',
        'id': 'count'
    }).reset_index()
    
    # Рассчитываем долю рынка внутри категории
    category_totals = category_performance.groupby('category')['amount'].transform('sum')
    category_performance['market_share'] = category_performance['amount'] / category_totals * 100
    
    # Создаем bubble chart
    fig = px.scatter(
        category_performance[category_performance['market_share'] > 1],  # Только значимые товары
        x='quantity',
        y='amount',
        size='market_share',
        color='category',
        hover_name='product_name',
        title="🥊 Конкурентный анализ товаров (размер = доля рынка в категории)",
        labels={'quantity': 'Объем продаж (шт.)', 'amount': 'Выручка (руб.)'}
    )
    
    fig.update_layout(height=600)
    
    return fig, category_performance

def create_profitability_analysis(df):
    """Анализ прибыльности (симуляция)"""
    
    # Симулируем маржинальность по категориям
    margin_rates = {
        'Столы': 0.35,
        'Стулья': 0.42,
        'Кресла': 0.38,
        'Диваны': 0.30,
        'Шкафы': 0.25
    }
    
    # Добавляем маржу по умолчанию для неизвестных категорий
    df['margin_rate'] = df['category'].map(margin_rates).fillna(0.35)
    df['profit'] = df['amount'] * df['margin_rate']
    
    # Анализ прибыльности по регионам
    profitability = df.groupby('region').agg({
        'amount': 'sum',
        'profit': 'sum',
        'id': 'count'
    }).reset_index()
    
    profitability['profit_margin'] = profitability['profit'] / profitability['amount'] * 100
    profitability['profit_per_order'] = profitability['profit'] / profitability['id']
    
    # Bubble chart прибыльности
    fig = px.scatter(
        profitability.head(20),
        x='amount',
        y='profit',
        size='id',
        color='profit_margin',
        hover_name='region',
        title="💰 Анализ прибыльности по регионам",
        labels={'amount': 'Выручка', 'profit': 'Прибыль'},
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(height=600)
    
    return fig, profitability

def create_advanced_forecasting(df):
    """Продвинутое прогнозирование с сезонностью"""
    
    # Подготовка данных
    daily_sales = df.groupby('order_date')['amount'].sum().reset_index()
    daily_sales = daily_sales.sort_values('order_date')
    
    # Добавляем сезонные компоненты
    daily_sales['trend'] = np.arange(len(daily_sales))
    daily_sales['month'] = daily_sales['order_date'].dt.month
    daily_sales['day_of_week'] = daily_sales['order_date'].dt.dayofweek
    
    # Создаем циклические признаки
    daily_sales['month_sin'] = np.sin(2 * np.pi * daily_sales['month'] / 12)
    daily_sales['month_cos'] = np.cos(2 * np.pi * daily_sales['month'] / 12)
    daily_sales['dow_sin'] = np.sin(2 * np.pi * daily_sales['day_of_week'] / 7)
    daily_sales['dow_cos'] = np.cos(2 * np.pi * daily_sales['day_of_week'] / 7)
    
    # Обучаем модель
    features = ['trend', 'month_sin', 'month_cos', 'dow_sin', 'dow_cos']
    X = daily_sales[features].fillna(0)
    y = daily_sales['amount']
    
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)
    
    # Прогноз на 60 дней
    future_dates = pd.date_range(
        start=daily_sales['order_date'].max() + timedelta(days=1),
        periods=60,
        freq='D'
    )
    
    future_df = pd.DataFrame({'order_date': future_dates})
    future_df['trend'] = np.arange(len(daily_sales), len(daily_sales) + 60)
    future_df['month'] = future_df['order_date'].dt.month
    future_df['day_of_week'] = future_df['order_date'].dt.dayofweek
    future_df['month_sin'] = np.sin(2 * np.pi * future_df['month'] / 12)
    future_df['month_cos'] = np.cos(2 * np.pi * future_df['month'] / 12)
    future_df['dow_sin'] = np.sin(2 * np.pi * future_df['day_of_week'] / 7)
    future_df['dow_cos'] = np.cos(2 * np.pi * future_df['day_of_week'] / 7)
    
    future_predictions = model.predict(future_df[features])
    
    # Визуализация
    fig = go.Figure()
    
    # Исторические данные
    fig.add_trace(go.Scatter(
        x=daily_sales['order_date'],
        y=daily_sales['amount'],
        mode='lines',
        name='Исторические данные',
        line=dict(color='blue')
    ))
    
    # Прогноз
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=future_predictions,
        mode='lines',
        name='ML прогноз (60 дней)',
        line=dict(color='red', dash='dash')
    ))
    
    # Доверительный интервал
    std_pred = np.std(y - model.predict(X))
    upper_bound = future_predictions + 1.96 * std_pred
    lower_bound = future_predictions - 1.96 * std_pred
    
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=upper_bound,
        fill=None,
        mode='lines',
        line_color='rgba(0,0,0,0)',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=lower_bound,
        fill='tonexty',
        mode='lines',
        line_color='rgba(0,0,0,0)',
        name='Доверительный интервал',
        fillcolor='rgba(255,0,0,0.2)'
    ))
    
    fig.update_layout(
        title="🔮 Продвинутое ML-прогнозирование с сезонностью",
        xaxis_title="Дата",
        yaxis_title="Сумма продаж",
        height=600
    )
    
    return fig, future_predictions.sum(), feature_importance

def main():
    # Заголовок
    st.markdown('<h1 class="main-header">🚀 AI-Дашборд анализа заказов Оримэкс</h1>', unsafe_allow_html=True)
    
    # Загрузка данных
    with st.spinner('🤖 Загрузка данных и инициализация AI моделей...'):
        df = load_data()
    
    if df.empty:
        st.error("❌ Не удалось загрузить данные. Убедитесь, что база данных создана.")
        return
    
    # Основные метрики
    total_revenue = df['amount'].sum()
    total_orders = len(df)
    avg_order = df['amount'].mean()
    unique_customers = df['buyer'].nunique()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h2>💰 {total_revenue:,.0f} ₽</h2>
            <p>Общая выручка</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h2>🛒 {total_orders:,}</h2>
            <p>Всего заказов</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h2>📊 {avg_order:,.0f} ₽</h2>
            <p>Средний заказ</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h2>👥 {unique_customers:,}</h2>
            <p>Уникальных клиентов</p>
        </div>
        """, unsafe_allow_html=True)
    
    # AI-анализ
    st.markdown("## 🤖 AI-Аналитика")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🤖 Детекция аномалий",
        "🎯 Сегментация клиентов", 
        "🔮 ML-прогнозирование",
        "🕸️ Сетевой анализ",
        "😊 Анализ настроения",
        "💰 Анализ прибыльности"
    ])
    
    with tab1:
        st.subheader("🤖 AI-детекция аномалий")
        fig_anomaly, anomaly_count = create_ai_anomaly_detection(df)
        st.plotly_chart(fig_anomaly, width='stretch')
        
        if anomaly_count > 0:
            st.warning(f"⚠️ Обнаружено {anomaly_count} аномальных дней в продажах")
        else:
            st.success("✅ Аномалий в продажах не обнаружено")
    
    with tab2:
        st.subheader("🎯 AI-сегментация клиентов")
        fig_segments, rfm_data = create_customer_segmentation(df)
        st.plotly_chart(fig_segments, width='stretch')
        
        # Статистика по сегментам
        segment_stats = rfm_data['cluster_name'].value_counts()
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**📊 Распределение клиентов по сегментам:**")
            for segment, count in segment_stats.items():
                st.write(f"• {segment}: {count} клиентов ({count/len(rfm_data)*100:.1f}%)")
        
        with col2:
            # Средние значения по сегментам
            segment_means = rfm_data.groupby('cluster_name')[['recency', 'frequency', 'monetary']].mean()
            st.write("**📈 Средние характеристики сегментов:**")
            st.dataframe(segment_means.round(0))
    
    with tab3:
        st.subheader("🔮 Машинное обучение: прогнозирование")
        fig_ml, fig_importance, accuracy = create_ml_sales_prediction(df)
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_ml, width='stretch')
        with col2:
            st.plotly_chart(fig_importance, width='stretch')
        
        st.markdown(f"""
        <div class="prediction-box">
            <h3>🎯 Точность модели: {100-accuracy:.1f}%</h3>
            <p>Модель Random Forest обучена на исторических данных и учитывает сезонность, тренды и лаговые признаки</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab4:
        st.subheader("🕸️ Сетевой анализ связей")
        fig_network = create_network_analysis(df)
        st.plotly_chart(fig_network, width='stretch')
        
        st.info("💡 График показывает самые сильные связи между клиентами и товарами по объему продаж")
    
    with tab5:
        st.subheader("😊 Анализ настроения продаж")
        fig_sentiment, sentiment_stats = create_sentiment_analysis(df)
        st.plotly_chart(fig_sentiment, width='stretch')
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**📊 Распределение настроения:**")
            for mood, count in sentiment_stats.items():
                st.write(f"• {mood}: {count} дней")
        
        with col2:
            # Текущее настроение
            latest_sentiment = sentiment_stats.index[0] if len(sentiment_stats) > 0 else "😐 Нейтрально"
            st.markdown(f"""
            <div class="prediction-box">
                <h3>Текущее настроение рынка:</h3>
                <h2>{latest_sentiment}</h2>
            </div>
            """, unsafe_allow_html=True)
    
    with tab6:
        st.subheader("💰 Анализ прибыльности")
        fig_profit, profit_data = create_profitability_analysis(df)
        st.plotly_chart(fig_profit, width='stretch')
        
        # Конкурентный анализ
        fig_competitive, competitive_data = create_competitive_analysis(df)
        st.plotly_chart(fig_competitive, width='stretch')
        
        # Топ прибыльные регионы
        top_profitable = profit_data.sort_values('profit', ascending=False).head(10)
        st.subheader("🏆 Топ-10 прибыльных регионов")
        st.dataframe(
            top_profitable[['region', 'profit', 'profit_margin', 'profit_per_order']].style.format({
                'profit': '{:,.0f} ₽',
                'profit_margin': '{:.1f}%',
                'profit_per_order': '{:,.0f} ₽'
            }),
            width='stretch'
        )

if __name__ == "__main__":
    main()
