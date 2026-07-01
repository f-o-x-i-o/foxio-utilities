---
name: vcv-rack-dsp-module-dev
description: Desarrollar un módulo DSP para VCV Rack 2 en C++ end-to-end — arquitectura del core portable, build/deploy/troubleshooting del plugin, panel y widgets, disciplina de testing (capas, asserts analíticos, auditoría de tests zombi) y gotchas de sesiones largas con agente de código. Usala al empezar o mantener un módulo de Rack, cuando el módulo "no aparece / no refleja cambios", cuando el panel o los sliders hacen algo raro, o al montar/auditar la suite de tests del DSP.
---
<!-- foxio-library
saved: 2026-07-01
from:  /Users/simon/Development/VCV/foxio-research (psi-pack, destilada con skill-distiller)
-->


# vcv-rack-dsp-module-dev

El camino completo de un módulo DSP para VCV Rack 2. El 80% del dolor no está en el
DSP: está en que Rack no muestra el módulo, carga un binario viejo, o los tests dan
verde sin validar nada. Esta skill es la receta + las rutinas de diagnóstico.

---

## 1. Arquitectura: el DSP no conoce el host
Regla de oro: **la lógica de DSP no incluye nada del framework.** El plugin de Rack, y
mañana el firmware del micro, son wrappers finos que llaman a la misma primitiva.

- Lógica en **headers puros** (`dsp/*.hpp`), namespace propio, sin `rack.hpp`.
- El módulo VCV hace I/O + params y llama a la primitiva en su loop `process()`.
- Los tests apuntan a la **primitiva**, no al wrapper.

Por qué: portable (el mismo header compila para desktop y Cortex-M7/STM32H7),
testeable sin abrir Rack (`g++` sobre un `main()`), y una sola fuente de verdad para la
lógica compartida entre módulos (el fix se hace una vez).

**Single source of truth para constantes/defaults:** los valores usados en varios lados
(init del módulo, serialización JSON, UI, tests) van en **un struct en el header**
(`struct Defaults {...}`) y todos leen de ahí. Duplicarlos = se desincronizan y los
tests terminan validando un valor que ya no es el de producción (ver §5).

**Estructura del repo:**
```
repo/
  vcv/           # el plugin (Makefile vive ACÁ, no en la raíz)
    src/         # *.cpp de cada módulo + plugin.cpp/plugin.hpp
    res/         # paneles .svg
    plugin.json  # manifest
  dsp/           # DSP puro header-only
    test/        # suites standalone
```

---

## 2. Build, deploy & troubleshooting

**Build loop** (desde `vcv/`, donde está el Makefile):
```bash
make -j$(sysctl -n hw.ncpu)
# si dice "Nothing to be done" pero editaste, forzá el rebuild:
touch src/MiModulo.cpp && make
```

**Deploy:** Rack carga plugins de `~/Documents/Rack2/plugins-<os>-<cpu>/`, NO del
default de `make install` (`~/Library/Application Support/Rack2/...`). Confirmá cuál lee
tu Rack: la carpeta con muchos plugins y el `settings.json` reciente. Arreglá la causa
raíz en el Makefile: definí `RACK_USER_DIR := ~/Documents/Rack2` **ANTES** del
`include plugin.mk` (plugin.mk lo fija con `?=`) y agregá un target `install-local`.
**Rack lee plugins SOLO al arranque** → Cmd+Q completo y reabrir.

**plugin.json — ABI version:** el campo `version` empieza con el major de la ABI de Rack
(`2.`), no con la versión de tu plugin. `0.1.0` → log dice
`does not match Rack ABI version 2` y no carga. Usá `2.x.y`. Declará solo los módulos
que `plugin.cpp` registra.

**Registrar un módulo = 3 lugares:** `plugin.hpp` (`extern Model* modelX;`),
`plugin.cpp` (`p->addModel(modelX);`), `plugin.json` (entrada). Si es un `.cpp` nuevo,
agregalo al Makefile o no se linkea.

**Troubleshooting "no aparece / no veo mis cambios"** (checklist en orden):
1. ¿Reiniciaste Rack? Carga solo al arranque.
2. ¿La carpeta correcta? (`~/Documents/Rack2/...`, no la de `make install`). Comparar
   timestamp/tamaño del `plugin.dylib` deployado.
3. **Binario stale (el gordo):** si hay un directorio `MiPlugin/` extraído Y un
   `.vcvplugin`, Rack **prioriza el directorio extraído** → un build viejo te gana al
   nuevo. `rm -rf` los artefactos viejos y reiniciá.
4. Leé el log: `grep -i mi_plugin ~/Documents/Rack2/log.txt | tail` (dice el error
   exacto: ABI, módulo no registrado, load OK).
5. Browser filtrando: ponelo en "All", no "Favorites".

**Gotchas:** `.vcvplugin` es un **tar.zst** (`tar --zstd -xf`, no unzip). `dist/` se
genera con `make dist`, no con `make` a secas.

---

## 3. Panel (SVG) & widgets
Bugs de UI: compila y hace algo raro. Los recurrentes:

- **Dimensiones en mm, no px.** Ancho del panel = HP × 5.08 mm (1 HP = 5.08 mm). Poner
  px hace un módulo enano con los elementos laterales fuera del borde ("knobs cortados").
- **nanoSVG no renderiza `<text>`.** Los labels del SVG no aparecen → dibujalos en C++
  con `nvgText` en un Widget. El SVG queda solo para gráfica.
- **Sliders/knobs que no modulan → `Quantity`.** El default de
  `getMinValue()/getMaxValue()` es **[0,1]**; sin override, el slider ignora tu rango
  real. Implementalos con `override` (ojo: *esos* nombres, no `getMin/getMax`). Para
  selección discreta usá un switch físico (`CKSSThree`), no un knob sobre [0,1] con snap
  (da solo 2 posiciones).
- **Tooltips con unidad real:** `ParamQuantity` custom en `getDisplayValueString()` si el
  knob guarda un normalizado pero querés mostrar Hz/ms.
- **Revisar layout antes de compilar:** renderizá el SVG a PNG y miralo:
  `pip3 install cairosvg; python3 -c "import cairosvg; cairosvg.svg2png(url='res/P.svg', write_to='/tmp/p.png', scale=2.5)"`.
- **Componentes del SDK:** `grep -n "HugeKnob\|CKSSThree" $RACK_DIR/include/componentlibrary.hpp`.
- Clock/gate de salida: VCV usa 0–10V. Detección de clip: chequeá el valor **pre-clamp**.

---

## 4. Testing: capas + asserts que se sostienen
"Suena bien" no es un assert. Un core DSP necesita capas distintas (no las mezcles):

- **Fidelidad / calibración** — ¿reproduce el modelo/ciencia? Compara vs la referencia.
- **Sanidad de software** — NaN/Inf, denormals, determinismo bit-exact, reset idempotente,
  estabilidad. **Crítico si el core va a firmware.**
- **Caracterización de señal** — THD/SNR/frecuencia (AES17 adaptado a tu caso).

Cada suite es un binario `g++ -std=c++17 -O2 -Wall` que incluye el header puro (sin el
host) y emite un **HTML con waveforms** además del pass/fail → separás "bug en el DSP"
de "bug en el wrapper/binario deployado". Ante duda de un parámetro, **micro-experimento
medido** (un `/tmp/x.cpp` que incluye el header real), no adivines.

**Assert analítico > proxy con umbral (lo importante):**
Síntoma: un test de propiedad cualitativa ("más caótico / complejo / energético") pasa o
falla según un umbral que vas tuneando, y depende de *dónde/cómo* medís.
El movimiento:
1. **Apagá todo lo que ensucia** (ruido, acoplamientos, otros términos) para aislar UN
   término del modelo.
2. **Derivá en papel** qué valor exacto debe dar bajo esas condiciones.
3. **Asertá ese valor** con epsilon de float, no `> umbral`.
Ganás robustez (sin umbral mágico), diagnóstico (si rompe, se rompió *ese* término) y el
test documenta el modelo.
> Ejemplo (psi-pack): en vez de "el output es más complejo con Ψ alto" (fallaba con
> Lempel-Ziv, dependía de qué sample medías), se apagó noise y coupling para aislar el
> término de ganancia `(1 + α·Ψ)`; con α=1 la amplitud tiene que duplicarse exacto →
> assert `RMS(Ψ=1)/RMS(Ψ=0) == 2.0`. Sirve para cualquier término lineal aislable.

Métricas de frecuencia: la autocorrelación con ventana ancha engancha el 2× período /
subarmónicos; para DFT usá ventana = múltiplo entero del período (si no, leakage).
Separá lo que probás: precisión de fase (corto plazo, no acumules 48k sumas float) vs
frecuencia (largo plazo, zero-crossings).

**Auditar tests que dan falsa confianza (zombis).** Un test que pasa sin validar
producción es peor que uno que falla. Patrones:
- **Tautológico:** redefine la constante y la compara consigo mismo, sin leer el código.
- **Se prueba a sí mismo:** testea una lambda/función local que no existe en producción.
- **Trivial:** aserta algo siempre verdadero (monotonía de interpolación lineal).
- **Config distinta a producción:** valida con N=5 cuando shippeás N=7.
- **Comentario mentiroso:** dice "scan tauD" pero el código usa tauD fijo.
Auditoría: cruzá **spec/paper (primario) ↔ código de producción ↔ test**; el test debe
*leer* la constante del código real (no redefinirla), correr la config que shippeás, y
poder fallar. La causa raíz casi siempre es duplicación → centralizá en el struct único
de §1.

**Regresión post-integración:** tras integrar el core al host, corré **todas** las
suites, no solo la que tocaste. La integración es donde se rompe algo en silencio.

---

## 5. Gotchas de sesión larga con agente de código
- **"File has not been read yet" tras compactación:** los `Read` de la ventana anterior
  no cuentan; re-Read antes de `Edit`/`Write`.
- **Edit "string not found" con unicode** (box-drawing │, griego α/β/ψ): los `\uXXXX` no
  matchean; re-Read y copiá el texto exacto.
- **Recuperar un valor/decisión perdida:** `git show <commit>:ruta | grep ...`; para
  probar una versión vieja sin tocar la rama, `git worktree add /tmp/vieja <commit>`.
- **Shell macOS/zsh:** `cat` no tiene `-A` (usá `-v`); zsh expande `--include=*.cpp`
  (pasá dirs explícitos); paréntesis en `git commit -m` rompen bajo zsh (comillas simples,
  sin paréntesis). Corré cada comando desde el CWD correcto (build en `vcv/`, tests en
  `dsp/test/`).

---

## Validado en
psi-pack / Foxio Research (github.com/f-o-x-i-o/psi-pack): módulos PsiLFO, Abstractor→RIFT
(VCV Rack 2, C++17, core portable a STM32H7). Todos los fallos de instalación (carpeta,
binario stale, ABI), de panel (mm, nvgText, Quantity), de tests (Lempel-Ziv→ratio-2.0,
tests zombi A7/A10/A12, N=5-vs-N=7) y de sesión se repitieron a lo largo del desarrollo.
