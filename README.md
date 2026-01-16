# Kono-Transcriptor

Kono-Transcriptor es una herramienta ligera que ayuda a convertir grabaciones de voz y archivos de audio en texto para facilitar la edición, la generación de subtítulos y la postproducción.

## Descripción

Esta aplicación toma archivos de audio (o grabaciones) y genera transcripciones de manera rápida para que editores, periodistas, podcasters y creadores de contenido puedan ahorrar tiempo en la transcripción manual. Incluye opciones básicas para exportar el texto o preparar subtítulos.

## Para quién es

- **Editores de video y audio:** agiliza la creación de subtítulos y la localización de fragmentos.
- **Periodistas y entrevistadores:** facilita la extracción de citas y la edición de entrevistas.
- **Podcasters y creadores de contenido:** obtiene textos listos para publicar o para usar en show notes.

## Características principales

- Transcripción automática de archivos de audio.
- Exportación de texto y soporte para formatos de subtítulos (por ejemplo, SRT) — si aplica.
- Interfaz sencilla para cargar archivos y revisar la transcripción.

## Capturas / Imágenes

![Captura 1](imgs\imgs_readme\captura1.png)

![Captura 2](imgs\imgs_readme\captura2.png)

## Instalación

### Opción 1: Descarga directa

Puedes descargar el archivo ejecutable (.exe) listo para usar desde la sección "Releases" de este repositorio en GitHub. No requiere instalación de Python ni dependencias.

### Opción 2: Instalación manual (Python)

1. Crear un entorno virtual (opcional pero recomendado):

```bash
python -m venv venv
venv\Scripts\activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecutar el script principal:

```bash
python kono-transcriptor.py
```
