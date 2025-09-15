@echo off
echo 🚀 Запуск дашбордов Оримэкс
echo ============================

echo.
echo 📊 Доступные дашборды:
echo 1. Базовый дашборд - http://localhost:8501
echo 2. Расширенный дашборд - http://localhost:8502  
echo 3. AI-дашборд - http://localhost:8503
echo 4. Инструменты аналитики - http://localhost:8504
echo 5. Ультимативный дашборд - http://localhost:8505
echo 6. МЕГА-дашборд - http://localhost:8506
echo 7. Лаунчер - http://localhost:8500

echo.
set /p choice="Выберите дашборд (1-7) или нажмите Enter для лаунчера: "

if "%choice%"=="1" (
    echo Запускаем базовый дашборд...
    streamlit run dashboard.py --server.port 8501
) else if "%choice%"=="2" (
    echo Запускаем расширенный дашборд...
    streamlit run advanced_dashboard.py --server.port 8502
) else if "%choice%"=="3" (
    echo Запускаем AI-дашборд...
    streamlit run super_dashboard.py --server.port 8503
) else if "%choice%"=="4" (
    echo Запускаем инструменты аналитики...
    streamlit run analytics_tools.py --server.port 8504
) else if "%choice%"=="5" (
    echo Запускаем ультимативный дашборд...
    streamlit run ultimate_dashboard.py --server.port 8505
) else if "%choice%"=="6" (
    echo Запускаем МЕГА-дашборд...
    streamlit run mega_dashboard.py --server.port 8506
) else (
    echo Запускаем лаунчер...
    streamlit run launcher.py --server.port 8500
)

pause
