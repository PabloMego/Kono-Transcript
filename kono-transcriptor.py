import webview
import threading
import time
import os
import json
import sys

# Evitar que subprocess lance consolas adicionales en Windows (ffmpeg, instaladores, etc.)
try:
    if os.name == 'nt':
        import subprocess as _subprocess
        _CREATE_NO_WINDOW = 0x08000000
        _orig_popen = _subprocess.Popen

        def _popen_no_window(*args, **kwargs):
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = _CREATE_NO_WINDOW
            return _orig_popen(*args, **kwargs)

        _subprocess.Popen = _popen_no_window
except Exception:
    pass

# Evitar imports pesados en el arranque: cargar whisper/pyperclip solo cuando se usan
WHISPER_AVAILABLE = False
PYPERCLIP_AVAILABLE = False

import tkinter as tk
from tkinter import filedialog

# Si el instalador incluye ffmpeg en {app}\ffmpeg, forzar pydub a usarlo.
try:
    from pydub import AudioSegment
    _app_dir = os.path.dirname(os.path.abspath(__file__))
    _ff_local = os.path.join(_app_dir, "ffmpeg", "ffmpeg.exe")
    if os.path.exists(_ff_local):
        AudioSegment.converter = _ff_local
except Exception:
    pass


class API:
    def __init__(self):
        self.window = None

    def open_file_dialog(self):
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title="Selecciona un archivo de audio",
            filetypes=[("Archivos de audio", "*.mp3 *.wav *.m4a *.ogg *.flac *.aac")]
        )
        root.destroy()
        return path or ""

    def export_txt(self, text):
        # Prefer using webview's native save dialog if available to avoid Tk windows appearing behind the webview
        try:
            if self.window and hasattr(self.window, 'create_file_dialog'):
                # 'save' dialog returns a list with the selected path or None
                try:
                    res = self.window.create_file_dialog(dialog_type=webview.FOLDER_DIALOG if False else 'save', save_filename=None, file_types=(('Text files','*.txt'),))
                except TypeError:
                    # Fallback signature
                    res = self.window.create_file_dialog('save')
                # Normalize result
                if isinstance(res, (list, tuple)) and res:
                    path = res[0]
                elif isinstance(res, str) and res:
                    path = res
                else:
                    path = ''
                if path:
                    try:
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(text or "")
                        return path
                    except Exception:
                        # fallback to tkinter if file write fails via webview dialog
                        pass
        except Exception:
            pass

        # Fallback to tkinter dialog
        try:
            root = tk.Tk()
            root.withdraw()
            path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
            root.destroy()
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text or "")
                return path
        except Exception:
            pass
        return ""

    def copy_all(self, text):
        try:
            try:
                import pyperclip
                pyperclip.copy(text or "")
                return True
            except Exception:
                root = tk.Tk()
                root.withdraw()
                root.clipboard_clear()
                root.clipboard_append(text or "")
                root.update()
                root.destroy()
                return True
        except Exception:
            return False

    def start_transcription(self, path, model_name, language):
        if not path or not os.path.exists(path):
            return {"ok": False, "error": "No file selected or file not found."}

        # Mapeo de nombres a códigos de Whisper (soporta varios idiomas nombrados en la UI)
        lang_map = {
            "español": "es",
            "es": "es",
            "inglés": "en",
            "ingles": "en",
            "en": "en",
            "francés": "fr",
            "frances": "fr",
            "fr": "fr",
            "alemán": "de",
            "aleman": "de",
            "de": "de",
        }
        lang_norm = (language or "").strip().lower()
        if lang_norm in ["detección automática", "detectar automáticamente", "detectar automatico", "detectar", "auto", "", "automatic detection"]:
            lang_norm = "auto"
        elif lang_norm in lang_map:
            lang_norm = lang_map[lang_norm]

        threading.Thread(target=self._transcription_worker, args=(path, model_name, lang_norm), daemon=True).start()
        return {"ok": True}

    def _transcription_worker(self, path, model_name, language):
        try:
            # Cargar whisper de forma diferida para no bloquear el inicio
            try:
                import whisper
                local_whisper = whisper
                whisper_available_local = True
            except Exception:
                local_whisper = None
                whisper_available_local = False

            if whisper_available_local:
                model = local_whisper.load_model(model_name or "base")

                # Intento de troceado usando pydub. Si falla, vuelve al modo anterior por duración.
                try:
                    from pydub import AudioSegment

                    audio = AudioSegment.from_file(path)
                    total_ms = len(audio)
                    # config: chunks de 30s con 1s de solapamiento
                    chunk_ms = 30 * 1000
                    overlap_ms = 1000
                    step = max(1000, chunk_ms - overlap_ms)
                    positions = list(range(0, total_ms, step))

                    processed_ms = 0
                    for idx, start_ms in enumerate(positions):
                        end_ms = min(start_ms + chunk_ms, total_ms)
                        piece = audio[start_ms:end_ms]
                        # exportar a wav temporal
                        import tempfile
                        tf = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                        tmp_path = tf.name
                        tf.close()
                        try:
                            piece.export(tmp_path, format='wav')
                        except Exception:
                            try:
                                os.unlink(tmp_path)
                            except Exception:
                                pass
                            raise

                        # transcribir chunk
                        try:
                            if language == 'auto':
                                res = model.transcribe(tmp_path)
                            else:
                                res = model.transcribe(tmp_path, language=language)
                        except Exception:
                            # si falla en un chunk, eliminar temporal y continuar
                            try:
                                os.unlink(tmp_path)
                            except Exception:
                                pass
                            raise

                        segs = res.get('segments', [])
                        for seg in segs:
                            ts = round(seg.get('start', 0) + (start_ms / 1000.0), 2)
                            chunk = {"timestamp": ts, "text": seg.get("text", "").strip()}
                            try:
                                if self.window:
                                    self.window.evaluate_js(f'window.onTranscriptionChunk({json.dumps(chunk)});')
                            except Exception:
                                pass

                        processed_ms += (end_ms - start_ms)
                        try:
                            prog = int((processed_ms / total_ms) * 100)
                        except Exception:
                            prog = 0
                        try:
                            if self.window:
                                self.window.evaluate_js(f'window.onTranscriptionProgress({min(prog,100)});')
                        except Exception:
                            pass

                        try:
                            os.unlink(tmp_path)
                        except Exception:
                            pass

                    try:
                        if self.window:
                            self.window.evaluate_js('window.onTranscriptionDone();')
                    except Exception:
                        pass

                except Exception:
                    # Fallback: si pydub no está disponible o hay algún error, usar el método por duración
                    def get_duration_seconds(pth):
                        try:
                            from pydub import AudioSegment
                            seg = AudioSegment.from_file(pth)
                            return seg.duration_seconds
                        except Exception:
                            try:
                                if pth.lower().endswith('.wav'):
                                    import wave
                                    with wave.open(pth, 'rb') as w:
                                        frames = w.getnframes()
                                        rate = w.getframerate()
                                        return frames / float(rate)
                            except Exception:
                                return None

                    duration = None
                    try:
                        duration = get_duration_seconds(path)
                    except Exception:
                        duration = None

                    progress_stop = threading.Event()
                    progress_lock = threading.Lock()
                    current_prog = {"val": 0}

                    def progress_by_duration():
                        start = time.time()
                        try:
                            while not progress_stop.is_set():
                                elapsed = time.time() - start
                                with progress_lock:
                                    if duration and duration > 0:
                                        p = int((elapsed / duration) * 100)
                                        p = max(0, min(p, 95))
                                        current_prog['val'] = p
                                    else:
                                        if current_prog['val'] < 90:
                                            current_prog['val'] += 3
                                        current_prog['val'] = min(current_prog['val'], 90)
                                    p = int(current_prog['val'])
                                try:
                                    if self.window:
                                        self.window.evaluate_js(f'window.onTranscriptionProgress({p});')
                                except Exception:
                                    pass
                                time.sleep(0.5)
                        except Exception:
                            pass

                    t = threading.Thread(target=progress_by_duration, daemon=True)
                    t.start()

                    # realizar transcripción completa como fallback
                    if language == "auto":
                        result = model.transcribe(path)
                    else:
                        result = model.transcribe(path, language=language)

                    progress_stop.set()
                    try:
                        t.join(timeout=1.0)
                    except Exception:
                        pass

                    segments = result.get("segments", [])
                    total = len(segments) or 1
                    with progress_lock:
                        baseline = int(min(current_prog.get("val", 0), 95))

                    for i, seg in enumerate(segments, start=1):
                        chunk = {"timestamp": round(seg.get("start", 0), 2), "text": seg.get("text", "").strip()}
                        try:
                            if self.window:
                                self.window.evaluate_js(f'window.onTranscriptionChunk({json.dumps(chunk)});')
                        except Exception:
                            pass
                        try:
                            prog = baseline + int((i / total) * (100 - baseline))
                        except Exception:
                            prog = int((i / total) * 100)
                        try:
                            if self.window:
                                self.window.evaluate_js(f'window.onTranscriptionProgress({prog});')
                        except Exception:
                            pass
                    try:
                        if self.window:
                            self.window.evaluate_js('window.onTranscriptionDone();')
                    except Exception:
                        pass
            else:
                demo_lines = [
                    "Hola a todos, bienvenidos a un nuevo video.",
                    "Hoy estamos probando la nueva herramienta de transcripción de Kono Studio.",
                    "Esta aplicación utiliza modelos locales o remotos para generar texto en tiempo real.",
                    "Puedes copiar o exportar el resultado al finalizar.",
                ]
                total = len(demo_lines)
                for i, line in enumerate(demo_lines, start=1):
                    chunk = {"timestamp": i * 3, "text": line}
                    try:
                        if self.window:
                            self.window.evaluate_js(f'window.onTranscriptionChunk({json.dumps(chunk)});')
                    except Exception:
                        pass
                    prog = int((i / total) * 100)
                    try:
                        if self.window:
                            self.window.evaluate_js(f'window.onTranscriptionProgress({prog});')
                    except Exception:
                        pass
                    time.sleep(1.2)
                try:
                    if self.window:
                        self.window.evaluate_js('window.onTranscriptionDone();')
                except Exception:
                    pass
        except Exception as e:
            try:
                if self.window:
                    self.window.evaluate_js(f'window.onTranscriptionError({json.dumps(str(e))});')
            except Exception:
                pass


def main():
    api = API()
    html_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "index_test.html")
    WIDTH = 1400
    HEIGHT = 800
    try:
        root = tk.Tk()
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        root.destroy()
    except Exception:
        screen_w = None
        screen_h = None

    if screen_w and screen_h:
        x = int((screen_w - WIDTH) / 2)
        y = int((screen_h - HEIGHT) / 2)
    else:
        x = None
        y = None

    # create window and attach API
    try:
        window = webview.create_window("Kono Transcriptor", html_path, js_api=api, width=WIDTH, height=HEIGHT, x=x, y=y)
    except Exception as e:
        with open(os.path.join(os.path.dirname(__file__), 'kono.log'), 'a', encoding='utf-8') as _f:
            _f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - ERROR creating window: {e}\n")
        raise
    api.window = window

    # Small logger helper
    def write_log(msg):
        try:
            with open(os.path.join(os.path.dirname(__file__), 'kono.log'), 'a', encoding='utf-8') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
        except Exception:
            pass

    write_log('Window created')

    # Event to detect when the UI has finished loading
    ui_loaded = threading.Event()

    def on_loaded():
        write_log('UI loaded event received')
        ui_loaded.set()

    try:
        window.events.loaded += on_loaded
    except Exception:
        write_log('Could not attach loaded event')

    def on_closed():
        write_log('Window closed by user')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

    # Suscribirse al evento de cerrado de la ventana principal
    try:
        window.events.closed += on_closed
    except Exception:
        pass

    # Watchdog: if UI not loaded within timeout, log and show message
    def watchdog():
        timeout = 12
        write_log(f'Watchdog started, waiting up to {timeout}s for UI load')
        if not ui_loaded.wait(timeout):
            write_log('UI did not signal loaded within timeout')
            try:
                # show a simple Tk alert (may or may not appear depending on GUI state)
                root = tk.Tk()
                root.withdraw()
                from tkinter import messagebox
                messagebox.showwarning('Kono Transcriptor', 'La interfaz no terminó de cargar en el tiempo esperado. Revisa que WebView2 esté instalado.')
                root.destroy()
            except Exception:
                write_log('Failed to show messagebox to user')
        else:
            write_log('Watchdog: UI loaded successfully')

    threading.Thread(target=watchdog, daemon=True).start()

    try:
        write_log('Starting webview')
        webview.start(gui='edgechromium')
        write_log('webview.start returned')
    except Exception as e:
        write_log(f'webview.start raised exception: {e}. Falling back to default start')
        try:
            webview.start()
        except Exception as e2:
            write_log(f'Fallback webview.start also failed: {e2}')


if __name__ == '__main__':
    main()

