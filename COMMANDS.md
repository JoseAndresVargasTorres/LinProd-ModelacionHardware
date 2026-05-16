# Guía de Comandos — LinProd (Proyecto 2)

> Ejecutar todos los comandos desde la **raíz del repositorio**:
> `LinProd-ModelacionHardware/`

---

## 1. Requisitos previos

```bash
# Python 3.8+
python3 --version

# Tkinter (necesario para la GUI)
python3 -c "import tkinter; print('tkinter OK')"
# Si falla:
sudo apt-get install python3-tk

# reportlab (única dependencia externa)
pip3 install reportlab
python3 -c "import reportlab; print('reportlab', reportlab.Version)"
```

---

## 2. Instalar dependencias

```bash
pip3 install -r docs/requirements.txt   # si existe
# o directamente:
pip3 install reportlab pytest
```

---

## 3. Verificar pruebas automatizadas (65 pruebas)

```bash
# Suite completa
python3 -m pytest tests/ -v

# Por módulo
python3 -m pytest tests/test_model.py -v       # Módulo 1
python3 -m pytest tests/test_simulator.py -v   # Módulo 2
python3 -m pytest tests/test_reports.py -v     # Módulo 4

# Prueba específica
python3 -m pytest tests/test_simulator.py::TestReferenceResults::test_3_products_reference_values -v
```

Resultado esperado: **65 passed** (0 failed).

---

## 4. Pruebas independientes por módulo

### Módulo 1 — Modelo OOP

```bash
python3 -m linprod.model
```

Verifica la construcción de la línea y hace una simulación manual de 2 ciclos.
Salida esperada: `✔ Línea de producción válida` + snapshot JSON.

### Módulo 2 — Motor de Simulación

```bash
python3 -m linprod.simulator
```

Corre 4 tests internos:
- Simulación con 3 productos → P1=12, P2=16, P3=20 ✔
- Pause/resume ✔
- Determinismo (reset + re-simulación) ✔
- Validaciones de errores ✔

### Módulo 4 — Reportería PDF (sin GUI)

```bash
python3 -m linprod.reports
```

Genera `reporte_linprod_prueba.pdf` en el directorio actual con una línea demo
de 3 procesos y 5 productos. Abrir con cualquier visor de PDF para verificar.

---

## 5. Ejecutar la interfaz gráfica (Módulo 3)

```bash
python3 -m linprod.app
```

La ventana se abre con un tema oscuro. Panel izquierdo = configuración de la
línea, panel derecho = visualización de la simulación en tiempo real.

---

## 6. Flujo completo para la demostración del profesor

El profesor llegará con una línea de **mínimo 5 procesos** ya parametrizada.
Seguir estos pasos en la GUI:

### 6.1 Configurar la línea de producción

1. En el campo **«Nombre del proceso»** escribir el nombre del primer proceso.
2. Activar **«Proceso Inicial»** para el primero y **«Proceso Final»** para el último.
3. Hacer clic en **«+ Agregar Tarea»** para añadir las tareas del proceso.
   - Cada tarea requiere: nombre y tiempo de procesamiento (ciclos).
4. Hacer clic en **«✔ Confirmar Proceso»** para fijar el proceso en la línea.
5. Repetir para todos los procesos. El orden de confirmación define el orden en la línea.
6. Verificar la vista de la línea: deben aparecer todos los procesos con sus tareas.

### 6.2 Configurar y lanzar la simulación

1. En **«Número de productos»** ingresar la cantidad indicada por el profesor.
2. Hacer clic en **«▶ Iniciar»**.
3. La simulación avanza automáticamente; cada ciclo actualiza la vista.

### 6.3 Pausar en el ciclo T indicado

Cuando el ciclo llegue al valor $T$ pedido por el profesor:

```
Hacer clic en "⏸ Pausar"
```

La simulación se detiene. El panel derecho muestra el estado de **cada tarea**:
- Producto que está procesando (o vacío si libre).
- Ciclos restantes.
- Tamaño de la cola de espera.

> **Tip:** También se puede pausar por anticipado con **«Step ▶|»** para avanzar
> ciclo a ciclo y detenerse exactamente en T.

### 6.4 Reanudar después de la pausa

```
Hacer clic en "▷ Reanudar"
```

### 6.5 Esperar la finalización y generar el reporte

1. Dejar correr hasta que todos los productos terminen (barra de progreso al 100 %).
2. Hacer clic en **«⬇ Generar PDF»**.
3. Seleccionar la ruta de guardado (por defecto: `reporte_linprod.pdf`).
4. Abrir el PDF generado: debe mostrar los 7 ítems obligatorios del enunciado.

### 6.6 Reiniciar para una nueva simulación

```
Hacer clic en "↺ Reiniciar Todo"
```

Vuelve al estado inicial con la misma línea configurada. Se puede cambiar el
número de productos y relanzar sin volver a configurar los procesos.

---

## 7. Generar `diagrama.png` desde el SVG

El diagrama de clases se encuentra en `docs/diagrama_clases.svg`.  
Para convertirlo a `docs/diagrama.png` (necesario para compilar `documentacion.tex`):

### Opción A — cairosvg (disponible en este entorno ✔)

```bash
python3 -c "
import cairosvg
cairosvg.svg2png(
    url='docs/diagrama_clases.svg',
    write_to='docs/diagrama.png',
    scale=2
)
print('diagrama.png generado')
"
```

### Opción B — Inkscape

```bash
inkscape --export-type=png \
         --export-filename=docs/diagrama.png \
         --export-dpi=150 \
         docs/diagrama_clases.svg
```

### Opción C — rsvg-convert

```bash
rsvg-convert -h 1130 docs/diagrama_clases.svg -o docs/diagrama.png
```

El archivo `docs/diagrama.png` ya existe (generado previamente con cairosvg).

---

## 8. Compilar la documentación en Overleaf

1. Subir a un proyecto Overleaf los archivos:
   - `docs/documentacion.tex` — documento principal
   - `docs/diagrama.png` — diagrama de clases (en la misma carpeta raíz del proyecto Overleaf)
2. Seleccionar compilador: **pdfLaTeX**.
3. Compilar (puede requerir 2 pasadas por el `\tableofcontents`).
4. Completar los nombres de los integrantes en la tabla de la portada.

> **Nota:** Si Overleaf no puede cargar `diagrama.png`, verificar que el archivo
> esté en la raíz del proyecto (junto a `documentacion.tex`), no en una subcarpeta.

---

## 9. Referencia rápida de comandos

| Acción | Comando |
|--------|---------|
| Todas las pruebas | `python3 -m pytest tests/ -v` |
| Test de modelo | `python3 -m linprod.model` |
| Test de simulador | `python3 -m linprod.simulator` |
| Test de reportes | `python3 -m linprod.reports` |
| Abrir GUI | `python3 -m linprod.app` |
| Generar diagrama.png | `python3 -c "import cairosvg; cairosvg.svg2png(url='docs/diagrama_clases.svg', write_to='docs/diagrama.png', scale=2)"` |
| Prueba de una sola función | `python3 -m pytest tests/test_simulator.py::TestReferenceResults -v` |
