# Pygame Videogame Maker

A 2D platformer game creator with a built-in visual editor, built with Pygame.

Este proyecto permite componer escenas con un editor integrado, guardarlas como
composiciones EEI y ejecutarlas directamente.

## Funcionalidades

* **Editor de escenas**: Añade entidades y entornos concretos desde una paleta desplazable, consulta el árbol de escena y edita propiedades compatibles.
* **Viewport ampliado**: La resolución objetivo queda centrada en un espacio de composición más grande. Los elementos pueden situarse fuera del marco de juego; al ejecutar, el juego los recorta según su resolución.
* **Composiciones EEI**: Guarda jerarquía, rutas de clase, transformaciones y estado en archivos `.eei.json` versionados.
* **Marcadores solo del editor**: Los nodos lógicos, como la música, pueden mostrar un marcador seleccionable sin añadir un sprite al juego.
* **Edición con teclado y mando**: Usa el ratón o el cursor virtual y los botones de un mando conectado.
* **Generador de proyectos**: Crea una carpeta nueva con el editor, el runtime, componentes iniciales y una composición vacía.

## Primeros pasos

### 1. Instalar dependencias

Instala las dependencias del proyecto con:

```bash
uv sync
```

### 2. Abrir el editor

Para abrir el editor visual, ejecuta:

```bash
uv run pygame-editor editor
```

Para ejecutar directamente la composición actual, usa `uv run pygame-editor run`.

### Crear un proyecto de videojuego

Desde el repositorio del editor, genera una carpeta de proyecto limpia:

```bash
uv run pygame-editor new MiJuego --output-dir ../juegos
cd ../juegos/MiJuego
uv sync
uv run mi-juego editor
```

El proyecto generado conserva el editor, el runtime y las entidades y
entornos genéricos, pero empieza con una composición vacía. Usa
`uv run mi-juego run` para ejecutar el juego. Consulta
`game/docs/DesarrollarUnJuego.md` para añadir contenido propio y desarrollar sus
mecánicas. Sustituye `mi-juego` por el comando creado a partir del nombre que
hayas elegido.

### Cambiar de escena

Usa **F2** o **Tab** para ir a la siguiente escena; **F1** o **Shift+Tab** para
volver a la anterior. Pulsa **Escape** para cerrar la aplicación.

## Editor visual

El editor permite crear escenas con estas funciones:

* **Resolución objetivo**: Elige 720×480, 1024×768, la resolución del escritorio o introduce un tamaño personalizado. El marco de juego queda centrado en el viewport.
* **Paleta**: Añade entidades y entornos concretos exportados por los módulos del juego. Desplázate por cada columna si no caben todos los elementos; al elegir uno, empieza a arrastrarlo para colocarlo.
* **Espacio de composición**: Selecciona y mueve nodos dentro del viewport ampliado, también fuera del marco de juego. Sus coordenadas se conservan al guardar y jugar.
* **Árbol de escena**: Selecciona nodos desde la jerarquía, consulta su relación padre/hijo y desplázate por composiciones grandes.
* **Inspector de propiedades**: Edita los valores públicos compatibles del nodo seleccionado. Los booleanos cambian al hacer clic; los textos y números se editan con el teclado.
* **Menú contextual**: Haz clic derecho en un nodo para borrarlo, cambiar su orden de renderizado o añadir una entidad o entorno permitido antes o después.
* **Guardar y jugar**: Usa los botones de la barra o **Ctrl+S** para guardar. **Play** guarda la composición y la abre en la escena de juego.
* **Cursor con mando**: Si hay un mando conectado, el stick izquierdo mueve el cursor virtual; A/B hacen clic principal, Y/X clic secundario y el stick derecho desplaza los paneles.

Para mostrar un marcador seleccionable de un objeto lógico sin sprite, define
`EDITOR_MARKER_LABEL` en su clase. El marcador solo se dibuja en el editor.

## Modelo de interacción entidad–entorno (EEI)

El juego se construye con dos componentes principales:

* **Entornos (`Environment`)**: Representan espacios o zonas que aplican reglas a sus entidades hijas. Los incluidos son fondos, fuerzas, música y contenedores vacíos; pueden anidarse bajo entidades.
* **Entidades (`Entity`)**: Objetos del juego como jugadores, plataformas y objetos. Cada entidad pertenece a un entorno y puede contener entornos hijos.

El editor comprueba estas reglas al añadir nodos y guarda la jerarquía en la
composición. Consulta [`game/docs/DesarrollarUnJuego.md`](game/docs/DesarrollarUnJuego.md)
para ampliar el proyecto.

Puedes ajustar el tamaño inicial de ventana, el título, los FPS y la pantalla en
`game/configs/settings.toml`. El editor permite elegir la resolución objetivo
de cada composición.

```toml
[window]
title = "Videogame Maker"
width = 720
height = 480
fps = 60
```

### Controles y mandos

El editor carga etiquetas y asignaciones del mando desde
`game/configs/controllers/generic.toml`. Declara los controles como tablas TOML;
el editor también cuenta con índices predeterminados para botones y ejes.

```toml
name = "Generic Controller"
deadzone = 0.2

[[buttons]]
name = "a"
index = 0
label = "A"

[[axes]]
name = "left_x"
index = 0
```

## Despliegue en consola

Para transferir el juego a una consola compatible, configura `DEPLOY_CONSOLE_IP`
y ejecuta el script:

```bash
bash deploy_to_console.sh
```

El script empaqueta las dependencias y los recursos necesarios y sincroniza el
proyecto por SSH.

## Scripts auxiliares

### Optimizar imágenes PNG

Este script recorta el espacio transparente sobrante de los sprites para
reducir su tamaño.

```bash
# Trim all images in the platforms folder
uv run python scripts/prune_pngs.py game/assets/images/platforms/grass_platforms
```
