# 🌍 Visor Maestro Chachajo

El **Visor Maestro Chachajo** es una aplicación actualmente en fase de construcción, diseñada para la sistematización, análisis y gestión de datos geográficos del territorio. Mediante una metodología "offline-first" e interactiva, el programa permite procesar y editar información espacial de forma local y directa en campo. Su propósito central es mapear y sistematizar tanto las áreas que ya han sido intervenidas como aquellas zonas con potencial para aislamiento, facilitando la toma de decisiones para identificar, ubicar y establecer nuevas áreas geográficas estratégicas destinadas a la protección y conservación de la fauna local.

---

## 🚀 Características Principales

1. **Visor Geográfico Interactivo:**
   * Exploración de mapas base (Satélite y Plano).
   * Control y superposición de capas analíticas: Límites, Zonas de Uso, Restauración, Drenajes, Puntos de Comunidad, Sitios Estratégicos y Cámaras Trampa.
   * Generación de Mapas de Calor (KDE) en tiempo real.
2. **Visor Fotográfico Integrado:**
   * Visualización de fotografías georreferenciadas directamente desde el mapa.
   * Carga dinámica de imágenes originales sin salir de la aplicación.
3. **Gestión y Edición de Datos Espaciales:**
   * Inserción de nuevos puntos (marcadores) directamente en el mapa usando herramientas de dibujo interactivo.
   * Asignación automática a capas específicas (Comunidad, Cámaras Trampa, Sitios Estratégicos).
   * Edición tabular en caliente: modificación de atributos directamente en tablas interactivas con guardado bidireccional (GeoJSON y Excel).
4. **Exportación de Resultados:**
   * Guardado del mapa actual como un archivo HTML interactivo (captura web).
   * Exportación de la base de datos actualizada a un reporte consolidado en Excel (`.xlsx`).

---

## 🧠 Metodología y Tecnologías Utilizadas

El visor está construido bajo una **metodología "Offline-First" y Portable**. Toda la capacidad de análisis espacial y la base de datos viajan empaquetadas en una sola carpeta, garantizando la privacidad de la información y la posibilidad de ejecutarlo en territorios con baja o nula conectividad a internet.

El ecosistema tecnológico (Stack) utilizado incluye:

* **Streamlit:** Framework de Python utilizado para construir la interfaz gráfica de usuario (GUI) de manera ágil e interactiva.
* **GeoPandas & Shapely:** Motores matemáticos para la lectura, manipulación y escritura de geometrías y datos espaciales (archivos `.geojson`).
* **Folium & Streamlit-Folium:** Bibliotecas encargadas de la renderización del mapa utilizando el motor de JavaScript *Leaflet.js*.
* **Pandas & OpenPyXL:** Procesamiento de datos tabulares, cruces de bases de datos y lectura/escritura de archivos Excel (`.xlsx`) y TSV (`.tsv`).
* **PyWebView & PyInstaller:** Herramientas de compilación que transforman el entorno de Python y Streamlit en un ejecutable nativo (`.exe`) con ventana de escritorio independiente del navegador web del usuario.

---

## 📂 Estructura de Datos (`/data/`)

Para que el visor funcione correctamente, los datos deben estar organizados de la siguiente manera dentro de la carpeta `data/` incluida en el compilado:

* `Datos_Procesados_Fase1/`: Contiene todos los polígonos, líneas y puntos en formato `GeoJSON` estandarizado (WGS84 - EPSG:4326).
* `Tablas/`: Contiene la *Base de Datos Integrada Sinergia* en Excel, así como los registros exploratorios en formato `.tsv`.
* `Fotos/`: Estructura de carpetas (`Registro Fotográfico` y `Recorrido Exploratorio`) donde reposan los archivos `.jpg` y `.png` vinculados espacialmente en las tablas.

---

## 🛠️ Solución de Problemas (Troubleshooting)

Al ser una aplicación portable, en computadoras Windows "limpias" (que no se usan para programar) podría ser necesario instalar dependencias de Microsoft la primera vez:

1. **La aplicación abre y se cierra de inmediato (Pantalla negra):**
   * **Causa:** Faltan las librerías matemáticas de C++ requeridas por GeoPandas.
   * **Solución:** Instalar *Microsoft Visual C++ Redistributable* (x64).
2. **La ventana abre pero se queda en blanco:**
   * **Causa:** El sistema no tiene el motor de navegación moderno de Windows.
   * **Solución:** Descargar e instalar *Microsoft Edge WebView2 Runtime*.

---

**Desarrollado para la comunidad de Chachajo - Proyecto Sinergia.**