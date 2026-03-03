
@echo off
:: PASO 1: Entrar a la carpeta donde quedó el proyecto en el servidor  EJEMPLO: cd /d "C:\Ruta\Al\Proyecto\crm-alpapel"
cd /d "PON_AQUI_LA_DIRECCIÓN_REAL_DE_LA_CARPETA" 

:: PASO 2: Activar el entorno virtual (asumiendo que la carpeta venv está adentro)
call venv\Scripts\activate

:: PASO 3: Arrancar el CRM
streamlit run app.py --server.port 8501 --server.headless true

pause