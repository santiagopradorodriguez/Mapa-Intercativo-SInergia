import pandas as pd
import os

ruta_excel = os.path.join(os.getcwd(), 'data', 'Tablas', 'Base_Datos_Integrada_Sinergia_Chachajo.xlsx')

try:
    xl = pd.ExcelFile(ruta_excel)
    hojas_disponibles = xl.sheet_names
    
    # Intenta adivinar cuál es la de Biodiversidad o Etnobiología
    nombre_hoja = next((h for h in hojas_disponibles if 'bio' in h.lower() or 'etno' in h.lower()), None)
    if not nombre_hoja:
        print(f"👉 Hojas disponibles: {hojas_disponibles}")
        nombre_hoja = input("✍️ Escribe el nombre exacto de la hoja de Biodiversidad: ")
        
    print(f"\n📖 Leyendo hoja '{nombre_hoja}' asumiendo encabezados en la fila 3...")
    # Saltamos las 2 primeras filas para que la Fila 3 quede como los títulos
    df = pd.read_excel(ruta_excel, sheet_name=nombre_hoja, skiprows=2)
    
    # Confirmación visual
    if len(df.columns) >= 5:
        print(f"📊 La columna E (quinta columna) se llama: '{df.columns[4]}'")
    
    print("\n🌳 Como las primeras filas son Fauna y luego siguen las Plantas...")
    fila_excel = input("✍️ Fíjate en tu Excel: ¿En qué número de fila de Excel empieza la primera Planta/Flora? (Ej: 45) ")
    
    # Matemática: Excel es base 1. Saltamos 2 filas (encabezado en la 3). 
    # Por lo tanto, los datos arrancan en la Fila 4 de Excel, que es el Índice 0 de Python.
    indice_corte = int(fila_excel) - 4
    
    if 0 < indice_corte < len(df):
        df_fauna = df.iloc[:indice_corte].dropna(how='all')
        df_flora = df.iloc[indice_corte:].dropna(how='all')
        
        with pd.ExcelWriter(ruta_excel, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_fauna.to_excel(writer, sheet_name='Fauna local', index=False)
            df_flora.to_excel(writer, sheet_name='Flora local', index=False)
            
        print(f"\n✅ ¡Éxito! Se separaron {len(df_fauna)} registros de Fauna y {len(df_flora)} de Flora.")
    else:
        print("\n❌ El número de fila es inválido o se sale del límite de la tabla.")
        
except Exception as e:
    print(f"❌ Ocurrió un error: {e}")