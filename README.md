# Fuentes del video y la página del EGEL Plus (respaldo)

Respaldo del código con el que se generan `index.html` y `EGEL_Plus_FIT.mp4` de la rama `main`.
Esta rama no se publica. Se conserva mientras se migra todo a un solo repositorio.

- `egel/make.py`: arma la animación (escenas, narración `NARR`, tiempos). Base: `egel/base/index.src.html`.
- `egel/make_video_page.py`: arma la página publicada con el reproductor MP4.
- `egel/scenes.html`, `egel/page.html`, `egel/extra.css`: escenas del video, secciones de la página y estilos.
- `egel/img/`: imágenes ya difuminadas. Los documentos originales con datos personales NO están aquí a propósito.
- `tts/render.py`: voz (Kokoro, ef_dora, es-419) y render del MP4 (Playwright + ffmpeg). Config `egel`.

Las rutas dentro de los scripts son las de la sesión original (`/home/claude/...`) y se ajustarán en la migración.
