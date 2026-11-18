# FinTrack — учебная система учёта личных финансов

Локальное веб-приложение для записи доходов и расходов, распределения операций по категориям и просмотра итогового баланса. Проект подготовлен как самостоятельный учебный пример для демонстрации модульной интеграции. Публичный GitHub-репозиторий и деплой не созданы.

## Стек
- Python 3.10+; Flask
- SQLite; параметризованные SQL-запросы
- HTML, CSS, Jinja2
- pytest

## Запуск
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Откройте http://127.0.0.1:5000. База SQLite создаётся автоматически в каталоге instance.

## Тестирование
```bash
pytest -q
```

## API
- `GET /api/categories` — список категорий.
- `GET /api/transactions` — список операций.
- `POST /api/transactions` — создание операции (JSON: amount, kind, category_id, operation_date, comment).
- `GET /api/reports/summary` — сумма доходов, расходов и баланс.

## Ограничения учебной версии
Авторизация, публичный хостинг, GitHub Actions, Code Climate и публичная демонстрация не настроены. Не используйте проект для хранения реальных финансовых данных.



## Демонстрация проекта

Рабочая версия приложения:
https://fintrack-vitalik.onrender.com
