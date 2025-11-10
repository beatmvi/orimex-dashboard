#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расширенный интерактивный дашборд для анализа заказов Оримэкс
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
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Настройка страницы
st.set_page_config(
    page_title="📊 Расширенный дашборд Оримэкс",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Кастомные стили
st.markdown("""
<style>
    .main-header {
        font-size: 3.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        color: white;
    }
    .kpi-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stAlert {
        border-radius: 10px;
    }
    .css-1d391kg {
        padding-top: 1rem;
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
        
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()

@st.cache_data
def get_advanced_stats(df):
    """Расширенная статистика"""
    if df.empty:
        return {}
    
    return {
        'total_orders': len(df),
        'total_amount': df['amount'].sum(),
        'avg_order_amount': df['amount'].mean(),
        'median_order_amount': df['amount'].median(),
        'std_order_amount': df['amount'].std(),
        'unique_products': df['product_name'].nunique(),
        'unique_contractors': df['head_contractor'].nunique(),
        'unique_regions': df['region'].nunique(),
        'unique_managers': df['manager'].nunique(),
        'date_range': (df['order_date'].min(), df['order_date'].max()),
        'top_order': df['amount'].max(),
        'conversion_rate': len(df[df['amount'] > df['amount'].mean()]) / len(df) * 100,
        'growth_rate': calculate_growth_rate(df),
        'seasonal_factor': calculate_seasonality(df)
    }

def calculate_growth_rate(df):
    """Расчет темпа роста"""
    monthly = df.groupby(df['order_date'].dt.to_period('M'))['amount'].sum().reset_index()
    if len(monthly) < 2:
        return 0
    
    monthly['month_num'] = range(len(monthly))
    if len(monthly) > 1:
        correlation = monthly['month_num'].corr(monthly['amount'])
        return correlation * 100
    return 0

def calculate_seasonality(df):
    """Расчет сезонности"""
    monthly = df.groupby(df['order_date'].dt.month)['amount'].mean()
    return monthly.std() / monthly.mean() * 100

def create_advanced_time_series(df):
    """Расширенный анализ временных рядов"""
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Сумма заказов по дням', 'Количество заказов по дням',
            'Средняя сумма заказа', 'Тренд роста',
            'Распределение по дням недели', 'Сезонность по месяцам'
        ),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}],
               [{"type": "bar"}, {"type": "bar"}]],
        vertical_spacing=0.08
    )
    
    # Подготовка данных
    daily_stats = df.groupby('order_date').agg({
        'amount': ['sum', 'mean', 'count']
    }).reset_index()
    daily_stats.columns = ['date', 'total_amount', 'avg_amount', 'order_count']
    
    # 1. Сумма по дням с трендом
    fig.add_trace(
        go.Scatter(x=daily_stats['date'], y=daily_stats['total_amount'],
                  mode='lines+markers', name='Сумма', line=dict(color='#1f77b4')),
        row=1, col=1
    )
    
    # Добавляем тренд
    x_numeric = np.arange(len(daily_stats))
    z = np.polyfit(x_numeric, daily_stats['total_amount'], 1)
    trend_line = np.poly1d(z)(x_numeric)
    
    fig.add_trace(
        go.Scatter(x=daily_stats['date'], y=trend_line,
                  mode='lines', name='Тренд', line=dict(color='red', dash='dash')),
        row=1, col=1
    )
    
    # 2. Количество заказов
    fig.add_trace(
        go.Scatter(x=daily_stats['date'], y=daily_stats['order_count'],
                  mode='lines+markers', name='Количество', line=dict(color='#ff7f0e')),
        row=1, col=2
    )
    
    # 3. Средняя сумма заказа
    fig.add_trace(
        go.Scatter(x=daily_stats['date'], y=daily_stats['avg_amount'],
                  mode='lines+markers', name='Средняя сумма', line=dict(color='#2ca02c')),
        row=2, col=1
    )
    
    # 4. Кумулятивный тренд
    daily_stats['cumulative'] = daily_stats['total_amount'].cumsum()
    fig.add_trace(
        go.Scatter(x=daily_stats['date'], y=daily_stats['cumulative'],
                  mode='lines', name='Накопительный итог', fill='tonexty', line=dict(color='#9467bd')),
        row=2, col=2
    )
    
    # 5. По дням недели
    dow_stats = df.groupby('day_of_week')['amount'].sum().reindex([
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ])
    
    fig.add_trace(
        go.Bar(x=['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'], y=dow_stats.values,
               name='По дням недели', marker_color='#17becf'),
        row=3, col=1
    )
    
    # 6. Сезонность по месяцам
    monthly_stats = df.groupby(df['order_date'].dt.month)['amount'].mean()
    month_names = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 
                   'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
    
    fig.add_trace(
        go.Bar(x=[month_names[i-1] for i in monthly_stats.index], y=monthly_stats.values,
               name='Средняя сумма по месяцам', marker_color='#bcbd22'),
        row=3, col=2
    )
    
    fig.update_layout(height=1000, showlegend=False, title_text="📈 Расширенный анализ временных рядов")
    return fig

def create_abc_analysis(df):
    """ABC анализ товаров и клиентов"""
    
    # ABC анализ товаров
    product_stats = df.groupby('product_name')['amount'].sum().sort_values(ascending=False)
    product_stats_cum = product_stats.cumsum() / product_stats.sum() * 100
    
    products_a = product_stats_cum[product_stats_cum <= 80].index
    products_b = product_stats_cum[(product_stats_cum > 80) & (product_stats_cum <= 95)].index
    products_c = product_stats_cum[product_stats_cum > 95].index
    
    # ABC анализ клиентов
    client_stats = df.groupby('buyer')['amount'].sum().sort_values(ascending=False)
    client_stats_cum = client_stats.cumsum() / client_stats.sum() * 100
    
    clients_a = client_stats_cum[client_stats_cum <= 80].index
    clients_b = client_stats_cum[(client_stats_cum > 80) & (client_stats_cum <= 95)].index
    clients_c = client_stats_cum[client_stats_cum > 95].index
    
    return {
        'products': {'A': products_a, 'B': products_b, 'C': products_c},
        'clients': {'A': clients_a, 'B': clients_b, 'C': clients_c},
        'product_stats': product_stats,
        'client_stats': client_stats
    }

def create_correlation_heatmap(df):
    """Корреляционная тепловая карта"""
    
    # Подготавливаем числовые данные для корреляции
    correlation_data = df.pivot_table(
        index='order_date', 
        columns='category', 
        values='amount', 
        aggfunc='sum', 
        fill_value=0
    )
    
    correlation_matrix = correlation_data.corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix.values,
        x=correlation_matrix.columns,
        y=correlation_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=np.round(correlation_matrix.values, 2),
        texttemplate="%{text}",
        textfont={"size": 12},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title="🔥 Корреляция продаж между категориями товаров",
        xaxis_title="Категории",
        yaxis_title="Категории",
        height=600
    )
    
    return fig

def create_sales_forecast(df):
    """Прогнозирование продаж"""
    
    # Подготовка данных для прогноза
    daily_sales = df.groupby('order_date')['amount'].sum().reset_index()
    daily_sales['days'] = (daily_sales['order_date'] - daily_sales['order_date'].min()).dt.days
    
    # Простая линейная регрессия
    X = daily_sales['days'].values.reshape(-1, 1)
    y = daily_sales['amount'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Прогноз на следующие 30 дней
    future_days = np.arange(daily_sales['days'].max() + 1, daily_sales['days'].max() + 31)
    future_predictions = model.predict(future_days.reshape(-1, 1))
    
    future_dates = [daily_sales['order_date'].max() + timedelta(days=i) for i in range(1, 31)]
    
    fig = go.Figure()
    
    # Исторические данные
    fig.add_trace(go.Scatter(
        x=daily_sales['order_date'],
        y=daily_sales['amount'],
        mode='lines+markers',
        name='Исторические данные',
        line=dict(color='#1f77b4')
    ))
    
    # Прогноз
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=future_predictions,
        mode='lines+markers',
        name='Прогноз на 30 дней',
        line=dict(color='red', dash='dash')
    ))
    
    fig.update_layout(
        title="🔮 Прогноз продаж на 30 дней",
        xaxis_title="Дата",
        yaxis_title="Сумма продаж (руб.)",
        height=500
    )
    
    return fig, future_predictions.sum()

def create_manager_performance(df):
    """Анализ эффективности менеджеров"""
    
    manager_stats = df.groupby('manager').agg({
        'amount': ['sum', 'mean', 'count'],
        'buyer': 'nunique'
    }).round(2)
    
    manager_stats.columns = ['Общая сумма', 'Средний заказ', 'Количество заказов', 'Уникальных клиентов']
    manager_stats = manager_stats.reset_index()
    manager_stats = manager_stats.sort_values('Общая сумма', ascending=False)
    
    # Эффективность = Общая сумма / Количество заказов * Уникальных клиентов
    manager_stats['Эффективность'] = (
        manager_stats['Общая сумма'] / 
        manager_stats['Количество заказов'] * 
        manager_stats['Уникальных клиентов'] / 1000
    ).round(2)
    
    fig = px.scatter(
        manager_stats.head(20),
        x='Количество заказов',
        y='Средний заказ',
        size='Общая сумма',
        color='Эффективность',
        hover_name='manager',
        title="💼 Эффективность менеджеров (размер = общая сумма, цвет = эффективность)",
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(height=600)
    return fig, manager_stats

def create_geographic_analysis(df):
    """Географический анализ продаж"""
    
    region_stats = df.groupby('region').agg({
        'amount': ['sum', 'mean', 'count'],
        'buyer': 'nunique'
    }).reset_index()
    
    region_stats.columns = ['Регион', 'Общая сумма', 'Средний заказ', 'Количество заказов', 'Клиентов']
    region_stats = region_stats.sort_values('Общая сумма', ascending=False)
    
    # Создаем карту-дерево
    fig_treemap = px.treemap(
        region_stats.head(20),
        path=['Регион'],
        values='Общая сумма',
        color='Средний заказ',
        title="🗺️ Карта продаж по регионам",
        color_continuous_scale='plasma'
    )
    
    # Пузырьковая диаграмма
    fig_bubble = px.scatter(
        region_stats.head(15),
        x='Количество заказов',
        y='Средний заказ',
        size='Общая сумма',
        color='Клиентов',
        hover_name='Регион',
        title="🎯 Анализ регионов: объем vs эффективность",
        color_continuous_scale='viridis'
    )
    
    fig_bubble.update_layout(height=600)
    
    return fig_treemap, fig_bubble, region_stats

def create_product_portfolio_analysis(df):
    """Анализ товарного портфеля"""
    
    # Матрица BCG (Boston Consulting Group)
    product_stats = df.groupby(['product_name', 'category']).agg({
        'amount': 'sum',
        'quantity': 'sum'
    }).reset_index()
    
    # Рост = изменение продаж по месяцам
    growth_data = df.groupby(['product_name', df['order_date'].dt.to_period('M')])['amount'].sum().reset_index()
    growth_rates = growth_data.groupby('product_name')['amount'].apply(
        lambda x: (x.iloc[-1] - x.iloc[0]) / x.iloc[0] * 100 if len(x) > 1 and x.iloc[0] > 0 else 0
    ).reset_index()
    growth_rates.columns = ['product_name', 'growth_rate']
    
    # Доля рынка = доля от общих продаж
    total_sales = product_stats['amount'].sum()
    product_stats['market_share'] = product_stats['amount'] / total_sales * 100
    
    # Объединяем данные
    bcg_data = product_stats.merge(growth_rates, on='product_name', how='left')
    bcg_data['growth_rate'] = bcg_data['growth_rate'].fillna(0)
    
    # Создаем BCG матрицу
    fig = px.scatter(
        bcg_data.head(50),
        x='market_share',
        y='growth_rate',
        size='amount',
        color='category',
        hover_name='product_name',
        title="📊 BCG Матрица товаров (доля рынка vs рост)",
        labels={'market_share': 'Доля рынка (%)', 'growth_rate': 'Темп роста (%)'}
    )
    
    # Добавляем линии разделения BCG
    fig.add_hline(y=bcg_data['growth_rate'].median(), line_dash="dash", line_color="gray")
    fig.add_vline(x=bcg_data['market_share'].median(), line_dash="dash", line_color="gray")
    
    fig.update_layout(height=700)
    
    return fig, bcg_data

def create_cohort_analysis(df):
    """Когортный анализ клиентов"""
    
    # Определяем первую покупку каждого клиента
    df['order_month'] = df['order_date'].dt.to_period('M')
    first_purchase = df.groupby('buyer')['order_month'].min().reset_index()
    first_purchase.columns = ['buyer', 'cohort_month']
    
    # Объединяем с основными данными
    df_cohort = df.merge(first_purchase, on='buyer')
    df_cohort['months_since_first_purchase'] = (
        df_cohort['order_month'] - df_cohort['cohort_month']
    ).apply(lambda x: x.n)
    
    # Создаем когортную таблицу
    cohort_data = df_cohort.groupby(['cohort_month', 'months_since_first_purchase'])['buyer'].nunique().reset_index()
    cohort_table = cohort_data.pivot(index='cohort_month', 
                                    columns='months_since_first_purchase', 
                                    values='buyer')
    
    # Рассчитываем retention rate
    cohort_sizes = first_purchase.groupby('cohort_month')['buyer'].nunique()
    retention_table = cohort_table.divide(cohort_sizes, axis=0)
    
    # Создаем heatmap
    fig = go.Figure(data=go.Heatmap(
        z=retention_table.values,
        x=[f'Месяц {i}' for i in retention_table.columns],
        y=[str(i) for i in retention_table.index],
        colorscale='Blues',
        text=np.round(retention_table.values * 100, 1),
        texttemplate="%{text}%",
        textfont={"size": 10}
    ))
    
    fig.update_layout(
        title="👥 Когортный анализ удержания клиентов (%)",
        xaxis_title="Месяцы с момента первой покупки",
        yaxis_title="Месяц первой покупки",
        height=500
    )
    
    return fig

def create_price_analysis(df):
    """Анализ ценообразования"""
    
    # Распределение цен по категориям
    fig_violin = px.violin(
        df[df['amount'] < df['amount'].quantile(0.95)],  # Убираем выбросы
        x='category',
        y='amount',
        title="🎻 Распределение цен по категориям товаров",
        box=True
    )
    fig_violin.update_layout(height=500)
    
    # Анализ выбросов
    Q1 = df['amount'].quantile(0.25)
    Q3 = df['amount'].quantile(0.75)
    IQR = Q3 - Q1
    outliers = df[(df['amount'] < Q1 - 1.5 * IQR) | (df['amount'] > Q3 + 1.5 * IQR)]
    
    fig_outliers = px.scatter(
        outliers.head(100),
        x='order_date',
        y='amount',
        color='category',
        hover_data=['buyer', 'product_name'],
        title="⚡ Аномальные заказы (выбросы в ценах)"
    )
    fig_outliers.update_layout(height=500)
    
    return fig_violin, fig_outliers, len(outliers)

def create_funnel_analysis(df):
    """Воронка продаж"""
    
    # Создаем воронку по размерам заказов
    bins = [0, 10000, 50000, 100000, 500000, float('inf')]
    labels = ['< 10к', '10-50к', '50-100к', '100-500к', '> 500к']
    
    df['amount_category'] = pd.cut(df['amount'], bins=bins, labels=labels, include_lowest=True)
    funnel_data = df['amount_category'].value_counts().sort_index()
    
    fig = go.Figure(go.Funnel(
        y=funnel_data.index,
        x=funnel_data.values,
        textinfo="value+percent initial",
        marker_color=["deepskyblue", "lightsalmon", "tan", "teal", "silver"]
    ))
    
    fig.update_layout(
        title="🔽 Воронка заказов по размеру сделки",
        height=500
    )
    
    return fig

def create_advanced_kpis(df):
    """Расширенные KPI метрики"""
    
    # Рассчитываем различные KPI
    total_revenue = df['amount'].sum()
    avg_order_value = df['amount'].mean()
    total_orders = len(df)
    unique_customers = df['buyer'].nunique()
    
    # Customer Lifetime Value (упрощенный)
    customer_orders = df.groupby('buyer').agg({
        'amount': 'sum',
        'id': 'count'
    })
    clv = customer_orders['amount'].mean()
    
    # Частота заказов
    days_range = (df['order_date'].max() - df['order_date'].min()).days
    order_frequency = total_orders / days_range if days_range > 0 else 0
    
    # Revenue per customer
    rpc = total_revenue / unique_customers
    
    # Конверсия (процент клиентов с повторными заказами)
    repeat_customers = len(customer_orders[customer_orders['id'] > 1])
    repeat_rate = repeat_customers / unique_customers * 100
    
    return {
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'total_orders': total_orders,
        'unique_customers': unique_customers,
        'clv': clv,
        'order_frequency': order_frequency,
        'rpc': rpc,
        'repeat_rate': repeat_rate
    }

def main():
    # Заголовок
    st.markdown('<h1 class="main-header">📊 Расширенный дашборд анализа заказов Оримэкс</h1>', unsafe_allow_html=True)
    
    # Загрузка данных
    with st.spinner('🔄 Загрузка и обработка данных...'):
        df = load_data()
    
    if df.empty:
        st.error("❌ Не удалось загрузить данные. Убедитесь, что база данных создана.")
        return
    
    # Боковая панель с расширенными фильтрами
    st.sidebar.header("🔧 Расширенные фильтры")
    
    # Фильтр по датам с пресетами
    date_preset = st.sidebar.selectbox(
        "Быстрый выбор периода",
        ["Пользовательский", "Последние 30 дней", "Последние 90 дней", "Текущий месяц", "Предыдущий месяц", "Весь период"]
    )
    
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
    elif date_preset == "Весь период":
        start_date = df['order_date'].min().date()
        end_date = df['order_date'].max().date()
    else:
        date_range = st.sidebar.date_input(
            "Выберите период",
            value=(df['order_date'].min().date(), df['order_date'].max().date()),
            min_value=df['order_date'].min().date(),
            max_value=df['order_date'].max().date()
        )
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = df['order_date'].min().date()
            end_date = df['order_date'].max().date()
    
    # Дополнительные фильтры
    regions = ['Все'] + sorted(df['region'].unique().tolist())
    selected_regions = st.sidebar.multiselect("Регионы", regions, default=['Все'])
    
    categories = ['Все'] + sorted(df['category'].unique().tolist())
    selected_categories = st.sidebar.multiselect("Категории товаров", categories, default=['Все'])
    
    managers = ['Все'] + sorted(df['manager'].unique().tolist())
    selected_managers = st.sidebar.multiselect("Менеджеры", managers, default=['Все'])
    
    # Фильтр по размеру заказа
    amount_range = st.sidebar.slider(
        "Размер заказа (руб.)",
        min_value=int(df['amount'].min()),
        max_value=int(df['amount'].max()),
        value=(int(df['amount'].min()), int(df['amount'].quantile(0.95))),
        step=1000
    )
    
    # Применение фильтров
    filtered_df = df.copy()
    
    # Фильтр по датам
    filtered_df = filtered_df[
        (filtered_df['order_date'].dt.date >= start_date) & 
        (filtered_df['order_date'].dt.date <= end_date)
    ]
    
    # Фильтр по регионам
    if 'Все' not in selected_regions and selected_regions:
        filtered_df = filtered_df[filtered_df['region'].isin(selected_regions)]
    
    # Фильтр по категориям
    if 'Все' not in selected_categories and selected_categories:
        filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]
    
    # Фильтр по менеджерам
    if 'Все' not in selected_managers and selected_managers:
        filtered_df = filtered_df[filtered_df['manager'].isin(selected_managers)]
    
    # Фильтр по сумме
    filtered_df = filtered_df[
        (filtered_df['amount'] >= amount_range[0]) & 
        (filtered_df['amount'] <= amount_range[1])
    ]
    
    # Расширенные KPI метрики
    kpis = create_advanced_kpis(filtered_df)
    
    # Отображение KPI в красивых карточках
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>💰 Общий доход</h3>
            <h2>{kpis['total_revenue']:,.0f} ₽</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>📊 Средний заказ</h3>
            <h2>{kpis['avg_order_value']:,.0f} ₽</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>🛒 Заказов</h3>
            <h2>{kpis['total_orders']:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>👥 Клиентов</h3>
            <h2>{kpis['unique_customers']:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>🔄 Повторные покупки</h3>
            <h2>{kpis['repeat_rate']:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Дополнительные метрики
    col6, col7, col8 = st.columns(3)
    with col6:
        st.metric("💎 CLV", f"{kpis['clv']:,.0f} ₽", help="Customer Lifetime Value")
    with col7:
        st.metric("📈 RPC", f"{kpis['rpc']:,.0f} ₽", help="Revenue Per Customer")
    with col8:
        st.metric("⚡ Заказов/день", f"{kpis['order_frequency']:.1f}")
    
    # Вкладки для разных видов анализа
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📈 Временные ряды", 
        "🎯 ABC анализ", 
        "🗺️ География", 
        "📊 Портфель товаров",
        "👥 Когорты клиентов",
        "💼 Менеджеры", 
        "🔮 Прогнозы",
        "📋 Детальные данные"
    ])
    
    with tab1:
        st.subheader("📈 Расширенный анализ временных рядов")
        if not filtered_df.empty:
            fig_time = create_advanced_time_series(filtered_df)
            st.plotly_chart(fig_time, width='stretch')
            
            # Корреляционная карта
            if len(filtered_df['category'].unique()) > 1:
                fig_corr = create_correlation_heatmap(filtered_df)
                st.plotly_chart(fig_corr, width='stretch')
    
    with tab2:
        st.subheader("🎯 ABC анализ товаров и клиентов")
        if not filtered_df.empty:
            abc_data = create_abc_analysis(filtered_df)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**📦 ABC товары:**")
                st.write(f"🟢 **A-товары** ({len(abc_data['products']['A'])}): {len(abc_data['products']['A'])/len(abc_data['product_stats'])*100:.1f}% товаров = 80% выручки")
                st.write(f"🟡 **B-товары** ({len(abc_data['products']['B'])}): {len(abc_data['products']['B'])/len(abc_data['product_stats'])*100:.1f}% товаров = 15% выручки")
                st.write(f"🔴 **C-товары** ({len(abc_data['products']['C'])}): {len(abc_data['products']['C'])/len(abc_data['product_stats'])*100:.1f}% товаров = 5% выручки")
                
                if len(abc_data['products']['A']) > 0:
                    st.write("**🏆 Топ A-товары:**")
                    for i, (product, amount) in enumerate(abc_data['product_stats'].head(10).items()):
                        st.write(f"{i+1}. {product}: {amount:,.0f} ₽")
            
            with col2:
                st.write("**👥 ABC клиенты:**")
                st.write(f"🟢 **A-клиенты** ({len(abc_data['clients']['A'])}): {len(abc_data['clients']['A'])/len(abc_data['client_stats'])*100:.1f}% клиентов = 80% выручки")
                st.write(f"🟡 **B-клиенты** ({len(abc_data['clients']['B'])}): {len(abc_data['clients']['B'])/len(abc_data['client_stats'])*100:.1f}% клиентов = 15% выручки")
                st.write(f"🔴 **C-клиенты** ({len(abc_data['clients']['C'])}): {len(abc_data['clients']['C'])/len(abc_data['client_stats'])*100:.1f}% клиентов = 5% выручки")
                
                if len(abc_data['clients']['A']) > 0:
                    st.write("**🏆 Топ A-клиенты:**")
                    for i, (client, amount) in enumerate(abc_data['client_stats'].head(10).items()):
                        st.write(f"{i+1}. {client}: {amount:,.0f} ₽")
    
    with tab3:
        st.subheader("🗺️ Географический анализ")
        if not filtered_df.empty:
            fig_treemap, fig_bubble, region_stats = create_geographic_analysis(filtered_df)
            
            st.plotly_chart(fig_treemap, width='stretch')
            st.plotly_chart(fig_bubble, width='stretch')
            
            # Воронка по регионам
            funnel_fig = create_funnel_analysis(filtered_df)
            st.plotly_chart(funnel_fig, width='stretch')
    
    with tab4:
        st.subheader("📊 Анализ товарного портфеля")
        if not filtered_df.empty:
            fig_bcg, bcg_data = create_product_portfolio_analysis(filtered_df)
            st.plotly_chart(fig_bcg, width='stretch')
            
            st.write("**📋 Интерпретация BCG матрицы:**")
            col1, col2 = st.columns(2)
            with col1:
                st.success("🌟 **Звезды** (правый верх): Высокий рост + Высокая доля")
                st.info("🐄 **Дойные коровы** (правый низ): Низкий рост + Высокая доля")
            with col2:
                st.warning("❓ **Вопросы** (левый верх): Высокий рост + Низкая доля")
                st.error("🐕 **Собаки** (левый низ): Низкий рост + Низкая доля")
            
            # Анализ цен
            fig_violin, fig_outliers, outliers_count = create_price_analysis(filtered_df)
            st.plotly_chart(fig_violin, width='stretch')
            st.plotly_chart(fig_outliers, width='stretch')
            st.info(f"🔍 Найдено {outliers_count} аномальных заказов")
    
    with tab5:
        st.subheader("👥 Когортный анализ клиентов")
        if not filtered_df.empty and len(filtered_df['buyer'].unique()) > 10:
            fig_cohort = create_cohort_analysis(filtered_df)
            st.plotly_chart(fig_cohort, width='stretch')
            
            st.info("💡 **Интерпретация:** Темные области показывают высокий процент удержания клиентов в соответствующие месяцы после первой покупки")
        else:
            st.warning("⚠️ Недостаточно данных для когортного анализа")
    
    with tab6:
        st.subheader("💼 Анализ эффективности менеджеров")
        if not filtered_df.empty:
            fig_managers, manager_stats = create_manager_performance(filtered_df)
            st.plotly_chart(fig_managers, width='stretch')
            
            st.subheader("📊 Рейтинг менеджеров")
            st.dataframe(
                manager_stats.head(15).style.format({
                    'Общая сумма': '{:,.0f} ₽',
                    'Средний заказ': '{:,.0f} ₽',
                    'Эффективность': '{:.2f}'
                }),
                width='stretch'
            )
    
    with tab7:
        st.subheader("🔮 Прогнозирование и тренды")
        if not filtered_df.empty:
            fig_forecast, forecast_sum = create_sales_forecast(filtered_df)
            st.plotly_chart(fig_forecast, width='stretch')
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"📈 Прогноз на следующие 30 дней: **{forecast_sum:,.0f} ₽**")
            with col2:
                growth_rate = calculate_growth_rate(filtered_df)
                if growth_rate > 0:
                    st.success(f"📊 Тренд роста: **+{growth_rate:.1f}%**")
                else:
                    st.error(f"📉 Тренд снижения: **{growth_rate:.1f}%**")
    
    with tab8:
        st.subheader("📋 Детальные данные и экспорт")
        
        # Статистика фильтрации
        st.info(f"📊 Показано **{len(filtered_df):,}** записей из **{len(df):,}** общих")
        
        # Экспорт опции
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if not filtered_df.empty:
                csv = filtered_df.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    label="📥 Скачать данные (CSV)",
                    data=csv,
                    file_name=f"orimex_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if not filtered_df.empty:
                summary_stats = filtered_df.groupby(['region', 'category']).agg({
                    'amount': ['sum', 'mean', 'count']
                }).round(2)
                summary_csv = summary_stats.to_csv(encoding='utf-8')
                st.download_button(
                    label="📊 Сводная статистика (CSV)",
                    data=summary_csv,
                    file_name=f"orimex_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col3:
            if not filtered_df.empty:
                abc_data = create_abc_analysis(filtered_df)
                abc_products = pd.DataFrame({
                    'Товар': abc_data['product_stats'].index,
                    'Сумма': abc_data['product_stats'].values
                })
                abc_csv = abc_products.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    label="🎯 ABC анализ (CSV)",
                    data=abc_csv,
                    file_name=f"orimex_abc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        # Детальная таблица с поиском
        search_term = st.text_input("🔍 Поиск по данным:", placeholder="Введите название товара, клиента или регион...")
        
        if search_term:
            mask = (
                filtered_df['product_name'].str.contains(search_term, case=False, na=False) |
                filtered_df['buyer'].str.contains(search_term, case=False, na=False) |
                filtered_df['region'].str.contains(search_term, case=False, na=False) |
                filtered_df['manager'].str.contains(search_term, case=False, na=False)
            )
            display_df = filtered_df[mask]
        else:
            display_df = filtered_df
        
        # Сортировка
        sort_column = st.selectbox(
            "Сортировать по:",
            ['order_date', 'amount', 'quantity', 'buyer', 'product_name', 'region']
        )
        sort_order = st.radio("Порядок:", ['По убыванию', 'По возрастанию'], horizontal=True)
        
        if sort_order == 'По убыванию':
            display_df = display_df.sort_values(sort_column, ascending=False)
        else:
            display_df = display_df.sort_values(sort_column, ascending=True)
        
        # Отображение таблицы
        st.dataframe(
            display_df.head(1000),  # Ограничиваем для производительности
            width='stretch',
            column_config={
                "amount": st.column_config.NumberColumn(
                    "Сумма",
                    format="%.0f ₽"
                ),
                "order_date": st.column_config.DateColumn(
                    "Дата заказа",
                    format="DD.MM.YYYY"
                )
            }
        )
        
        if len(display_df) > 1000:
            st.warning(f"⚠️ Показаны первые 1000 записей из {len(display_df):,}")
    
    # Боковая панель с дополнительной аналитикой
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Быстрая аналитика")
    
    if not filtered_df.empty:
        # Топ товар дня
        today_data = filtered_df[filtered_df['order_date'].dt.date == filtered_df['order_date'].dt.date.max()]
        if not today_data.empty:
            top_product_today = today_data.groupby('product_name')['amount'].sum().idxmax()
            st.sidebar.success(f"🏆 Топ товар сегодня: {top_product_today}")
        
        # Самый активный менеджер
        top_manager = filtered_df.groupby('manager')['amount'].sum().idxmax()
        top_manager_amount = filtered_df.groupby('manager')['amount'].sum().max()
        st.sidebar.info(f"👨‍💼 Топ менеджер: {top_manager}\n💰 {top_manager_amount:,.0f} ₽")
        
        # Средний чек по категориям
        avg_by_category = filtered_df.groupby('category')['amount'].mean().sort_values(ascending=False)
        st.sidebar.write("**📊 Средний чек по категориям:**")
        for cat, avg in avg_by_category.head(5).items():
            st.sidebar.write(f"• {cat}: {avg:,.0f} ₽")
    
    # Футер с дополнительной информацией
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            "**📊 Дашборд создан для анализа данных заказов Оримэкс**\n\n"
            "✅ Нормализованная база данных SQLite\n"
            "✅ Интерактивная аналитика с Plotly\n"
            "✅ Расширенные KPI метрики"
        )
    
    with col2:
        st.markdown(
            f"**🔄 Последнее обновление:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"**📈 Версия:** 2.0 Advanced\n"
            f"**🗄️ Записей в БД:** {len(df):,}\n"
            f"**🔍 Отфильтровано:** {len(filtered_df):,}"
        )
    
    with col3:
        if not filtered_df.empty:
            efficiency = len(filtered_df[filtered_df['amount'] > filtered_df['amount'].mean()]) / len(filtered_df) * 100
            st.markdown(
                f"**⚡ Эффективность продаж:** {efficiency:.1f}%\n\n"
                f"**📊 Покрытие регионов:** {filtered_df['region'].nunique()}\n"
                f"**🎯 Активных менеджеров:** {filtered_df['manager'].nunique()}\n"
                f"**📦 Товарных позиций:** {filtered_df['product_name'].nunique()}"
            )

if __name__ == "__main__":
    main()
