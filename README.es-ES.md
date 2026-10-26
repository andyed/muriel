

<p align="center">
  <picture>
    <source srcset="assets/logo-animated-dark.gif" media="(prefers-color-scheme: dark)">
    <img src="assets/logo-animated.gif" alt="muriel — multi-channel visual production for LLM agents" width="720">
  </picture>
</p>

# muriel

**muriel es una habilidad (skill) de Claude Code que produce artefactos visuales en dieciséis canales — catorce de salida y dos de referencia cruzada entre canales — aplicando un mínimo de contraste 8:1 y una disciplina de tokens de marca en tiempo de renderizado.** Los tokens de diseño se importan desde `design.md` y se exportan a W3C DTCG; un agente de crítica basado en visión audita la salida; el piso de contraste nunca cede.

Un único archivo de habilidad (`SKILL.md`) enseña al agente a generar cada artefacto visual que un investigador-diseñador-ingeniero despliega: desde archivos fuente de texto que se difuminan en git y se regeneran a partir de datos. La disciplina de restricciones (contraste 8:1, paleta OLED, un solo tratamiento tipográfico, generado > dibujado, reproducible > puntual) permanece *activa* en tiempo de renderizado: los tokens de marca se analizan, el contraste se audita y las dimensiones se aplican; no como una validación (lint) posterior, sino como parte del acto de creación.

### Proyectos derivados — intercambia los tuyos por favoritos

muriel es la base de [marginalia](https://github.com/andyed/marginalia) (llamados editoriales y maquetación de revistas, citados a lo largo de [`channels/web.md`](plugins/muriel/skills/compose/channels/web.md)) y [iblipper](https://github.com/andyed/iblipper2025) (tipografía cinética y animación de vocabulario emocional, citados en [`vocabularies/kinetic-typography.md`](plugins/muriel/skills/compose/vocabularies/kinetic-typography.md)). Ambos surgieron de la misma disciplina de restricciones y se incluyen como valores predeterminados aquí porque están ajustados para cumplir con las reglas de muriel directamente.

**Son valores predeterminados, no requisitos.** La disciplina de restricciones — contraste 8:1, paleta OLED, un solo tratamiento tipográfico, tokens de marca activos en tiempo de renderizado — es el eje central. Las bibliotecas específicas son preferencias. Intercambia tu biblioteca editorial favorita, motor de tipografía cinética, renderizador de gráficos, cargador de guías de estilo, proveedor de generación de imágenes o rasterizador; las opiniones de muriel tratan sobre *qué* restricciones se mantienen, no *cuál* biblioteca las aplica. Cada documento de canal nombra la biblioteca que asume, y ninguna de esas suposiciones es un requisito estricto frente a un sustituto razonable.

### Construido sobre / se integra con

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776ab?logo=python&logoColor=white)
![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d97757)
![GitHub Release](https://img.shields.io/github/v/release/andyed/muriel?logo=github&color=181717)

**Python channels**
![Pillow](https://img.shields.io/badge/Pillow-raster-informational)
![matplotlib](https://img.shields.io/badge/matplotlib-figures-11557c?logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-capture-45ba4b?logo=playwright&logoColor=white)
![svgwrite / cairosvg](https://img.shields.io/badge/svgwrite_%2F_cairosvg-SVG-orange)

**Editorial**
![marginalia](https://img.shields.io/badge/marginalia-editorial-e6e4d2?labelColor=0a0a0f)
![pandoc](https://img.shields.io/badge/pandoc-markdown-373737?logo=markdown&logoColor=white)
![WeasyPrint](https://img.shields.io/badge/WeasyPrint-HTML%E2%86%92PDF-000)

**Interactive / graphics**
![WebGL](https://img.shields.io/badge/WebGL-rendering-9b35d3)
![D3.js](https://img.shields.io/badge/D3.js-linked_displays-f68e56?logo=d3dotjs&logoColor=white)
![PixiJS v8](https://img.shields.io/badge/PixiJS-v8-e72264?logo=pixijs&logoColor=white)
![pretext](https://img.shields.io/badge/pretext-typography-666)

**Diagrams / video**
![Mermaid](https://img.shields.io/badge/Mermaid-diagrams-ff3670?logo=mermaid&logoColor=white)
![Excalidraw](https://img.shields.io/badge/Excalidraw-sketch_exports-6965db)
![FFmpeg](https://img.shields.io/badge/FFmpeg-video-007808?logo=ffmpeg&logoColor=white)

## Canales

Catorce canales de salida, cada uno con su propio subarchivo bajo [`channels/`](plugins/muriel/skills/compose/channels/):

- **Raster** (Pillow + `typeset.py`) — almacena activos, iconos, banners, marcas tipográficas, diseños de capturas de pantalla
- **Vector / SVG** (`svgwrite`, `cairosvg`, Mermaid, Excalidraw) — figuras para publicaciones, diagramas impulsados por datos, iconos escalables, diagramas de flujo
- **Web** (marginalia + Playwright + weasyprint) — entradas de blog, llamados editoriales, maquetación de revistas, captura DOM → PNG/PDF
- **Interactivo** (WebGL / Canvas / D3 / PixiJS) — demostraciones en vivo con controles deslizantes de parámetros, andamios de interfaz de ciencia ficción
- **Vídeo** (ffmpeg + `desktop-control` + hyperframes) — demostraciones de producto, GIFs, composiciones HTML → MP4
- **Terminal** (gráficos Unicode vía `chart.py`) — sparklines, gráficos de barras, tablas
- **Visualización de densidad** (`typeset.render_heatmap()`) — mapas de calor de fijación tipo Tobii
- **Gráficos de mirada** — escaneo de ruta, burbujas de escaneo, línea de tiempo de AOI, rosa de sacádicas, acercamiento-retirada
- **Ciencia** (matplotlib + LaTeX + `muriel.stats`) — figuras para publicaciones, maquetación de cuadernos, informes APA
- **Gráficos** (Recharts / ECharts / Chart.js / Plotly / D3) — guía de bibliotecas de gráficos JS con 22 reglas numeradas, detección de antipatrones y tokens de color estrictos 8:1 de muriel. matplotlib vive en **Ciencia**. Ver [`channels/charts.md`](plugins/muriel/skills/compose/channels/charts.md).
- **Infografías** (SVG determinista) — explicadores de imagen única, 10 tipos × patrones de maquetación × paletas seguras para daltónicos
- **Diagramas** (SVG determinista) — primitivas retóricas: matriz 2×2, ciclo de N pasos, Venn incluido, además de puentes Mermaid → SVG/ASCII y TeX → SVG (MathJax); comparación por pares, embudo, pila, DAG, espectro, pirámide, cuadrícula de calor en cola. Cada configuración lleva una precondition epistemológica + antiprescripción
- **Espacial** (`muriel.spatial` + `render_assets/`) — andamiaje de profundidad para tipografía en capas + topología de campos escalares. Cuadrículas de perspectiva SVG estáticas (1pt / 2pt / 3pt / iso) donde `grid()` andamia *espacio*, más `ridgemap()` — una primitiva hermana que andamia *campos escalares* como rebanadas 1D apiladas (linaje de pulsar plot de Joy Division / Harold Craft 1970). Los ejemplos de Three.js + CSS3DRenderer comparten una biblioteca auxiliar. Linaje Cooper VLW / Mackinlay-Robertson-Card / Dumais Data Mountain. Ver [`channels/spatial.md`](plugins/muriel/skills/compose/channels/spatial.md).
- **Pulido** (CSS / TSX / disciplina de microinteracción HTML) — pulido de IU + reglas de detalle visual: radio de borde concéntrico (`outer = inner + padding`), alineación óptica, sombras sobre bordes, escala al presionar (`0.96`, nunca por debajo de `0.95`), animaciones de iconos contextuales (`scale 0.25→1` + `blur 4px→0` + `bounce: 0`), área de clic de 40×40px, sin `transition: all`, números tabulares, `text-wrap: balance` / `pretty`, suavizado de fuentes macOS. 16 reglas numeradas, extraídas de [thedavidmurray/claude-make-interfaces-feel-better](https://github.com/thedavidmurray/claude-make-interfaces-feel-better) (MIT, archivado) con el piso de contraste 8:1 de muriel aún vinculante. Ver [`channels/polish.md`](plugins/muriel/skills/compose/channels/polish.md).

Más dos referencias cruzadas entre canales usadas por cada canal:

- **Dimensiones** ([`channels/dimensions.md`](plugins/muriel/skills/compose/channels/dimensions.md)) — tarjetas sociales, huellas de dispositivo, niveles de viewport, tamaños de papel, resoluciones de vídeo
- **Guías de estilo** ([`channels/style-guides.md`](plugins/muriel/skills/compose/channels/style-guides.md)) — esquema de `brand.toml`, tokens de movimiento, derivación de CSS / matplotlibrc, reglas de propiedad. Vuelta completa a través de la importación de Google Stitch `design.md` (`muriel import`) y exportación a W3C Design Tokens (DTCG) (`muriel export-dtcg`), por lo que brand.toml se conecta con `style-dictionary`, theo, Figma tokens-studio, token-css y las canalizaciones iOS / Android / Tailwind aguas abajo.


## Filosofía — resolución multirrestringida

muriel es un solver multirrestringido para la producción visual. Las herramientas son nativas de LLM (formato de habilidad, crítica de modelo de visión, tokens de marca vivos en tiempo de renderizado, movimiento como un campo de esquema de primer nivel, adaptadores de motor para Pillow / Flux / pretext / ffmpeg / Playwright). Los principios son más antiguos: Visible Language Workshop de Cooper, disciplina de tinta de datos de Tufte, ranking de variables retinianas de Bertin, agrupación Gestalt, maquetación CRAP, E-Z Reader de Reichle, patrones de escaneo de la ciencia de la visión. Las herramientas sirven a los principios.


## Instalación

> **Dónde viven las cosas.** La fuente canónica de la habilidad es [`plugins/muriel/skills/compose/SKILL.md`](plugins/muriel/skills/compose/SKILL.md). La raíz del repositorio `.claude-plugin/` solo contiene `marketplace.json`; el manifiesto propio del complemento vive en [`plugins/muriel/.claude-plugin/plugin.json`](plugins/muriel/.claude-plugin/plugin.json) (no se necesita un manifiesto de nivel raíz cuando la `source` del marketplace apunta a un subdirectorio). El enlace simbólico `.agents/skills/muriel` confirmado es un puente intencional entre arneses (ver *Otros arneses de IA* a continuación), no una copia suelta.

### Como un complemento de Claude Code (recomendado)

Desde cualquier sesión de Claude Code:

```text
/plugin marketplace add andyed/muriel
/plugin install muriel@andyed-muriel
```

Eso es todo: sin clonar, sin enlaces simbólicos. `/plugin uninstall` revierte limpiamente. Invócalo con `/muriel:compose` (las habilidades del complemento están en espacio de nombres; el prefijo `muriel:` previene colisiones con otros complementos). El subagente `muriel-critique` se carga junto con la habilidad.

### Como una habilidad de Claude Code (instalación para desarrolladores)

Si estás trabajando en el repositorio de muriel mismo, instala desde un checkout para que los cambios aparezcan en vivo:

```bash
git clone https://github.com/andyed/muriel ~/Documents/dev/muriel
cd ~/Documents/dev/muriel && ./install.sh
```

El script crea exactamente dos enlaces simbólicos de directorio — `plugins/muriel/skills/compose/` → `~/.claude/skills/muriel` (para que la invocación bare `/muriel` siga funcionando) y `plugins/muriel/agents/` → `~/.claude/agents/muriel`. Un enlace simbólico por cada uno es intencional: un nuevo canal, referencia o asiento de jurado aparecerá en la instalación en vivo en el momento en que se añada al checkout, sin necesidad de volver a ejecutarlo. Claude Code escanea `~/.claude/agents/` de forma recursiva e identifica un subagente por su frontmatter `name:` en lugar de su ruta, por lo que el montaje único de agentes registra cada asiento.

El script verifica a dónde apunta realmente un montaje existente en lugar de asumir que cualquier cosa presente es correcta. Un enlace simbólico que posee se reencadena automáticamente. Un montaje por elemento heredado — un directorio real de enlaces simbólicos individuales, que nunca recopila directorios añadidos posteriormente — se informa y se deja solo hasta que vuelvas a ejecutar con `--repair`, lo cual lo mueve a `muriel.bak-<timestamp>` antes de reemplazarlo. Nada se elimina.

Se niega de plano si la instalación del complemento ya está presente, para evitar una doble carga.

### Como un paquete de Python

```bash
pip install -e ~/Documents/dev/muriel   # instalación desde fuente (editable)
# pip install muriel                    # PyPI — aún no publicado; sigue vía GitHub Releases
pip install https://github.com/andyed/muriel/releases/download/v0.11.0/muriel-0.11.0-py3-none-any.whl
```

Luego, desde cualquier script o notebook:

```python
from muriel import matplotlibrc_dark            # auto-aplica un matplotlibrc OLED al importar
from muriel.stats import format_comparison      # ayudantes de informes estilo APA
from muriel.contrast import audit_svg           # auditoría WCAG 8:1, módulo + CLI
from muriel.styleguide import load_styleguide   # cargador de brand.toml con alias + movimiento
from muriel.dimensions import figsize_for, OG_CARD
```

### Como una CLI

Después de `pip install`, el comando `muriel` despacha a cada subcomando:

```bash
muriel                              # listar subcomandos
muriel capture https://example.com  # barrido de capturas de pantalla responsivas
muriel contrast audit page.svg      # auditoría WCAG 8:1
muriel dimensions                   # imprimir el registro de dimensiones
muriel heroshot in.png out.png --tilt 12 --brand brand.toml --target og.card
muriel tilt-shift raw.png hero.png  # desenfoque de profundidad de campo de lente falso
muriel venn spec.json out.png       # diagrama de Euler proporcional por área
muriel styleguide brand.toml --css  # derivar propiedades CSS :root personalizadas
```

Cada subcomando también es invocable directamente vía `python -m muriel.capture`, `python -m muriel.tools.heroshot`, etc.

### El agente de crítica

El subagente `muriel-critique` se entrega con el complemento y se carga automáticamente mediante ambas rutas de instalación anteriores (instalación de complemento y `install.sh`). Despáchalo desde cualquier sesión de Claude Code con la herramienta de Agente, `subagent_type: muriel-critique`. Ver [Agente de crítica](#agente-de-crítica) a continuación. Cinco asientos de jurado se entregan y cargan de la misma forma — `muriel-squinter` (jerarquía bajo desenfoque), `muriel-thumbnail` (señal en 1/8 y 16 px), `muriel-stranger` (legibilidad de premisa, brief oculto), `muriel-forger` (distinguibilidad de falsificaciones) y `muriel-pedant` (etiquetas, unidades, afirmaciones numéricas) — cada uno despachado como `subagent_type: muriel-<asiento>` y gobernado por [`references/jury.md`](plugins/muriel/skills/compose/references/jury.md). Siéntalos como subagentes: la denegación de evidencia es aislamiento de contexto, no una instrucción de prompt.

### Otros arneses de IA (Cursor, Codex, Gemini CLI, GitHub Copilot, Kiro, OpenCode, Pi, Qoder, Rovo Dev, Trae, …)

El `SKILL.md` canónico en `plugins/muriel/skills/compose/SKILL.md` usa el formato [Agent Skills](https://github.com/anthropics/claude-code/blob/main/docs/skills.md) que es portable entre la mayoría de arneses de agentes. El repositorio incluye un enlace simbólico `.agents/skills/muriel` a la fuente canónica — leído **nativamente** por Codex CLI y como una **ruta alternativa** por Cursor, Gemini CLI, GitHub Copilot, OpenCode y Pi. La verificación por arnés está incompleta; ver [`HARNESSES.md`](HARNESSES.md) para el plan de implementación y la lista de verificación. Kiro, Qoder, Rovo Dev y Trae necesitan adaptadores de manifiesto por arnés (P1, aún no implementados).

## Dependencias (por canal)

| Canal | Requerido | Opcional |
|---|---|---|
| Raster | Python 3, Pillow | [`muriel/typeset.py`](muriel/typeset.py) para plantillas |
| SVG | ninguno (hecho a mano) | `svgwrite`, `drawsvg`, `cairosvg`, `rsvg-convert`, Mermaid CLI, [mcp_excalidraw](https://github.com/yctimlin/mcp_excalidraw) para refinamiento de lienzo en vivo |
| Web (editorial) | marginalia (CDN) | pandoc 3.x para markdown → HTML |
| Web (captura estática) | Playwright *o* weasyprint | headless Chrome |
| Interactivo | navegador moderno | D3, Three.js, p5.js, PixiJS v8 (CDN) |
| Vídeo | ffmpeg (construcción completa: `brew tap homebrew-ffmpeg/ffmpeg`) | hyperframes para HTML → MP4; `desktop-control` para captura automatizada |
| Terminal | Python 3 | [`muriel/chart.py`](muriel/chart.py) |
| Vis. densidad / Mirada | Python 3, Pillow | [`muriel/typeset.py`](muriel/typeset.py) `render_heatmap()` |
| Ciencia | Python 3 | matplotlib, NumPy (para figuras); `muriel.stats` / `muriel.matplotlibrc_{dark,light}` / `muriel.dimensions` usan solo stdlib |
| Infografías | Python 3 | `svgwrite`, `cairosvg` para exportación raster |
| Dimensiones | Python 3 | — (módulo de referencia solo stdlib) |
| Guías de estilo | Python 3 | `tomli` en 3.10 (3.11+ tiene `tomllib`); matplotlib opcional para derivación de rcparams |

## Reglas universales

Codificadas en `SKILL.md` y aplicadas en cada canal:

- **Mínimo de contraste 8:1** en todo texto (calcular ratio WCAG)
- **Elementos decorativos ≥55/255** en fondos oscuros
- **Medir antes de dibujar** (bbox / viewBox / getBoundingClientRect)
- **Paleta OLED:** crema sobre negro casi puro, no blanco puro
- **Generado > dibujado.** Si los datos pueden impulsarlo, deben hacerlo.
- **Reproducible > puntual.** Guarda el script junto con la salida.

## Agente de crítica

muriel incluye un agente de crítica basado en modelo de visión en [`plugins/muriel/agents/muriel-critique.md`](plugins/muriel/agents/muriel-critique.md). Lee un artefacto renderizado y nombra — con evidencia — cada forma en que el artefacto falla las reglas de muriel, antipatrones de canal y (opcionalmente) los tokens de un `brand.toml`. Herramientas de solo lectura (Read / Glob / Grep), endurecidas contra inyección de prompt, lavado de insignias y falsificación de afirmaciones de contraste incrustadas en la imagen misma. Los asientos de jurado difieren. `muriel-squinter`, `muriel-thumbnail` y `muriel-pedant` añaden Bash para sus herramientas de lente (`muriel.squint` para los dos primeros, extracción basada en grep para el tercero). `muriel-forger` lleva Write más una salida de renderizado documentada porque su método completo es construir una falsificación y renderizarla; su salida aterriza en `render_assets/forgery/<decisionId>/`, que está gitignored. `muriel-stranger` mantiene solo Read y Bash a propósito: su lente es un solo pase sobre el artefacto con el brief oculto, y cada herramienta adicional es una forma de perder eso.

**Instalación:** el subagente se entrega con el complemento muriel y se carga automáticamente mediante ambas rutas de instalación en [Instalación](#instalación) anteriores (instalación de complemento vía `/plugin install muriel@andyed-muriel` y la ruta de desarrollador `install.sh`). No se requieren enlaces simbólicos manuales. Si `subagent_type: muriel-critique` falla al resolverse, verifica a dónde apunta el montaje — `ls -la ~/.claude/agents/muriel` — y vuelve a ejecutar `./install.sh --repair`.

**Invocar** desde cualquier sesión de Claude Code:

> "Ejecuta muriel-critique en `path/to/artifact.png` con el canal `raster` y la marca `examples/muriel-brand.toml`."

**Salida:** una crítica en markdown estructurada con un veredicto (`PASS` / `NEEDS REVISION` / `FAIL`), una lista numerada de problemas (regla / evidencia / corrección, etiquetada por gravedad) y una justificación. Gravedad CRITICAL → FAIL; cualquier HIGH → NEEDS REVISION; de lo contrario PASS.

**Fijaciones de regresión:** artefactos adversarios y basales para el agente de crítica viven en [`examples/critique-fixtures/`](plugins/muriel/skills/compose/examples/critique-fixtures/) con sus veredictos esperados. Contribuye nuevos ataques allí — cualquier CVE para sistemas de críticos visuales puede ser un pull request de un párrafo.

## Galería / Showcase

- **[muriel.mindbendingpixels.com](https://muriel.mindbendingpixels.com)** — la propia página de aterrizaje y galería de muriel. Seis exposiciones de "Trabajo destacado" que abarcan ciencia, infografías, gráficos de mirada y registros de paneles; un sintonizador de movimiento interactivo para los tokens de duración + aceleración de la marca; documentos de instalación + agente de crítica en forma condensada. Construido con muriel, alojado en el subdominio mindbendingpixels. Paleta OLED en todo el sitio, cumpliendo el piso de 8:1 que cada documento de canal aplica.
- **[Scrutinizer — Brand & Perceptual Tokens](https://andyed.github.io/scrutinizer-www/tokens/)** — Página en vivo que usa muriel de extremo a extremo: la Guía de Estilo [`scrutinizer-brand.toml`](plugins/muriel/skills/compose/examples/scrutinizer-brand.toml), la primitiva [`foveal_overlay`](muriel/tools/diagrams/foveal_overlay.py) (puerto de la superposición de la app), la primitiva [`engine_sectors_overlay`](muriel/tools/diagrams/engine_sectors_overlay.py) (sectores corticales isotrópicos de Blauch et al. 2026), el módulo [`palettes`](muriel/palettes.py) (Wong / IBM / Tol) y las constantes de contraste/dimensión. La página también expone las constantes de decaimiento perceptual de Scrutinizer (SIGMA_LM, SIGMA_BY, CMF_A, etc.) para diseñadores que construyen IU consciente de lo periférico. Primer artefacto público de la integración muriel + Scrutinizer.

## Arte anterior relacionado

- **[anthropics/skills](https://github.com/anthropics/skills)** (Apache-2.0) — El monorepo oficial de habilidades de Anthropic. Diecisiete habilidades que cubren la amplitud de superficies de agentes, de las cuales siete entran en el territorio de muriel: **`brand-guidelines`** (siete colores de marca de Anthropic + tipografía Poppins/Lora aplicada vía python-pptx; el ejemplo canónico de aplicación de marca de paleta única + par tipográfico único), **`theme-factory`** (diez temas nombrados — Ocean Depths, Sunset Boulevard, Forest Canopy, Modern Minimalist, Golden Hour, Arctic Frost, Desert Rose, Tech Innovation, Botanical Garden, Midnight Galaxy — más una ruta de tema personalizado "pregunta al usuario, vibra y genera uno similar"), **`canvas-design`** (arte visual PNG/PDF con un directorio personalizado `canvas-fonts`), **`frontend-design`** (plantillas UI/UX), **`web-artifacts-builder`** (artefactos HTML con React + Tailwind), **`algorithmic-art`** (generativo p5.js con aleatoriedad sembrada), **`slack-gif-creator`** (GIFs animados con restricción de tamaño). muriel se posiciona en la misma superficie pero con restricciones más estrictas: 11 paletas vs 1, texto seguro/decorativo exclusivo de dos niveles vs sin control, generación de contraste por construcción (`muriel.palettes.generate_for_floor()`) vs elegir de un menú, piso 8:1 vs sin garantía de contraste, tokens de movimiento en `brand.toml` vs sin vocabulario de movimiento, canalización de auditoría vs aplicar y entregar. Anthropic entrega amplitud (17 habilidades en muchos dominios); muriel entrega profundidad en este. Línea base útil para posicionar cualquier nueva característica de muriel.
- **[pbakaus/impeccable](https://github.com/pbakaus/impeccable)** (Apache-2.0, **Skill 3.1.1**, mayo 2026) — Habilidad de diseño de código abierto de Paul Bakaus para arneses de programación con IA, extendida desde la habilidad frontend-design original de Anthropic. Ahora incluye siete archivos de referencia de dominio (Tipografía, Color y Contraste, Espacial, Movimiento, Interacción, Responsivo, Redacción UX), veintitrés comandos `/impeccable:*` (`craft`, `critique`, `audit`, `polish`, `bolder`, `quieter`, `distill`, `harden`, `animate`, `colorize`, `typeset`, `layout`, …), veintisiete reglas deterministas de antipatrones más doce reglas de crítica LLM, y una CLI independiente `npx impeccable detect` (regex + escaneo de captura Puppeteer, sin clave de API requerida) que emite JSON para veinticuatro problemas detectables. Empaquetado en once arneses (Claude Code, Cursor, Codex CLI, Gemini CLI, GitHub Copilot, Kiro, OpenCode, Pi, Qoder, Rovo Dev, Trae). La sección `Absolute bans` de muriel en `channels/web.md` y el antipatrón de fuentes reflexivas se reformulan de impeccable. Donde impeccable es de superficie única + lado JS y entrega su propio detector, muriel es multicanal + nativo Python con un agente de crítica de visión; se complementan — encadenar `muriel capture` → `npx impeccable detect` → `muriel-critique` es la canalización más fuerte para "renderizar → escaneo de reglas estáticas → crítico visual" en una superficie web. La implementación multicanal de muriel en [`HARNESSES.md`](HARNESSES.md) refleja la matriz de empaquetado de impeccable.
- **[nexu-io/html-anything](https://github.com/nexu-io/html-anything)** (Apache-2.0, 4.7k★) — Editor HTML agéntico con ~75 arquetipos de superficie agrupados en nueve familias (decks, frames / movimiento, tarjetas sociales, prototipos web, artículos, docs de oficina / PM, paneles, pósters, especializados), cada uno renderizado como HTML de un solo archivo; exportación con un clic a PNG / WeChat / X / Zhihu. El contemporáneo más cercano a un catálogo de superficies completamente desarrollado — muriel lo cita en lugar de reconstruir la taxonomía. Censado en [`vocabularies/surfaces.md`](plugins/muriel/skills/compose/vocabularies/surfaces.md); patrones extraídos incluyen la forma de frontmatter tipado (`category` / `scenario` / `aspect_hint` / `featured` / `recommended` / `example_source_url`), el patrón de aplicación de "reglas absolutas por superficie" (`deck-swiss-international`'s `border-radius: 0` por todas partes, 22 maquetaciones bloqueadas S01–S22, paleta de 4 temas bloqueada sin modificación hex), pilas de fuentes CJK-first (display Latin + `Noto Sans SC`) y la cadena de linaje "inspirado en" entregada como datos y no como prosa. Mapeo take/keep-ours en la tabla [Habilidades hermanas](plugins/muriel/skills/compose/SKILL.md#sibling-skills--what-we-borrow-from-each). Implementación completa de superficie en cola.
- **[pixijs/pixijs-skills](https://github.com/pixijs/pixijs-skills)** (MIT) — Fuente de verdad para el vocabulario de PixiJS. Subconjunto curado documentado en [`vocabularies/pixijs.md`](plugins/muriel/skills/compose/vocabularies/pixijs.md); upstream es donde vive la profundidad.
- **Habilidad `dataviz` incluida en Claude Code** (Anthropic, incluida en la caja) — la primera habilidad de primera parte en el territorio de muriel para cargarse por defecto (auto-dispara en "chart"/"dashboard"/"palette"). Un canal, deliberadamente neutral en marca: sus docs dicen que intercambies la paleta de tu marca pero no entrega herramientas para ello — que es exactamente lo que es muriel (`brand.toml`, DTCG, contraste por construcción). muriel es más estricto (piso computado 8:1 vs su regla de alivio 3:1) en quince canales más.
- **[caylent/tufte-data-viz](https://github.com/caylent/tufte-data-viz)** (MIT) — Principios de visualización de datos de Edward Tufte como una habilidad de agente: 22 reglas numeradas + referencia rápida por biblioteca para Recharts, ECharts, Chart.js, matplotlib, Plotly, D3/SVG. El modelo estructural detrás de [`channels/charts.md`](plugins/muriel/skills/compose/channels/charts.md) de muriel — portamos la estructura de reglas, tablas de configuración por biblioteca y formato de detección PATTERN→FIX de antipatrones, luego anulamos los tokens de color porque la paleta publicada de Tufte falla el piso 8:1 de muriel (su serie `#666` y acento `#e41a1c` puntúan 5.7 y 4.7). Divergencias específicas registradas en la tabla [Habilidades hermanas](plugins/muriel/skills/compose/SKILL.md#sibling-skills--what-we-borrow-from-each).
- **[K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills)** (MIT) — Familia de habilidades de investigación que cubre matplotlib, análisis-estadístico, pensamiento-crítico-científico, investigación-de-mercado, pptx, markitdown, revisión-de-literatura, generación-de-hipótesis, esquemas-científicos. Varios módulos se superponen con `channels/science.md` de muriel y canales en cola (investigación-de-mercado, pptx). muriel toma vocabulario de selección de pruebas, el bucle de inspección PPTX generar→renderizar→inspeccionar, y la taxonomía de sesgo GRADE/Cochrane; mantenemos nuestro `muriel.stats` de solo biblioteca estándar (sin scipy/pingouin) y auditoría 8:1 en cada figura. Mapeo take/keep-ours en la tabla [Habilidades hermanas](plugins/muriel/skills/compose/SKILL.md#sibling-skills--what-we-borrow-from-each).
- **[matplotlib-venn](https://github.com/konstantint/matplotlib-venn)** — Renderizador de Euler proporcional por área que respalda [`muriel/tools/venn.py`](muriel/tools/venn.py).
- **[geraldnguyen/social-media-posters](https://github.com/geraldnguyen/social-media-posters)** (MIT) — CLI Python + GitHub Actions para *publicar* en X / LinkedIn / Instagram / Threads / Bluesky / YouTube. Queda aguas abajo de muriel: muriel produce la tarjeta OG en las dimensiones correctas, audita el contraste, aplica tokens de marca; social-media-posters la envía. El patrón de despacho de subcomandos del CLI de nivel superior `muriel` se toma de su `social_cli/`.
- **[yizhiyanhua-ai/fireworks-tech-graph](https://github.com/yizhiyanhua-ai/fireworks-tech-graph)** (MIT) — Habilidad de Claude Code que renderiza diagramas SVG de arquitectura técnica (14 tipos UML + diagramas de sistemas AI/agente como pipelines RAG, orquestación multi-agente, flujos de llamadas a herramientas) a partir de descripciones en lenguaje natural. El ejemplo vivo más cercano de generación de diagramas de arquitectura de sistemas; referencia útil a medida que el catálogo [`channels/diagrams.md`](plugins/muriel/skills/compose/channels/diagrams.md) de muriel crece más allá del MVP de matriz + ciclo hacia primitivas DAG causales y de pila.
- **[webadderall/Recordly](https://github.com/webadderall/Recordly)** (AGPL-3.0, app de escritorio — **no incluido**, solo integrado) — App de grabación de pantalla macOS/Windows/Linux con seguimiento automático de zoom del cursor, pulido de cursor, regiones de motion-blur, superposición de webcam y fotogramas estilizados, construida sobre PixiJS. Recomendado aguas arriba de las recetas tooltip-burn + ffmpeg de `channels/video.md` de muriel para vídeos de demostración de producto / walkthrough. AGPL significa que muriel nunca incrusta ni importa Recordly; la integración es puramente hand-off de sistema de archivos/MP4.
- **[yctimlin/mcp_excalidraw](https://github.com/yctimlin/mcp_excalidraw)** (MIT) — Servidor MCP + habilidad de Claude Code que expone 26 herramientas programáticas sobre Excalidraw (crear/mover/alinear/distribuir/agrupar formas, exportar/importar JSON `.excalidraw`, convertir Mermaid, lienzo en vivo en `localhost:3000`). Complementario a muriel: muriel *genera* artefactos SVG/raster determinísticamente desde especificaciones; mcp_excalidraw permite a un agente Claude Code *manipular* diagramas en un lienzo en vivo con el bucle dibujar-observar-ajustar. Se empareja limpiamente con el emisor planificado `muriel.authoring.excalidraw` — muriel escribe el archivo fuente `.excalidraw`, mcp_excalidraw lo abre para refinamiento iterativo, muriel re-audita al reexportar.
- **[thedavidmurray/claude-make-interfaces-feel-better](https://github.com/thedavidmurray/claude-make-interfaces-feel-better)** (MIT, archivado mayo 2026) — Principios de ingeniería de diseño para pulido de IU: tipografía / superficies / animaciones / rendimiento divididos en cuatro archivos de referencia más un índice `skill.md`. El modelo estructural + 16 reglas numeradas detrás de [`channels/polish.md`](plugins/muriel/skills/compose/channels/polish.md) de muriel — portamos todo el conjunto de reglas verbatim porque los valores están *ajustados* (radio concéntrico `outer = inner + padding`, `scale(0.96)` exacto al presionar nunca por debajo de `0.95`, `scale 0.25→1` + `bounce: 0` exacto para cambios de iconos contextuales, área de clic 40×40px, estallido ~100ms entre chunks semánticos) y anulamos añadiendo el piso de contraste 8:1 como puerta vinculante sobre la capa de pulido. Se sienta en un carril diferente a `impeccable` — impeccable ejecuta detección determinista de antipatrones sobre una página renderizada; esto codifica las *recetas* de ingeniería de diseño a las que recurres al autorizar la página.
- **[wrsmith108/visual-prompt-coach](https://github.com/wrsmith108/visual-prompt-coach)** (licencia no especificada) — Habilidad de Claude Code que convierte solicitudes visuales no estructuradas para materiales de cursos técnicos en prompts informados por framework. Opera Dan Roam (6×6 / clasificación SQVID), principios de aprendizaje multimedia de Mayer (coherencia como regla de eliminación, señalización como regla de énfasis), nivelación de diagramas de arquitectura C4, teoría de carga cognitiva (límites de conteo de elementos por conocimiento previo de la audiencia) y Gestalt / CRAP para maquetación. Pregunta hasta **cuatro preguntas de intake** (objetivo de aprendizaje, qué se muestra, conocimiento previo de la audiencia, restricciones) antes de producir el artefacto de prompt — la forma exacta en que la regla de elicitación de restricciones en cola de muriel llegó independientemente, lo cual valida el límite. Carece de una capa de crítica / puntuación aguas abajo; muriel.critique proporciona el complemento natural. El marco de ciencias cognitivas se empareja con [`agents/muriel-critique.md`](plugins/muriel/skills/compose/agents/muriel-critique.md) de muriel y la puntuación de crítica de 5 dimensiones en cola (donde la coherencia / señalización / contigüidad de Mayer podrían convertirse en ejes de evaluación).
- **[dot-Justin/teenage-engineering-ui-ux-skill](https://github.com/dot-Justin/teenage-engineering-ui-ux-skill)** (licencia no especificada) — Habilidad de IU web que genera interfaces en el registro visual de Teenage Engineering a través de *reglas procedimentales* (maquetación de viewport proporcional, tipografía minúscula fina, códigos de producto con guion corto, superficies true-black + warm-white) en lugar de replicación de activos. Enmarca la postura del curador explícitamente como **"inspirado en, no clonado"** — extrae ADN de diseño transferible (lógica de maquetación, jerarquía tipográfica, relaciones de color) mientras excluye activos propietarios (logotipos, dibujos de producto, copy de marca). El formato adopta `DESIGN.md` de Google Labs. Valida la misma postura que muriel toma en `nexu-io/open-design` y el flujo de trabajo del curador en [`SKILL.md`](plugins/muriel/skills/compose/SKILL.md#sibling-skills--what-we-borrow-from-each) — precedente externo útil al explicar la ética de minería de muriel a un nuevo contribuidor.
- **Índices de descubrimiento de habilidades** — Tres registros curados por la comunidad útiles al definir el territorio de muriel o evaluar si un dominio ya está cubierto antes de añadir un canal: [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) (1000+ habilidades, multi-arnés, el índice de mayor señal), [sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) (1,400+ habilidades con un CLI instalador), [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) (curado por la comunidad, enfocado en Claude). La mayoría de las entradas son habilidades de desarrollo puro o productividad — las habilidades que se superponen con muriel son una pequeña minoría. Úsalos para *descubrir* candidatos para la tabla Habilidades hermanas en [`SKILL.md`](plugins/muriel/skills/compose/SKILL.md#sibling-skills--what-we-borrow-from-each); no trates los índices mismos como autoritativos.

## Licencia

MIT. Ver [LICENSE](LICENSE).
