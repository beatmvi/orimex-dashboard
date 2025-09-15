#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Лаунчер для всех дашбордов Оримэкс
"""

import streamlit as st
import subprocess
import sys
import os

st.set_page_config(
    page_title="🚀 Лаунчер дашбордов Оримэкс",
    page_icon="🚀",
    layout="wide"
)

# Стили
st.markdown("""
<style>
    .launcher-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        margin: 1rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
    }
    
    .launcher-card:hover {
        transform: translateY(-10px);
    }
    
    .feature-list {
        text-align: left;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🚀 Центр управления дашбордами Оримэкс")
    st.markdown("Выберите нужный дашборд для анализа данных заказов")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown("""
        <div class="launcher-card">
            <h2>📊 Базовый дашборд</h2>
            <div class="feature-list">
                ✅ Основные метрики<br/>
                ✅ Графики по времени<br/>
                ✅ Анализ регионов<br/>
                ✅ Топ товары<br/>
                ✅ Фильтры и экспорт
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Запустить базовый дашборд", key="basic"):
            st.info("Запускаем базовый дашборд...")
            st.code("streamlit run dashboard.py --server.port 8501")
    
    with col2:
        st.markdown("""
        <div class="launcher-card">
            <h2>🎯 Расширенный дашборд</h2>
            <div class="feature-list">
                ✅ Все функции базового<br/>
                ✅ ABC анализ<br/>
                ✅ Когортный анализ<br/>
                ✅ BCG матрица<br/>
                ✅ Анализ менеджеров<br/>
                ✅ Прогнозирование
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Запустить расширенный дашборд", key="advanced"):
            st.info("Запускаем расширенный дашборд...")
            st.code("streamlit run advanced_dashboard.py --server.port 8502")
    
    with col3:
        st.markdown("""
        <div class="launcher-card">
            <h2>🤖 AI-дашборд</h2>
            <div class="feature-list">
                ✅ Все предыдущие функции<br/>
                ✅ AI-детекция аномалий<br/>
                ✅ ML-сегментация клиентов<br/>
                ✅ Машинное обучение<br/>
                ✅ Сетевой анализ<br/>
                ✅ Анализ настроения
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Запустить AI-дашборд", key="ai"):
            st.info("Запускаем AI-дашборд...")
            st.code("streamlit run super_dashboard.py --server.port 8503")
    
    with col4:
        st.markdown("""
        <div class="launcher-card">
            <h2>🚀 Ультимативный дашборд</h2>
            <div class="feature-list">
                ✅ Все AI функции<br/>
                ✅ Умные инсайты<br/>
                ✅ Путешествие клиентов<br/>
                ✅ Продуктовая ДНК<br/>
                ✅ Турнир менеджеров<br/>
                ✅ Предиктивная магия
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Запустить ультимативный", key="ultimate"):
            st.info("Запускаем ультимативный дашборд...")
            st.code("streamlit run ultimate_dashboard.py --server.port 8505")
    
    with col5:
        st.markdown("""
        <div class="launcher-card">
            <h2>🌟 МЕГА-дашборд</h2>
            <div class="feature-list">
                ✅ Космический дизайн<br/>
                ✅ 3D визуализации<br/>
                ✅ Бизнес-симулятор<br/>
                ✅ Реальное время<br/>
                ✅ AI-рекомендации<br/>
                ✅ Исполнительные сводки
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Запустить МЕГА-дашборд", key="mega"):
            st.info("Запускаем МЕГА-дашборд...")
            st.code("streamlit run mega_dashboard.py --server.port 8506")
    
    st.markdown("---")
    
    # Дополнительные инструменты
    st.subheader("🛠️ Дополнительные инструменты")
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("🔧 Инструменты аналитики"):
            st.info("Запускаем инструменты аналитики...")
            st.code("streamlit run analytics_tools.py --server.port 8504")
    
    with col5:
        if st.button("📊 Проверить данные"):
            st.info("Запускаем проверку данных...")
            if os.path.exists("check_data.py"):
                result = subprocess.run([sys.executable, "check_data.py"], 
                                      capture_output=True, text=True)
                st.text(result.stdout)
    
    with col6:
        if st.button("🔄 Пересоздать БД"):
            st.info("Пересоздаем базу данных...")
            if os.path.exists("csv_to_db.py"):
                result = subprocess.run([sys.executable, "csv_to_db.py"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    st.success("✅ База данных пересоздана!")
                else:
                    st.error(f"❌ Ошибка: {result.stderr}")
    
    # Инструкции
    st.markdown("---")
    st.markdown("""
    ## 📖 Инструкции по использованию
    
    1. **Базовый дашборд** - начните с него для общего обзора данных
    2. **Расширенный дашборд** - для детального анализа и бизнес-аналитики  
    3. **AI-дашборд** - для продвинутой аналитики с машинным обучением
    4. **Инструменты** - для создания пользовательских отчетов и экспорта
    
    ### 🔗 Порты:
    - Базовый: http://localhost:8501
    - Расширенный: http://localhost:8502  
    - AI-дашборд: http://localhost:8503
    - Инструменты: http://localhost:8504
    
    ### 💡 Советы:
    - Можете запускать несколько дашбордов одновременно
    - Используйте фильтры для фокусировки на нужных данных
    - Экспортируйте результаты анализа в удобном формате
    """)

if __name__ == "__main__":
    main()
