# Конфигуратор ПК

Веб-приложение для поиска комплектующих и сохранения сборок компьютеров.

## Возможности

- Регистрация, вход и просмотр профиля.
- Поиск комплектующих по названию и типу.
- Создание, редактирование и удаление своих сборок.
- ИИ-чат с историей и подбор сборки при настроенном ИИ-сервисе.

## Установка

Нужны Python 3.12 и Node.js 20 или новее с npm.
Скачайте проект и откройте терминал в его корне — папке с `backend` и `frontend`.

macOS / Linux:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
```

Windows — PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

## Настройки

Настройки хранятся в `backend/.env`. Пример — `backend/.env.example`.
Для работы ИИ укажите ключ сервиса, адрес API и модели.
Без настройки ИИ остальные функции сайта доступны.

## Запуск

**1. Сервер.** В первом терминале из корня проекта:

```bash
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

На Windows замените `.venv/bin/python` на `.\.venv\Scripts\python.exe`.

**2. Интерфейс.** Во втором терминале из корня проекта:

```bash
cd frontend
npm ci
npm start
```

**3. Сайт.** Откройте [http://localhost:3000](http://localhost:3000).
Оба терминала должны оставаться открытыми. Для остановки нажмите Ctrl+C в каждом.

При повторном запуске установка зависимостей и `npm ci` не нужны.
На подготовленном Mac можно запускать обе части двойным щелчком по `start-local.command`.

## Библиотеки

Сервер: FastAPI, Uvicorn, SQLAlchemy, Pydantic, bcrypt, python-jose,
OpenAI SDK и python-dotenv. Версии указаны в `backend/requirements-web.txt`.

Интерфейс: React, React Router, Axios и react-scripts.
Версии указаны в `frontend/package.json` и `frontend/package-lock.json`.
