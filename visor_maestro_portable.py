import os

# --- FORZAR TEMA OSCURO/AGUAMARINA DE STREAMLIT ---
def configurar_tema():
    st_dir = os.path.join(os.getcwd(), ".streamlit")
    os.makedirs(st_dir, exist_ok=True)
    config_path = os.path.join(st_dir, "config.toml")
    tema_config = "[theme]\nbase='dark'\nprimaryColor='#40E0D0'\nbackgroundColor='#000000'\nsecondaryBackgroundColor='#111111'\ntextColor='#FFFFFF'\n"
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(tema_config)
    except Exception:
        pass
configurar_tema()

import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import HeatMap, Draw
from streamlit_folium import st_folium
import os
import io
import re
import base64
import urllib.parse
from shapely.geometry import Point
from datetime import datetime
from PIL import Image
from pathlib import Path

st.set_page_config(page_title="Sinergia - Visor Interactivo De Chachajo", layout="wide", page_icon="🌍")

# --- VISOR DE IMÁGENES INDEPENDIENTE ---
query_params = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
if "visor_img" in query_params and "carpeta" in query_params:
    img_name = query_params["visor_img"][0] if isinstance(query_params["visor_img"], list) else query_params["visor_img"]
    carpeta = query_params["carpeta"][0] if isinstance(query_params["carpeta"], list) else query_params["carpeta"]
    
    BASE_DIR = os.getcwd()
    ruta_img = os.path.join(BASE_DIR, 'data', 'Fotos', carpeta, img_name)
    
    if not os.path.exists(ruta_img):
        ruta_img = os.path.join(BASE_DIR, 'data', 'Fotos', carpeta, img_name.replace('.jpg', '.JPG').replace('.png', '.PNG'))
        
    if os.path.exists(ruta_img):
        st.subheader(f"📷 Visor de Imagen Original: {img_name}")
        st.image(ruta_img, use_container_width=True)
    else:
        st.error(f"No se pudo cargar la imagen original en la ruta: {ruta_img}")
    st.stop()

# --- RUTAS PORTABLES Y RELATIVAS ---
BASE_DIR = os.getcwd()
CARPETA_DATA = os.path.join(BASE_DIR, 'data')
CARPETA_DATOS = os.path.join(CARPETA_DATA, 'Datos_Procesados_Fase1')
CARPETA_TABLAS = os.path.join(CARPETA_DATA, 'Tablas')
CARPETA_FOTOS = os.path.join(CARPETA_DATA, 'Fotos')

ARCHIVOS_GEOJSON = {
    'limite': '1_Limite_Chachajo.geojson',
    'uso': '2_Zonas_Uso_Clip.geojson',
    'restauracion': '3_Restauracion_Clip.geojson',
    'drenajes': '4_Drenaje_Sencillo_Clip.geojson',
    'puntos': '6_Puntos_Comunidad_Clip.geojson',
    'camaras': '7_Waypoints_Camaras.geojson'
}

@st.cache_data
def cargar_datos_actualizado():
    capas = {}
    
    for nombre, archivo in ARCHIVOS_GEOJSON.items():
        ruta = os.path.join(CARPETA_DATOS, archivo)
        if os.path.exists(ruta):
            gdf = gpd.read_file(ruta)
            for col in gdf.select_dtypes(include=['datetime64', 'datetime64[ns]', 'datetimetz']).columns:
                gdf[col] = gdf[col].astype(str)
            capas[nombre] = gdf.to_crs('EPSG:4326')
        else:
            capas[nombre] = None

    # Sitios Estratégicos
    archivo_estrategicos = None
    if os.path.exists(CARPETA_DATOS):
        for f in os.listdir(CARPETA_DATOS):
            if f.endswith('.geojson') and any(x in f.lower() for x in ['estrategicos', 'matematizados', 'tsv']):
                archivo_estrategicos = os.path.join(CARPETA_DATOS, f)
                break
                
    if archivo_estrategicos and os.path.exists(archivo_estrategicos):
        gdf_tsv = gpd.read_file(archivo_estrategicos)
        for col in gdf_tsv.select_dtypes(include=['datetime64', 'datetime64[ns]', 'datetimetz']).columns:
            gdf_tsv[col] = gdf_tsv[col].astype(str)
        capas['estrategicos'] = gdf_tsv.to_crs('EPSG:4326')
    else:
        capas['estrategicos'] = None
        
    # Registros Fotográficos
    ruta_tsv_fotos = os.path.join(CARPETA_TABLAS, 'Registros_Chachajo_Con_Nombres.tsv')
    df_fotos_valid = pd.DataFrame()
    if os.path.exists(ruta_tsv_fotos):
        try:
            df_fotos = pd.read_csv(ruta_tsv_fotos, sep='\t')
            
            def parse_dms(dms_str):
                try:
                    s = str(dms_str).strip(' "')
                    parts = [p for p in re.split(r'[°\'"]+', s) if p]
                    if len(parts) >= 3:
                        return float(parts[0]) + float(parts[1])/60 + float(parts[2])/3600
                except:
                    pass
                return None
            
            df_fotos['lat_dd'] = df_fotos['Latitud (N)'].apply(parse_dms)
            df_fotos['lon_dd'] = df_fotos['Longitud (W)'].apply(lambda x: -parse_dms(x) if parse_dms(x) else None)
            
            df_fotos_valid = df_fotos.dropna(subset=['lat_dd', 'lon_dd']).copy()
            df_fotos_valid['geometry'] = [Point(xy) for xy in zip(df_fotos_valid['lon_dd'], df_fotos_valid['lat_dd'])]
            capas['registros_fotos'] = gpd.GeoDataFrame(df_fotos_valid, geometry='geometry', crs='EPSG:4326')
        except Exception as e:
            st.warning(f"No se pudo cargar el TSV de fotos: {e}")
            capas['registros_fotos'] = None
    else:
        capas['registros_fotos'] = None

    # Recorrido Exploratorio
    ruta_tsv_nuevo = os.path.join(CARPETA_TABLAS, 'RegistrofFotograficoExploracionNuevo.tsv')
    if os.path.exists(ruta_tsv_nuevo):
        try:
            df_nuevo = pd.read_csv(ruta_tsv_nuevo, sep='\t')
            df_nuevo['lat_dd'] = df_nuevo['Latitud']
            df_nuevo['lon_dd'] = df_nuevo['Longitud']
            df_nuevo['Nombre_Archivo_Buscador'] = df_nuevo['Nombre de Archivo']
            
            df_nuevo_valid = df_nuevo.dropna(subset=['lat_dd', 'lon_dd']).copy()
            df_nuevo_valid['geometry'] = [Point(xy) for xy in zip(df_nuevo_valid['lon_dd'], df_nuevo_valid['lat_dd'])]
            capas['registros_exploracion'] = gpd.GeoDataFrame(df_nuevo_valid, geometry='geometry', crs='EPSG:4326')
        except Exception as e:
            st.warning(f"No se pudo cargar el TSV de Recorrido Exploratorio: {e}")
            capas['registros_exploracion'] = None
    else:
        capas['registros_exploracion'] = None

    # Excel Integrado
    ruta_excel_integrado = os.path.join(CARPETA_TABLAS, 'Base_Datos_Integrada_Sinergia_Chachajo.xlsx')
    if os.path.exists(ruta_excel_integrado):
        try:
            xl = pd.ExcelFile(ruta_excel_integrado)
            capas['tablas_extra'] = {}
            capas['descripciones_excel'] = {}
            
            for i, sheet in enumerate(xl.sheet_names):
                # Detección dinámica de la fila de encabezados
                df_temp = xl.parse(sheet, header=None, nrows=10)
                
                if len(df_temp) > 1 and pd.notna(df_temp.iloc[1, 0]):
                    capas['descripciones_excel'][sheet] = str(df_temp.iloc[1, 0])
                    
                sr = 0
                max_non_null = 0
                for r in range(len(df_temp)):
                    count = sum([1 for x in df_temp.iloc[r].dropna().astype(str) if 'unnamed' not in x.lower()])
                    if count > max_non_null:
                        max_non_null = count
                        sr = r
                        
                df_xls = xl.parse(sheet, skiprows=sr).dropna(how='all')
                df_xls.columns = [str(c).strip() for c in df_xls.columns]
                
                if 'Longitud (X)' in df_xls.columns and 'Latitud (Y)' in df_xls.columns:
                    gdf_xls = gpd.GeoDataFrame(
                        df_xls, 
                        geometry=gpd.points_from_xy(df_xls['Longitud (X)'], df_xls['Latitud (Y)']),
                        crs='EPSG:4326'
                    )
                    
                    if 'Cámara' in sheet or 'Camara' in sheet or 'Cmara' in sheet:
                        if capas.get('camaras') is not None and not capas['camaras'].empty:
                            capas['camaras'] = gpd.sjoin_nearest(capas['camaras'].to_crs('EPSG:3857'), gdf_xls.to_crs('EPSG:3857'), how='left', max_distance=50).to_crs('EPSG:4326')
                            if 'index_right' in capas['camaras'].columns:
                                capas['camaras'] = capas['camaras'].drop(columns=['index_right'])
                        else:
                            capas['camaras'] = gdf_xls
                            
                    elif 'Puntos' in sheet or 'GIS' in sheet or 'Estratégicos' in sheet:
                        if capas.get('estrategicos') is not None and not capas['estrategicos'].empty:
                            capas['estrategicos'] = gpd.sjoin_nearest(capas['estrategicos'].to_crs('EPSG:3857'), gdf_xls.to_crs('EPSG:3857'), how='left', max_distance=50).to_crs('EPSG:4326')
                            if 'index_right' in capas['estrategicos'].columns:
                                capas['estrategicos'] = capas['estrategicos'].drop(columns=['index_right'])
                        else:
                            capas['estrategicos'] = gdf_xls
                else:
                    capas['tablas_extra'][sheet] = df_xls

        except Exception as e:
            st.warning(f"Error al integrar la base de datos Excel: {e}")

    return capas

capas = cargar_datos_actualizado()

@st.cache_data
def get_image_base64(path):
    try:
        img = Image.open(path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.thumbnail((300, 300))
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=75)
        encoded_string = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{encoded_string}"
    except Exception:
        return ""

# --- SIDEBAR ---
st.sidebar.title("🛠️ Panel de Control")

st.sidebar.subheader("🗺️ Mapa Base")
mapa_base = st.sidebar.selectbox("Selecciona la imagen satelital:", [
    "Satélite Actual (Esri)",
    "Plano (OSM)"
])

st.sidebar.subheader("📌 Capas Analíticas")
mostrar_uso = st.sidebar.checkbox("Zonas de Uso", value=True)
mostrar_restauracion = st.sidebar.checkbox("Zonas Restauración", value=True)
mostrar_drenajes = st.sidebar.checkbox("Drenajes", value=False)
mostrar_puntos = st.sidebar.checkbox("Puntos Comunidad", value=False)
mostrar_kde = st.sidebar.checkbox("KDE (Mapa Calor)", value=False)
mostrar_estrategicos = st.sidebar.checkbox("Sitios Estratégicos (TSV)", value=True)
mostrar_fotos = st.sidebar.checkbox("Registros Fotográficos", value=True)
mostrar_exploracion = st.sidebar.checkbox("Registros Exploración", value=True)
mostrar_camaras = st.sidebar.checkbox("Cámaras Trampa (Desarrollo)", value=False)

# --- INICIALIZAR EL CONTADOR NUCLEAR ---
if 'map_key_counter' not in st.session_state:
    st.session_state.map_key_counter = 0

# --- TABS ---
tab_instrucciones, tab_mapa, tab_datos, tab_export = st.tabs(["📖 Instrucciones", "🗺️ Visor Geográfico", "📋 Tabla de Atributos", "💾 Exportación"])

with tab_instrucciones:
    st.subheader("📖 Instrucciones de Uso")
    st.markdown("""
    Bienvenido al **Visor Maestro Chachajo**, una aplicación en construcción diseñada para la sistematización y gestión de datos geográficos. El programa permite procesar información espacial para mapear áreas intervenidas, zonas potenciales para aislamiento y ubicar nuevas áreas geográficas destinadas a la protección de fauna.

    ### 🗺️ Visor Geográfico (Mapa)
    - **Navegación:** Usa el ratón para arrastrar el mapa y la rueda para hacer zoom.
    - **Capas Analíticas:** En el panel izquierdo (Panel de Control), puedes activar o desactivar diferentes capas (Zonas de Uso, Restauración, Puntos Comunidad, etc.).
    - **Herramienta de Dibujo:** En la esquina superior izquierda del mapa, encontrarás un icono de marcador (📍). Haz clic en él y luego en cualquier parte del mapa para crear un nuevo punto.
    - **Registro de Nuevos Puntos:** Después de colocar un marcador en el mapa, aparecerá un formulario en el panel izquierdo. Completa los datos y selecciona la capa de destino para guardar el punto.
    - **Visor de Fotos:** Haz clic en los marcadores de las capas fotográficas para ver la imagen y sus metadatos.

    ### 📋 Tabla de Atributos (Edición)
    - **Visualización:** Selecciona la capa que deseas ver en el menú desplegable.
    - **Edición:** Haz doble clic en cualquier celda para modificar su contenido de forma temporal.
    - **Guardado:** Una vez que realices cambios, presiona el botón "💾 Guardar Cambios" correspondiente para actualizar de forma permanente la base de datos (Excel o GeoJSON).
    - **Ver Imágenes:** En las tablas de fotografías ("Registros Fotográficos" y "Registros Exploración Nueva"), encontrarás la columna **"Ver Imagen 📸"**. Haz clic en el enlace para abrir la imagen original en el visor integrado.

    ### 💾 Exportación
    - **Captura Web (HTML):** Descarga el mapa actual (con las capas activas) como un archivo HTML interactivo para abrirlo en cualquier navegador sin internet.
    - **Reporte Excel:** Descarga todas las tablas de datos (incluyendo tus modificaciones) en un archivo Excel.
    
    > **Nota:** Todos los archivos exportados se guardarán automáticamente en tu **Escritorio**.
    """)

with tab_mapa:
    st.subheader("Visor Analítico del Territorio")
    
    if capas['limite'] is not None:
        centro_lat = capas['limite'].geometry.centroid.y.mean()
        centro_lon = capas['limite'].geometry.centroid.x.mean()
    else:
        centro_lat, centro_lon = 4.0, -76.0 
        
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=15, max_zoom=24, tiles=None)
    
    if mapa_base == "Satélite Actual (Esri)":
        folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satélite (Esri)', max_zoom=24, max_native_zoom=18).add_to(m)
    elif mapa_base == "Plano (OSM)":
        folium.TileLayer('OpenStreetMap', name='Plano (OSM)', max_zoom=24, max_native_zoom=19).add_to(m)

    # --- PLUGIN DRAW DE FOLIUM PARA PUNTOS ---
    Draw(
        export=False,
        position="topleft",
        draw_options={
            "polyline": False,
            "polygon": False,
            "circle": False,
            "rectangle": False,
            "circlemarker": False,
            "marker": True 
        }
    ).add_to(m)

    if capas['limite'] is not None:
        cols_limite = [c for c in capas['limite'].columns if c != 'geometry']
        folium.GeoJson(capas['limite'], name="Límite", style_function=lambda x: {'color': 'black', 'weight': 4, 'fillOpacity': 0, 'dashArray': '5, 5'}, popup=folium.GeoJsonPopup(fields=cols_limite)).add_to(m)

    if mostrar_uso and capas['uso'] is not None:
        gdf_uso = capas['uso']
        col_desc = 'Descipcion' if 'Descipcion' in gdf_uso.columns else 'Descripci' if 'Descripci' in gdf_uso.columns else None
        cols_uso = [c for c in gdf_uso.columns if c != 'geometry']
        colores = ['blue', 'cadetblue', 'green', 'purple', 'orange', 'darkblue', 'darkgreen', 'lightblue', 'darkpurple', 'pink', 'lightgreen']
        descripciones = gdf_uso[col_desc].dropna().unique() if col_desc else []
        diccionario_colores = {desc: colores[i % len(colores)] for i, desc in enumerate(descripciones)}
        
        fg_uso = folium.FeatureGroup(name="Zonas de Uso")
        folium.GeoJson(
            gdf_uso, 
            style_function=lambda feature: {'fillColor': '#2ca25f', 'color': '#006d2c', 'weight': 2, 'fillOpacity': 0.6},
            popup=folium.GeoJsonPopup(fields=cols_uso)
        ).add_to(fg_uso)
        
        for idx, row in gdf_uso.iterrows():
            if pd.notna(row.geometry):
                punto = row.geometry.representative_point()
                desc_texto = row[col_desc] if col_desc and pd.notna(row[col_desc]) else "Sin descripción"
                color_marcador = diccionario_colores.get(row.get(col_desc), 'gray')
                popup_html = "<div style='max-height: 250px; overflow-y: auto; font-size: 13px;'>" + "".join([f"<b>{c}:</b> {row[c]}<br>" for c in cols_uso if pd.notna(row[c])]) + "</div>"
                folium.Marker(location=[punto.y, punto.x], tooltip=f"<b>{desc_texto}</b>", popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color=color_marcador, icon='info-sign')).add_to(fg_uso)
        fg_uso.add_to(m)

    if mostrar_restauracion and capas['restauracion'] is not None:
        cols_rest = [c for c in capas['restauracion'].columns if c != 'geometry']
        folium.GeoJson(capas['restauracion'], name="Zonas Restauración", style_function=lambda x: {'color': 'orange', 'weight': 2, 'fillColor': 'orange', 'fillOpacity': 0.4}, popup=folium.GeoJsonPopup(fields=cols_rest)).add_to(m)

    if mostrar_drenajes and capas.get('drenajes') is not None:
        cols_dren = [c for c in capas['drenajes'].columns if c != 'geometry']
        folium.GeoJson(capas['drenajes'], name="Drenajes", style_function=lambda x: {'color': 'blue', 'weight': 2, 'opacity': 0.7}, popup=folium.GeoJsonPopup(fields=cols_dren)).add_to(m)

    if mostrar_puntos and capas.get('puntos') is not None:
        cols_puntos = [c for c in capas['puntos'].columns if c != 'geometry']
        fg_puntos = folium.FeatureGroup(name="Puntos Comunidad")
        for idx, row in capas['puntos'].iterrows():
            if pd.notna(row.geometry):
                popup_html = "<div style='max-height: 250px; overflow-y: auto; font-size: 13px;'>" + "".join([f"<b>{c}:</b> {row[c]}<br>" for c in cols_puntos if pd.notna(row[c])]) + "</div>"
                folium.Marker(location=[row.geometry.y, row.geometry.x], tooltip=f"<b>{row.get('Descripci', 'Punto Comunidad')}</b>", popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color='orange', icon='home')).add_to(fg_puntos)
        fg_puntos.add_to(m)

    if mostrar_kde and capas.get('puntos') is not None:
        heat_data = [[row.geometry.y, row.geometry.x] for idx, row in capas['puntos'].iterrows() if pd.notna(row.geometry)]
        if heat_data:
            HeatMap(heat_data, name="Mapa de Calor", radius=25, blur=15, max_zoom=13).add_to(m)

    if mostrar_estrategicos and capas['estrategicos'] is not None:
        cols_est = [c for c in capas['estrategicos'].columns if c != 'geometry']
        fg_est = folium.FeatureGroup(name="Sitios Estratégicos")
        for idx, row in capas['estrategicos'].iterrows():
            if pd.notna(row.geometry):
                zona = row.get('Nombre', row.get('Tipo de Zona/Infraestructura', 'Sitio Estratégico'))
                popup_html = "<div style='max-height: 250px; overflow-y: auto; font-size: 13px;'>" + "".join([f"<b>{c}:</b> {row[c]}<br>" for c in cols_est if pd.notna(row[c])]) + "</div>"
                folium.Marker(location=[row.geometry.y, row.geometry.x], tooltip=f"<b>{zona}</b>", popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color='orange', icon='star')).add_to(fg_est)
        fg_est.add_to(m)

    if mostrar_camaras and capas['camaras'] is not None:
        cols_cam = [c for c in capas['camaras'].columns if c != 'geometry']
        fg_camaras = folium.FeatureGroup(name="Cámaras Trampa")
        for idx, row in capas['camaras'].iterrows():
            if pd.notna(row.geometry):
                popup_html = "<div style='max-height: 250px; overflow-y: auto; font-size: 13px;'>" + "".join([f"<b>{c}:</b> {row[c]}<br>" for c in cols_cam if pd.notna(row[c])]) + "</div>"
                folium.Marker(location=[row.geometry.y, row.geometry.x], tooltip=f"<b>{row.get('ID_Camara', 'Cámara')}</b>", popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color='black', icon='camera')).add_to(fg_camaras)
        fg_camaras.add_to(m)

    if mostrar_fotos and capas.get('registros_fotos') is not None:
        cols_fotos = [c for c in capas['registros_fotos'].columns if c not in ['geometry', 'lat_dd', 'lon_dd', 'Nombre_Archivo_Buscador', 'Carpeta_Origen']]
        fg_fotos = folium.FeatureGroup(name="Registros Fotográficos")
        for idx, row in capas['registros_fotos'].iterrows():
            if pd.notna(row.geometry):
                nombre_img = row.get('Nombre_Archivo_Buscador') if pd.notna(row.get('Nombre_Archivo_Buscador')) else row.get('Índice / Nombre', 'Imagen')
                carpeta_origen = row.get('Carpeta_Origen', 'Registro Fotográfico')
                carpeta_origen = 'Registro Fotográfico' if pd.isna(carpeta_origen) else str(carpeta_origen)
                
                ruta_img = os.path.join(CARPETA_FOTOS, carpeta_origen, str(nombre_img))
                img_html = ""
                if os.path.exists(ruta_img):
                    b64_img = get_image_base64(ruta_img)
                    if b64_img: img_html = f"<div style='text-align: center; margin-top: 10px;'><img src='{b64_img}' width='250px' style='border-radius: 8px; box-shadow: 0px 4px 6px rgba(0,0,0,0.3);'/></div>"
                else:
                    ruta_img_upper = os.path.join(CARPETA_FOTOS, carpeta_origen, str(nombre_img).replace('.jpg', '.JPG').replace('.png', '.PNG'))
                    ruta_img_alt = os.path.join(CARPETA_FOTOS, 'Registro Fotográfico', str(nombre_img))
                    if os.path.exists(ruta_img_upper):
                        b64_img = get_image_base64(ruta_img_upper)
                        if b64_img: img_html = f"<div style='text-align: center; margin-top: 10px;'><img src='{b64_img}' width='250px' style='border-radius: 8px; box-shadow: 0px 4px 6px rgba(0,0,0,0.3);'/></div>"
                    elif os.path.exists(ruta_img_alt):
                        b64_img = get_image_base64(ruta_img_alt)
                        if b64_img: img_html = f"<div style='text-align: center; margin-top: 10px;'><img src='{b64_img}' width='250px' style='border-radius: 8px; box-shadow: 0px 4px 6px rgba(0,0,0,0.3);'/></div>"
                    else:
                        img_html = f"<div style='color: #008B8B; font-size: 11px; margin-top: 5px;'><i>(Imagen no encontrada: {nombre_img})</i></div>"
                
                texto_html = "".join([f"<b>{c}:</b> {row[c]}<br>" for c in cols_fotos if pd.notna(row[c])])
                popup_html = f"<div style='max-height: 400px; overflow-y: auto; font-size: 13px;'>{texto_html}{img_html}</div>"
                folium.Marker(location=[row.geometry.y, row.geometry.x], tooltip=f"<b>{nombre_img}</b>", popup=folium.Popup(popup_html, max_width=320), icon=folium.Icon(color='purple', icon='camera', prefix='fa')).add_to(fg_fotos)
        fg_fotos.add_to(m)

    if mostrar_exploracion and capas.get('registros_exploracion') is not None:
        cols_expl = [c for c in capas['registros_exploracion'].columns if c not in ['geometry', 'lat_dd', 'lon_dd', 'Nombre_Archivo_Buscador']]
        fg_expl = folium.FeatureGroup(name="Registros Exploración Nueva")
        for idx, row in capas['registros_exploracion'].iterrows():
            if pd.notna(row.geometry):
                nombre_img = row.get('Nombre_Archivo_Buscador') if pd.notna(row.get('Nombre_Archivo_Buscador')) else row.get('Nombre de Archivo', 'Imagen')
                ruta_img = os.path.join(CARPETA_FOTOS, 'Recorrido Exploratorio', str(nombre_img))
                img_html = ""
                if os.path.exists(ruta_img):
                    b64_img = get_image_base64(ruta_img)
                    if b64_img: img_html = f"<div style='text-align: center; margin-top: 10px;'><img src='{b64_img}' width='250px' style='border-radius: 8px; box-shadow: 0px 4px 6px rgba(0,0,0,0.3);'/></div>"
                else:
                    ruta_img_upper = os.path.join(CARPETA_FOTOS, 'Recorrido Exploratorio', str(nombre_img).replace('.jpg', '.JPG').replace('.png', '.PNG'))
                    if os.path.exists(ruta_img_upper):
                        b64_img = get_image_base64(ruta_img_upper)
                        if b64_img: img_html = f"<div style='text-align: center; margin-top: 10px;'><img src='{b64_img}' width='250px' style='border-radius: 8px; box-shadow: 0px 4px 6px rgba(0,0,0,0.3);'/></div>"
                    else:
                        img_html = f"<div style='color: #008B8B; font-size: 11px; margin-top: 5px;'><i>(Imagen no encontrada)</i></div>"
                
                texto_html = "".join([f"<b>{c}:</b> {row[c]}<br>" for c in cols_expl if pd.notna(row[c])])
                popup_html = f"<div style='max-height: 400px; overflow-y: auto; font-size: 13px;'>{texto_html}{img_html}</div>"
                folium.Marker(location=[row.geometry.y, row.geometry.x], tooltip=f"<b>{nombre_img}</b>", popup=folium.Popup(popup_html, max_width=320), icon=folium.Icon(color='darkgreen', icon='camera', prefix='fa')).add_to(fg_expl)
        fg_expl.add_to(m)

    # --- CONTROL DE CAPAS ---
    folium.LayerControl().add_to(m)

    # AQUÍ ESTÁ LA MAGIA NUCLEAR: El key cambia cada vez que guardas o cancelas.
    map_data = st_folium(m, width="100%", height=700, key=f"mapa_interactivo_{st.session_state.map_key_counter}", returned_objects=["all_drawings"])
    
    dibujos_actuales = map_data.get("all_drawings") if map_data else []

# --- SIDEBAR: GESTIÓN DE PUNTOS ---
st.sidebar.markdown("---")
st.sidebar.subheader("📍 Gestión de Puntos")

# Si el usuario dibujó algo en el mapa actual, mostramos el formulario
if dibujos_actuales and len(dibujos_actuales) > 0:
    ultimo_dibujo = dibujos_actuales[-1]
    lon_val, lat_val = ultimo_dibujo["geometry"]["coordinates"]
    
    with st.sidebar.expander("📝 Formulario de Registro", expanded=True):
        with st.form("form_nuevo_punto"):
            st.number_input("Latitud (Y)", value=float(lat_val), format="%.6f", disabled=True)
            st.number_input("Longitud (X)", value=float(lon_val), format="%.6f", disabled=True)
            
            nuevo_nombre = st.text_input("Nombre / ID del Lugar", placeholder="Ej: Nuevo Avistamiento")
            nueva_desc = st.text_area("Descripción / Notas de Campo", placeholder="Detalles, observaciones...")
            capa_destino = st.selectbox("¿A qué capa pertenece?", ["Puntos Comunidad", "Cámaras Trampa", "Sitios Estratégicos"])
            
            submitted = st.form_submit_button("Guardar en Base de Datos", type="primary", use_container_width=True)

        # Botón de cancelar (afuera del form para que no requiera validación)
        if st.sidebar.button("❌ Cancelar Registro", use_container_width=True):
            st.session_state.map_key_counter += 1 # Reinicia el mapa
            st.rerun()

        if submitted:
            # 1. El nuevo punto siempre nace en WGS84 (EPSG:4326) desde Folium
            nuevo_gdf = gpd.GeoDataFrame(
                [{'Descripci': nuevo_nombre, 'Nombre': nuevo_nombre, 'Notas': nueva_desc}], 
                geometry=[Point(lon_val, lat_val)],
                crs='EPSG:4326'
            )
            
            os.makedirs(CARPETA_DATOS, exist_ok=True)
            ruta_guardar = None
            
            if capa_destino == "Puntos Comunidad":
                ruta_guardar = os.path.join(CARPETA_DATOS, ARCHIVOS_GEOJSON['puntos'])
            elif capa_destino == "Cámaras Trampa":
                ruta_guardar = os.path.join(CARPETA_DATOS, ARCHIVOS_GEOJSON['camaras'])
            elif capa_destino == "Sitios Estratégicos":
                if os.path.exists(CARPETA_DATOS):
                    for f in os.listdir(CARPETA_DATOS):
                        if f.endswith('.geojson') and any(x in f.lower() for x in ['estrategicos', 'matematizados', 'tsv']):
                            ruta_guardar = os.path.join(CARPETA_DATOS, f)
                            break
                if not ruta_guardar:
                    ruta_guardar = os.path.join(CARPETA_DATOS, '8_Sitios_Estrategicos.geojson')

            if ruta_guardar:
                try:
                    if os.path.exists(ruta_guardar):
                        gdf_existente = gpd.read_file(ruta_guardar)
                        
                        if gdf_existente.crs is not None and nuevo_gdf.crs != gdf_existente.crs:
                            nuevo_gdf = nuevo_gdf.to_crs(gdf_existente.crs)
                        
                        for col in gdf_existente.columns:
                            if col not in nuevo_gdf.columns and col != 'geometry':
                                nuevo_gdf[col] = None
                                
                        for col in nuevo_gdf.columns:
                            if col not in gdf_existente.columns and col != 'geometry':
                                gdf_existente[col] = None
                                
                        gdf_final = pd.concat([gdf_existente, nuevo_gdf], ignore_index=True)
                    else:
                        gdf_final = nuevo_gdf
                    
                    gdf_final.to_file(ruta_guardar, driver='GeoJSON')
                    
                    st.toast("✅ Punto guardado exitosamente.", icon="🎉")
                    st.session_state.map_key_counter += 1 # REINICIO NUCLEAR DEL MAPA
                    st.cache_data.clear()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error al guardar el archivo: {e}")
                    st.info("⚠️ Verifica que no tengas el archivo abierto. Eso bloquea la escritura.")
            else:
                st.error("❌ No se pudo determinar la ruta de guardado.")
else:
    st.sidebar.info("💡 **Para agregar un registro nuevo:**\nUsa la herramienta del pin 📍 en el menú izquierdo del mapa y pon un marcador.")

with tab_datos:
    st.subheader("Base de Datos Espacial y Tabular")
    
    col_texto, col_toggle = st.columns([3, 1])
    with col_texto:
        st.markdown("Visualiza y explora las tablas de atributos asociadas a cada capa.")
    with col_toggle:
        modo_edicion = st.toggle("✏️ Activar Modo Edición", value=False)
        
    if modo_edicion:
        st.info("Modo Edición activado: Haz doble clic en cualquier celda para modificar la información. Luego, guarda los cambios.")
    
    categoria = st.radio(
        "📂 Categoría de Datos:",
        ["📊 Resumen General", "👥 Cartografía Social", "🗺️ Datos Geográficos", "📸 Registros Fotográficos", "📷 Diseño de Cámaras Trampa"],
        horizontal=True
    )
    
    opciones_capas = {}
    tablas_extra_keys = {}
    
    hojas_excel = list(capas.get('tablas_extra', {}).keys())
    hoja_resumen = hojas_excel[0] if hojas_excel else None
    
    if categoria == "📊 Resumen General":
        if hoja_resumen:
            opciones_capas[f"📊 {hoja_resumen}"] = f"extra_{hoja_resumen}"
            tablas_extra_keys[f"extra_{hoja_resumen}"] = hoja_resumen
        else:
            st.info("No se encontró el Resumen General en la base de datos Excel.")
            
    elif categoria == "👥 Cartografía Social":
        opciones_carto = []
        for hoja in hojas_excel:
            h_low = hoja.lower()
            if not any(x in h_low for x in ['resumen', 'puntos', 'gis', 'estratégic', 'estrategic', 'camara', 'cámara', 'fauna', 'flora', 'planta', 'bio', 'etno']):
                opciones_carto.append(f"👥 {hoja}")
        opciones_carto.append("🌱 Biodiversidad y Etnobiología")
        
        sub_categoria = st.selectbox("Seleccione la subsección:", opciones_carto)
        
        if sub_categoria == "🌱 Biodiversidad y Etnobiología":
            for hoja in hojas_excel:
                h_low = hoja.lower()
                if 'fauna' in h_low:
                    opciones_capas["🐾 Fauna Local"] = f"extra_{hoja}"
                    tablas_extra_keys[f"extra_{hoja}"] = hoja
                elif 'flora' in h_low or 'planta' in h_low:
                    opciones_capas["🌿 Flora Local"] = f"extra_{hoja}"
                    tablas_extra_keys[f"extra_{hoja}"] = hoja
            
            # Forzar la descripción de la categoría principal si existe
            desc_bio = ""
            for h in hojas_excel:
                if 'bio' in h.lower() or 'etno' in h.lower():
                    desc_bio = capas.get('descripciones_excel', {}).get(h, "")
                    break
            if len(desc_bio) > 10 and "unnamed" not in desc_bio.lower():
                st.info(f"📖 **Descripción de la sección:** {desc_bio}")
                
        else:
            hoja_real = sub_categoria.replace("👥 ", "")
            opciones_capas[sub_categoria] = f"extra_{hoja_real}"
            tablas_extra_keys[f"extra_{hoja_real}"] = hoja_real
            
        if not opciones_carto:
            st.info("No se encontraron tablas de Cartografía Social en el Excel.")
            
    elif categoria == "🗺️ Datos Geográficos":
        opciones_capas = {
            "Sitios Estratégicos (Enriquecidos)": "estrategicos",
            "Puntos Comunidad": "puntos",
            "Zonas de Uso": "uso",
            "Zonas Restauración": "restauracion",
            "Drenajes": "drenajes"
        }
        
    elif categoria == "📸 Registros Fotográficos":
        opciones_capas = {
            "Registros Fotográficos": "registros_fotos",
            "Registros Exploración Nueva": "registros_exploracion"
        }
        
    elif categoria == "📷 Diseño de Cámaras Trampa":
        opciones_capas = {
            "Cámaras Trampa (Enriquecidas)": "camaras"
        }
        
    if opciones_capas:
        capa_seleccionada = st.selectbox("Seleccione la capa o tabla para visualizar y editar:", list(opciones_capas.keys()))
        clave_gdf = opciones_capas[capa_seleccionada]
        
        if clave_gdf.startswith("extra_"):
            nombre_hoja = tablas_extra_keys[clave_gdf]
            df_mostrar = capas['tablas_extra'][nombre_hoja]
            
            desc_texto = capas.get('descripciones_excel', {}).get(nombre_hoja, "")
            if len(desc_texto) > 10 and "unnamed" not in desc_texto.lower():
                st.info(f"📖 **Descripción de la sección:** {desc_texto}")

            if modo_edicion:
                edited_df = st.data_editor(df_mostrar, use_container_width=True, height=500, key=f"editor_{clave_gdf}", num_rows="dynamic", hide_index=True)
                if st.button("💾 Guardar Cambios en Excel", type="primary"):
                    try:
                        ruta_excel_integrado = os.path.join(CARPETA_TABLAS, 'Base_Datos_Integrada_Sinergia_Chachajo.xlsx')
                        with pd.ExcelWriter(ruta_excel_integrado, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
                            edited_df.to_excel(writer, sheet_name=nombre_hoja, index=False)
                        st.success(f"✅ Cambios guardados en la hoja '{nombre_hoja}' del archivo Excel original.")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
            else:
                st.dataframe(df_mostrar, use_container_width=True, height=500, key=f"view_{clave_gdf}", hide_index=True)
                    
        elif capas.get(clave_gdf) is not None:
            df_mostrar = pd.DataFrame(capas[clave_gdf].drop(columns='geometry', errors='ignore'))

            if clave_gdf == "estrategicos":
                for sheet_name, desc in capas.get('descripciones_excel', {}).items():
                    if 'puntos' in sheet_name.lower() or 'estratégic' in sheet_name.lower() or 'estrategic' in sheet_name.lower() or 'gis' in sheet_name.lower():
                        if len(desc) > 10 and "unnamed" not in desc.lower():
                            st.info(f"📖 **Descripción de la sección:** {desc}")
                        break

            column_config = {}
            if clave_gdf == "registros_fotos":
                urls = []
                for _, row in df_mostrar.iterrows():
                    nombre_img = row.get('Nombre_Archivo_Buscador') if pd.notna(row.get('Nombre_Archivo_Buscador')) else row.get('Índice / Nombre', 'Imagen')
                    carpeta_origen = row.get('Carpeta_Origen', 'Registro Fotográfico')
                    carpeta_origen = 'Registro Fotográfico' if pd.isna(carpeta_origen) else str(carpeta_origen)
                    nombre_img_enc = urllib.parse.quote(str(nombre_img))
                    carpeta_origen_enc = urllib.parse.quote(str(carpeta_origen))
                    urls.append(f"/?visor_img={nombre_img_enc}&carpeta={carpeta_origen_enc}")
                df_mostrar.insert(0, 'Ver Imagen 📸', urls)
                column_config['Ver Imagen 📸'] = st.column_config.LinkColumn("Ver Imagen 📸", display_text="Abrir imagen")
                
            elif clave_gdf == "registros_exploracion":
                urls = []
                for _, row in df_mostrar.iterrows():
                    nombre_img = row.get('Nombre_Archivo_Buscador') if pd.notna(row.get('Nombre_Archivo_Buscador')) else row.get('Nombre de Archivo', 'Imagen')
                    nombre_img_enc = urllib.parse.quote(str(nombre_img))
                    urls.append(f"/?visor_img={nombre_img_enc}&carpeta=Recorrido%20Exploratorio")
                df_mostrar.insert(0, 'Ver Imagen 📸', urls)
                column_config['Ver Imagen 📸'] = st.column_config.LinkColumn("Ver Imagen 📸", display_text="Abrir imagen")
    
            if modo_edicion:
                edited_df = st.data_editor(df_mostrar, use_container_width=True, height=500, key=f"editor_{clave_gdf}", column_config=column_config, hide_index=True)
                
                if st.button("💾 Guardar Cambios en Capa Espacial", type="primary"):
                    try:
                        gdf_original = capas[clave_gdf]
                        if 'Ver Imagen 📸' in edited_df.columns:
                            edited_df = edited_df.drop(columns=['Ver Imagen 📸'])
                        edited_gdf = gpd.GeoDataFrame(edited_df, geometry=gdf_original.geometry, crs=gdf_original.crs)
                        
                        ruta_guardar = None
                        if clave_gdf in ARCHIVOS_GEOJSON:
                            ruta_guardar = os.path.join(CARPETA_DATOS, ARCHIVOS_GEOJSON[clave_gdf])
                        elif clave_gdf == "estrategicos":
                            for f in os.listdir(CARPETA_DATOS):
                                if f.endswith('.geojson') and any(x in f.lower() for x in ['estrategicos', 'matematizados', 'tsv']):
                                    ruta_guardar = os.path.join(CARPETA_DATOS, f)
                                    break
                                    
                        if ruta_guardar and os.path.exists(ruta_guardar):
                            edited_gdf.to_file(ruta_guardar, driver='GeoJSON')
                            st.success("✅ Cambios guardados correctamente.")
                            st.cache_data.clear()
                        else:
                            st.error("❌ No se pudo localizar el archivo fuente.")
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
            else:
                st.dataframe(df_mostrar, use_container_width=True, height=500, key=f"view_{clave_gdf}", column_config=column_config, hide_index=True)
        else:
            st.warning("No hay datos disponibles para esta capa o tabla.")

with tab_export:
    st.subheader("Exportación de Datos")
    st.write("### 📸 Exportar Mapa como Captura Web (HTML)")
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    st.info("💡 Al ser una versión de escritorio, los archivos se guardarán directamente en tu Escritorio.")
    
    # Detección inteligente del escritorio (Windows Inglés/Español o fallback a usuario)
    escritorio = Path.home() / "Desktop"
    if not escritorio.exists():
        escritorio = Path.home() / "Escritorio"
    if not escritorio.exists():
        escritorio = Path.home()
        
    if st.button(f"💾 Guardar Mapa en el Escritorio ({hoy})", use_container_width=True):
        try:
            ruta_html = os.path.join(escritorio, f"Mapa_Chachajo_Captura_{hoy}.html")
            m.save(ruta_html)
            st.success(f"✅ Mapa guardado exitosamente en:\n\n`{ruta_html}`")
        except Exception as e:
            st.error(f"❌ Error al guardar el mapa: {e}")
    
    st.write("---")
    st.write("### 📊 Exportar a Excel (Reporte)")
    
    if st.button(f"💾 Guardar Reporte Excel en el Escritorio ({hoy})", use_container_width=True):
        try:
            ruta_excel = os.path.join(escritorio, f"Reporte_Sinergia_{hoy}.xlsx")
            with pd.ExcelWriter(ruta_excel, engine='xlsxwriter') as writer:
                for clave, gdf in capas.items():
                    if clave != 'tablas_extra' and gdf is not None:
                        df = pd.DataFrame(gdf.drop(columns='geometry', errors='ignore'))
                        if not gdf.empty and gdf.geom_type.iloc[0] == 'Point':
                            df['Longitud (X)'] = gdf.geometry.x
                            df['Latitud (Y)'] = gdf.geometry.y
                        df.to_excel(writer, sheet_name=clave[:31], index=False)
            st.success(f"✅ Reporte guardado exitosamente en:\n\n`{ruta_excel}`")
        except Exception as e:
            st.error(f"❌ Error al guardar el Excel: {e}")