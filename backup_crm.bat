@echo off
:: 1. Definir rutas (Ajusta estas rutas a las del servidor)
set ORIGEN="C:\Proyectos\crm-alpapel\cartera_crm.db"
set DESTINO="C:\Backups_CRM"

:: 2. Obtener la fecha actual para el nombre del archivo (Formato AAAAMMDD)
set FECHA=%date:~10,4%%date:~7,2%%date:~4,2%

:: 3. Crear la carpeta de destino si no existe
if not exist %DESTINO% mkdir %DESTINO%

:: 4. Copiar el archivo con el nuevo nombre
copy /y %ORIGEN% %DESTINO%\cartera_backup_%FECHA%.db

echo Backup completado el %date%