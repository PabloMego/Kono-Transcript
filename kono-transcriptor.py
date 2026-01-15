import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import whisper
import threading
import os

# --- Variables globales ---
transcripcion_actual = ""  # Guardará la transcripción actual
archivo_seleccionado = ""  # Guardará la ruta completa del archivo

# --- Mapeo de idiomas para Whisper ---
idioma_map = {
    "Español": "es",
    "Inglés": "en",
    "Francés": "fr",
    "Alemán": "de"
}

# --- Función para seleccionar archivo ---
def seleccionar_archivo():
    global archivo_seleccionado
    archivo = filedialog.askopenfilename(
        title="Selecciona un archivo de audio",
        filetypes=[("Archivos de audio", "*.mp3 *.wav *.m4a *.ogg")]
    )
    if archivo:
        archivo_seleccionado = archivo
        ruta_audio.set(os.path.basename(archivo))

# --- Función para guardar archivo ---
def guardar_transcripcion():
    global transcripcion_actual
    if not transcripcion_actual:
        messagebox.showwarning("Atención", "Primero debes transcribir el audio antes de guardar.")
        return

    archivo_guardar = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Archivos de texto", "*.txt")],
        title="Guardar transcripción"
    )
    if archivo_guardar:
        with open(archivo_guardar, "w", encoding="utf-8") as f:
            f.write(transcripcion_actual)
        messagebox.showinfo("Éxito", f"Transcripción guardada en:\n{archivo_guardar}")

# --- Función para copiar todo al portapapeles ---
def copiar_todo():
    global transcripcion_actual
    if not transcripcion_actual:
        messagebox.showwarning("Atención", "No hay transcripción para copiar.")
        return
    root.clipboard_clear()
    root.clipboard_append(transcripcion_actual)
    messagebox.showinfo("Copiado", "Transcripción copiada al portapapeles.")

# --- Función para formatear marcas de tiempo ---
def formatear_timestamp(segundos):
    minutos = int(segundos // 60)
    segundos = int(segundos % 60)
    return f"[{minutos:02d}:{segundos:02d}]"

# --- Función para transcribir audio con progreso ---
def transcribir_audio():
    global transcripcion_actual, archivo_seleccionado
    modelo_nombre = modelo_var.get()
    idioma_seleccionado = idioma_var.get()

    if not archivo_seleccionado:
        messagebox.showwarning("Atención", "Por favor selecciona un archivo de audio.")
        return

    texto_area.config(state=tk.NORMAL)
    texto_area.delete(1.0, tk.END)
    texto_area.insert(tk.END, f"Cargando modelo '{modelo_nombre}'...\nEsto puede tardar unos segundos...\n")
    texto_area.config(state=tk.DISABLED)

    progress_bar["value"] = 0
    progress_bar["maximum"] = 100

    def worker():
        global transcripcion_actual
        try:
            model = whisper.load_model(modelo_nombre)

            # --- Detectar automáticamente si idioma = "Detectar automáticamente" ---
            if idioma_seleccionado == "Detectar automáticamente":
                result = model.transcribe(archivo_seleccionado, verbose=False)
            else:
                # Usar el código correcto
                idioma = idioma_map.get(idioma_seleccionado, "auto")
                result = model.transcribe(archivo_seleccionado, language=idioma, verbose=False)

            total_segments = len(result["segments"])
            transcripcion_actual = ""
            texto_area.config(state=tk.NORMAL)
            texto_area.delete(1.0, tk.END)

            for i, seg in enumerate(result["segments"], start=1):
                timestamp = formatear_timestamp(seg['start'])
                line = f"{timestamp} {seg['text'].strip()}\n\n"
                transcripcion_actual += line

                # Insertar timestamp en azul
                texto_area.insert(tk.END, timestamp + " ", "timestamp")
                # Insertar el resto del texto normal
                texto_area.insert(tk.END, seg['text'].strip() + "\n\n")

                # Actualizar barra de progreso
                progress_bar["value"] = (i / total_segments) * 100
                root.update_idletasks()

            texto_area.tag_config("timestamp", foreground="blue")
            texto_area.config(state=tk.DISABLED)
            progress_bar["value"] = 100

        except Exception as e:
            texto_area.config(state=tk.NORMAL)
            texto_area.delete(1.0, tk.END)
            texto_area.insert(tk.END, f"Ocurrió un error: {e}")
            texto_area.config(state=tk.DISABLED)
            progress_bar["value"] = 0

    threading.Thread(target=worker).start()

# --- Interfaz gráfica ---
root = tk.Tk()
root.title("Kono Studio - Transcriptor Local con Whisper")
root.geometry("750x650")

ruta_audio = tk.StringVar()
modelo_var = tk.StringVar(value="tiny")  # Modelo por defecto
idioma_var = tk.StringVar(value="Detectar automáticamente")  # Idioma por defecto

# Botones
tk.Button(root, text="Seleccionar Audio", command=seleccionar_archivo).pack(pady=5)
tk.Button(root, text="Transcribir", command=transcribir_audio).pack(pady=5)
tk.Button(root, text="Guardar Transcripción TXT", command=guardar_transcripcion).pack(pady=5)
tk.Button(root, text="Copiar Todo", command=copiar_todo).pack(pady=5)

# Selector de modelo
tk.Label(root, text="Selecciona el modelo Whisper local:").pack()
modelos_disponibles = ["tiny", "base", "small", "medium", "large"]
tk.OptionMenu(root, modelo_var, *modelos_disponibles).pack(pady=5)

# Selector de idioma
tk.Label(root, text="Selecciona el idioma:").pack()
idiomas_disponibles = ["Detectar automáticamente"] + list(idioma_map.keys())
tk.OptionMenu(root, idioma_var, *idiomas_disponibles).pack(pady=5)

# Mostrar nombre del archivo seleccionado
tk.Label(root, text="Archivo seleccionado:").pack()
tk.Label(root, textvariable=ruta_audio, fg="green", font=("Arial", 10, "bold")).pack(pady=2)

# Barra de progreso
progress_bar = ttk.Progressbar(root, orient="horizontal", length=700, mode="determinate")
progress_bar.pack(pady=5)

# Cuadro de texto para la transcripción
texto_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=95, height=25)
texto_area.pack(pady=10)

root.mainloop()
