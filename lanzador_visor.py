import os
import sys

# --- PARCHE PARA PYTHONNET (WEBVIEW) Y PYINSTALLER ---
# Fuerza a que pywebview encuentre la DLL de Python correcta dentro de _internal/
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    for archivo in os.listdir(bundle_dir):
        # Busca archivos como python310.dll, python311.dll, etc.
        if archivo.startswith("python3") and archivo.endswith(".dll") and len(archivo) >= 12:
            os.environ["PYTHONNET_PYDLL"] = os.path.join(bundle_dir, archivo)
            break
# ------------------------------------------------------

import threading
import time
import webview
import urllib.request
import urllib.error
import streamlit.web.cli as stcli
import signal

# Parche para evitar el error: "ValueError: signal only works in main thread"
# Esto ocurre porque Streamlit intenta registrar señales de apagado en un hilo secundario.
_original_signal = signal.signal
def patched_signal(signum, handler):
    try:
        return _original_signal(signum, handler)
    except ValueError:
        pass
signal.signal = patched_signal

# Redirigir stdout y stderr para evitar que Streamlit crashee
# por no encontrar la consola al compilar en modo --windowed
class NullWriter:
    def write(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass
if sys.stdout is None:
    sys.stdout = NullWriter()
if sys.stderr is None:
    sys.stderr = NullWriter()

def run_streamlit(script_path):
    sys.argv = [
        "streamlit", "run", script_path, 
        "--server.headless=true", 
        "--global.developmentMode=false",
        "--server.port=8599",
        "--server.address=127.0.0.1",
        "--theme.base=dark",
        "--theme.primaryColor=#40E0D0",
        "--theme.backgroundColor=#000000",
        "--theme.secondaryBackgroundColor=#111111",
        "--theme.textColor=#FFFFFF"
    ]
    try:
        stcli.main()
    except SystemExit:
        pass

def esperar_servidor(url, timeout=45):
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req):
                return True
        except urllib.error.HTTPError:
            return True  # El servidor respondió, aunque sea con un error de ruta
        except Exception:
            time.sleep(0.5)
    return False

if __name__ == "__main__":
    # PyInstaller crea referencias específicas cuando se compila
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
    else:
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
        
    script_path = os.path.join(bundle_dir, 'visor_maestro_portable.py')
    
    # Forzamos que el directorio de trabajo sea la carpeta del ejecutable 
    # para que las rutas relativas hacia ./data/ funcionen perfectamente.
    os.chdir(bundle_dir)
    
    # Iniciar Streamlit en segundo plano
    t = threading.Thread(target=run_streamlit, args=(script_path,), daemon=True)
    t.start()
    
    url_local = "http://127.0.0.1:8599"
    
    # Esperamos de forma inteligente hasta que Streamlit termine de cargar (máximo 45 segundos)
    esperar_servidor(url_local)
    
    # Creamos y lanzamos la ventana nativa
    try:
        webview.create_window(
            'Sinergia - Visor Maestro Chachajo', 
            url_local,
            width=1366,
            height=768,
            min_size=(800, 600)
        )
        webview.start()
    except Exception as e:
        import traceback
        print("\n❌ ERROR FATAL AL INICIAR LA VENTANA (WEBVIEW):")
        traceback.print_exc()
        input("\nPresiona Enter para salir del programa...")
    finally:
        # Forzar el cierre de todos los hilos al cerrar la ventana
        os._exit(0)
