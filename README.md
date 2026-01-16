# Kono Transcriptor

Transcribe archivos de audio a texto usando modelos Whisper (locales).

Kono transcriptor es interfaz de escritorio con `pywebview` que llama a `kono-transcriptor.py`; usa `openai-whisper` para la transcripción, `pydub` opcionalmente para trocear audio y `pyperclip` para copiar resultados.

Puedes probar versiones precompiladas desde la sección "Releases" del repositorio.

![Captura de pantalla](imgs/Captura%20de%20pantalla%202026-01-16%20020813.png)

Dependencias: ver `requirements.txt` (`pywebview`, `openai-whisper`, `pydub`, `pyperclip`)
