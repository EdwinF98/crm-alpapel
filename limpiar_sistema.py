import os
import shutil

# 1. Definir la ruta tal cual está en tu database.py
home_dir = os.path.expanduser("~")
data_dir = os.path.join(home_dir, "cartera_crm_data")
db_path = os.path.join(data_dir, "cartera_crm.db")

print(f"Buscando base de datos en: {db_path}")

# 2. Borrar el archivo si existe
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print("✅ Base de datos antigua ELIMINADA con éxito.")
    except Exception as e:
        print(f"❌ No se pudo borrar: {e}. Asegúrate de cerrar Streamlit primero.")
else:
    print("⚠️ No se encontró el archivo en esa ruta. Quizás ya lo borraste.")

# 3. Limpiar también la carpeta de temporales por si acaso
if os.path.exists(data_dir):
    print(f"Carpeta de datos lista para nueva inicialización: {data_dir}")