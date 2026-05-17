import os
import shutil

def recolectar_datos():
    # 1. Definir la ruta base original (absoluta)
    carpeta_raiz = r'c:\Users\MSI\OneDrive\Documentos\DOCUMENTOS SANTIAGO\santiago vault\Trabajo\Sinergia'
    
    # 2. Diccionario de elementos a copiar: {ruta_origen: subcarpeta_destino_en_data}
    elementos_a_copiar = {
        # Carpeta de datos procesados (GeoJSONs)
        os.path.join(carpeta_raiz, 'Datos_Procesados_Fase1'): 'Datos_Procesados_Fase1',
        
        # Archivos TSV Exploratorios
        os.path.join(carpeta_raiz, 'Scripts_y_Datos_Exploratorios', 'Registros_Chachajo_Con_Nombres.tsv'): 'Tablas',
        os.path.join(carpeta_raiz, 'Scripts_y_Datos_Exploratorios', 'RegistrofFotograficoExploracionNuevo.tsv'): 'Tablas',
        
        # Base de datos en Excel
        os.path.join(carpeta_raiz, 'Base_Datos_Integrada_Sinergia_Chachajo.xlsx'): 'Tablas',
        
        # Carpetas de fotografías
        os.path.join(carpeta_raiz, 'GEORREFERENCIACION AREAS RESTAURADAS CTO 374-2022', 'Entrega_Sinergia', 'Comunidad Chachajo', 'Registro Fotográfico'): os.path.join('Fotos', 'Registro Fotográfico'),
        os.path.join(carpeta_raiz, 'GEORREFERENCIACION AREAS RESTAURADAS CTO 374-2022', 'Entrega_Sinergia', 'Comunidad Chachajo', 'Recorrido Exploratorio'): os.path.join('Fotos', 'Recorrido Exploratorio')
    }
    
    # 3. Crear la carpeta principal 'data'
    carpeta_datos = os.path.join(os.getcwd(), 'data')
    
    print("--- INICIANDO RECOLECCIÓN DE DATOS (FASE 1) ---")
    
    for ruta_origen, subcarpeta in elementos_a_copiar.items():
        if not os.path.exists(ruta_origen):
            print(f"⚠️ ADVERTENCIA: No se encontró la ruta: {ruta_origen}")
            continue
            
        nombre_elemento = os.path.basename(ruta_origen)
        
        if os.path.isdir(ruta_origen):
            ruta_destino = os.path.join(carpeta_datos, subcarpeta)
            os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
            try:
                if os.path.exists(ruta_destino):
                    shutil.rmtree(ruta_destino)
                shutil.copytree(ruta_origen, ruta_destino)
                print(f"📁 Carpeta copiada exitosamente: {nombre_elemento} -> data/{subcarpeta}")
            except Exception as e:
                print(f"❌ Error al copiar carpeta {nombre_elemento}: {e}")
        else:
            carpeta_destino = os.path.join(carpeta_datos, subcarpeta)
            os.makedirs(carpeta_destino, exist_ok=True)
            ruta_destino = os.path.join(carpeta_destino, nombre_elemento)
            try:
                shutil.copy2(ruta_origen, ruta_destino)
                print(f"📄 Archivo copiado exitosamente: {nombre_elemento} -> data/{subcarpeta}")
            except Exception as e:
                print(f"❌ Error al copiar archivo {nombre_elemento}: {e}")

    print("\n--- RECOLECCIÓN FINALIZADA ---")
    print(f"Todos los datos están listos en: {carpeta_datos}")

if __name__ == "__main__":
    recolectar_datos()