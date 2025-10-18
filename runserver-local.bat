@echo off
REM runserver-local.bat - starts Django dev server bound to 127.0.0.1:8000
if exist env\Scripts\python.exe (
    env\Scripts\python.exe manage.py runserver 127.0.0.1:8000
) else (
    python manage.py runserver 127.0.0.1:8000
)
