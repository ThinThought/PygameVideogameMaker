# Pygame App Template

## Estructura y flujo del proyecto

Este proyecto funciona como **plantilla base para juegos y aplicaciones en Pygame**, pensada para ejecutarse tanto en PC como en consolas retro compatibles con Pygame.

La arquitectura se divide en tres capas principales: **core**, **scenes** y **entities**.
Cada capa tiene responsabilidades claras y límites definidos.

---

## 1. Core

El **core** contiene el bucle principal del programa y la inicialización global.

Aquí es donde:

* Se inicializa Pygame y sus subsistemas
* Se carga la configuración desde `settings.toml`
* Se crea la ventana (resolución, FPS, etc.)
* Se controla el ciclo principal (`handle_event → update → render`)
* Se gestiona el `clock` y el `dt`
* Se delega el control a la escena activa
* Se inicializan sistemas globales (audio, recursos, debug, etc.)

### Convención importante sobre el tiempo

El `dt` que se pasa a las escenas **siempre representa el tiempo transcurrido en segundos** (`float`).

```python
dt = clock.tick()  # segundos
```

👉 **Nunca se usan milisegundos en la lógica del juego**.
Si alguna librería externa necesita milisegundos (por ejemplo, `pygame.mixer`), la conversión se hace explícitamente.

---

### 👉 Cuándo modificar el core

Solo cuando necesites:

* Cambiar el comportamiento global del juego
* Añadir sistemas transversales (audio manager, input global, debug, etc.)
* Alterar el loop principal
* Ajustar cómo se gestionan escenas o recursos

Si estás añadiendo gameplay, **probablemente no necesitas tocar el core**.

---

## 2. Scenes

Las **scenes** representan los distintos estados o pantallas del juego: menú, juego, pausa, loading, tests, etc.

Cada escena:

* Maneja sus propios eventos
* Actualiza su lógica usando `dt` (en segundos)
* Dibuja su contenido
* Decide cuándo cambiar a otra escena
* Controla qué audio se reproduce al entrar o salir

La plantilla incluye escenas de prueba (por ejemplo, `BlankScene`, `AssetsTestScene`) que sirven como referencia y entorno de experimentación.

### Ciclo de vida de una escena

```text
on_enter → handle_event → update → render → on_exit
```

👉 `on_enter` y `on_exit` son los lugares correctos para:

* Arrancar o parar música
* Inicializar o limpiar recursos propios de la escena
* Resetear estado interno

---

### 👉 Cuándo crear o modificar una escena

* Cuando quieras añadir una nueva pantalla o modo
* Cuando cambie la lógica principal del juego
* Para separar responsabilidades y evitar lógica monolítica
* Para aislar pruebas (assets, input, rendimiento, etc.)

Regla simple:
**si cambia lo que ve o hace el jugador, probablemente es una escena nueva**.

---

## 3. Entities

Las **entities** son los elementos vivos del juego: jugador, enemigos, objetos, UI, animaciones, etc.

Una entity:

* Tiene estado propio
* Se actualiza cada frame
* Se dibuja dentro de una escena
* No conoce el loop global ni otras escenas directamente
* No controla audio ni escenas por sí misma

👉 Las escenas **orquestan**, las entities **actúan**.

---

### 👉 Cuándo crear o modificar entities

* Para añadir comportamiento reutilizable
* Para encapsular lógica concreta
* Para evitar código duplicado dentro de las escenas
* Para mantener las escenas legibles y pequeñas

Si una escena empieza a crecer demasiado, probablemente necesitas entities.

---

## Audio y multimedia

El audio se gestiona exclusivamente a través del **AudioManager**, inicializado en el core y accesible desde las escenas.

* La música y los efectos de sonido están separados
* El control de audio pertenece a las escenas, no a las entities
* Los tiempos de fade se expresan explícitamente en milisegundos (`fade_ms`)

### Sobre vídeo

Pygame **no es un motor multimedia completo**.
El soporte de vídeo es experimental y está pensado solo para:

* Tests de assets
* Prototipos
* Fondos animados simples

Para gameplay y escenas importantes, se recomienda usar:

* Animaciones
* Spritesheets
* Secuencias de imágenes

El vídeo **no es un pilar del engine**.

---

## Configuración: `settings.toml`

Toda la información relacionada con la ventana y el rendimiento debe definirse en `settings.toml`.

En este archivo se especifica, entre otros:

* Resolución de pantalla
* FPS objetivo
* Opciones generales de ejecución

👉 **No hardcodees resolución ni FPS en el código**.
Cualquier ajuste de pantalla debe hacerse aquí para garantizar portabilidad entre PC y consolas.

---

## Dependencias y vendor bundle

El proyecto utiliza un **vendor bundle** para incluir dependencias de Python junto al juego.

El archivo `make_vendor` define **qué paquetes se incluyen**.

👉 **Cuándo modificar `make_vendor`**

* Cuando añadas una nueva dependencia externa
* Cuando elimines librerías que ya no se usan
* Cuando quieras controlar explícitamente qué entra en el bundle final

Tras modificar este archivo, debes regenerar el vendor bundle antes de copiar el juego.

---

## Despliegue en consola

Una vez preparado el proyecto:

1. Verifica que el vendor bundle está actualizado
2. Copia la carpeta del juego a la consola en:

```
/roms/pygame
```

No es necesario ningún paso adicional.
La consola detectará el proyecto y podrá ejecutarse directamente.

---

## Filosofía de la plantilla

Esta plantilla está pensada para:

* Iterar rápido
* Mantener el código legible
* Separar claramente responsabilidades
* Facilitar el despliegue en hardware limitado
* Evitar “ingeniería prematura”

Empieza simple.
Cuando algo duela, **ahí es donde se refactoriza**.