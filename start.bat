@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo.
echo === Email Service — Запуск ===
echo.

:: Проверка Docker
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Docker не установлен. Установите Docker Desktop.
    pause
    exit /b 1
)

docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Docker не запущен. Запустите Docker Desktop.
    pause
    exit /b 1
)

:: Создание .env если нет
if not exist .env (
    echo Файл .env не найден. Создаю из .env.example...
    copy .env.example .env >nul

    :: Генерация ключей через Python
    where python >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        for /f "delims=" %%k in ('python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2^>nul') do (
            set "FERNET=%%k"
        )
        if defined FERNET (
            powershell -Command "(Get-Content .env) -replace '^FERNET_KEY=.*', 'FERNET_KEY=!FERNET!' | Set-Content .env"
            echo FERNET_KEY сгенерирован.
        )

        for /f "delims=" %%j in ('python -c "import secrets; print(secrets.token_hex(32))" 2^>nul') do (
            set "JWT=%%j"
        )
        if defined JWT (
            powershell -Command "(Get-Content .env) -replace '^JWT_SECRET_KEY=.*', 'JWT_SECRET_KEY=!JWT!' | Set-Content .env"
            echo JWT_SECRET_KEY сгенерирован.
        )
    ) else (
        echo [!] Python не найден. Заполните FERNET_KEY и JWT_SECRET_KEY в .env вручную.
    )

    echo.
    echo Проверьте .env и заполните OPENROUTER_API_KEY для генерации вариаций.
    echo.
)

:: Сборка и запуск
echo Собираю и запускаю контейнеры...
docker compose up --build -d

echo.
echo Ожидаю готовности PostgreSQL...
timeout /t 5 /nobreak >nul

:: Миграции
echo Запускаю миграции базы данных...
docker compose exec -T backend alembic revision --autogenerate -m "init" 2>nul
docker compose exec -T backend alembic upgrade head

echo.
echo ================================================
echo   Email Service запущен!
echo ================================================
echo.
echo   Дашборд:   http://localhost:3000
echo   API:       http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo   Зарегистрируйте аккаунт и начните работу.
echo.
echo Команды:
echo   docker compose logs -f          — логи всех сервисов
echo   docker compose logs -f backend  — логи бэкенда
echo   docker compose down             — остановить
echo.
pause
