#!/usr/bin/env python3

from datetime import datetime
import os

def main():
    from datetime import datetime

    # Тест использования datetime
    print("Testing datetime usage...")

    # Время последнего обновления базы данных
    if os.path.exists('orimex_orders.db'):
        db_time = os.path.getmtime('orimex_orders.db')
        db_datetime = datetime.fromtimestamp(db_time)
        print(f"Database time: {db_datetime}")
    else:
        print("Database file not found")

    print("Test completed successfully")

if __name__ == "__main__":
    main()