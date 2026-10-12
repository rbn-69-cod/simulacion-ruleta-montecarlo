# 🎰 Replicación Científica: Simulación Monte Carlo de Estrategias de Ruleta

Replicación empírica completa del artículo de investigación:  
> **Sarnecki, K. (2026).** *Comparison of the effectiveness of roulette betting strategies using Monte Carlo simulation*. **Journal of Computer Sciences Institute**, 40, 232–238.

Este repositorio contiene el código fuente, los datos, el notebook de análisis y una plataforma web interactiva lista para evaluación académica, exposición y entrega.

---

## 🚀 Opciones de Ejecución

El proyecto está diseñado para funcionar de manera inmediata en **Google Colab**, **Jupyter Notebook**, **PyCharm** y terminal estándar.

### Opción 1: Google Colab ☁️
1. Ve a [colab.research.google.com](https://colab.research.google.com).
2. Haz clic en **Subir (Upload)** y selecciona el archivo `simulacion_ruleta.ipynb`.
3. Ejecuta las celdas secuencialmente o presiona **Entorno de ejecución > Ejecutar todas**.
4. El notebook incluye la compilación automática del kernel en C (`gcc`) y genera todas las tablas, pruebas de hipótesis y gráficos directamente en la nube.

---

### Opción 2: Jupyter Notebook / JupyterLab 📓
1. Abre tu terminal en la carpeta del proyecto:
   ```bash
   cd /Users/pc/.gemini/antigravity/scratch/proyecto_ruleta
   ```
2. Inicia Jupyter:
   ```bash
   jupyter notebook simulacion_ruleta.ipynb
   # O si usas JupyterLab:
   jupyter lab
   ```
3. El notebook ya viene con todas las salidas, tablas formateadas y gráficos pre-renderizados, y puedes volver a ejecutarlo cuando quieras.

---

### Opción 3: PyCharm 🐍
1. Abre **PyCharm** y selecciona **Open** -> carpeta `proyecto_ruleta`.
2. PyCharm detectará automáticamente el archivo `requirements.txt`. Instala las dependencias si no las tienes:
   ```bash
   pip install -r requirements.txt
   ```
3. Puedes ejecutar cualquiera de estos scripts:
   - **`simulacion_ruleta.py`**: Corre la replicación completa de 3,36 millones de sesiones (o pásale un argumento como `python simulacion_ruleta.py 500` para prueba rápida).
   - **`server.py`**: Levanta el servidor web interactivo local en `http://localhost:8000`.
   - **`simulacion_ruleta.ipynb`**: Si tienes PyCharm Professional, puedes abrir y ejecutar el notebook directamente desde el IDE.

---

### Opción 4: Dashboard Web Interactivo en Vivo 🌐
Para presentaciones y defensas frente al jurado/profesor:
```bash
python3 server.py
```
Abre en tu navegador: **[http://localhost:8000](http://localhost:8000)**
- **Comparativa Paper vs Réplica**: Tablas dinámicas y gráficos interactivos (Chart.js).
- **Simulador Monte Carlo en Vivo**: Permite variar bankroll, límite de mesa, giros y estrategias en milisegundos usando el kernel en C.
- **Visualizador de Trayectorias Giro a Giro**: Observa la curva del capital en tiempo real y la trampa de la Martingala.
- **Guía de Exposición**: Guión diapositiva por diapositiva y respuestas a preguntas trampa.

---

## 📁 Estructura de Archivos del Proyecto

| Archivo | Descripción |
|---|---|
| `simulacion_ruleta.ipynb` | Notebook completo para **Google Colab** y **Jupyter** con teoría, código, gráficos y contrastes. |
| `simulacion_ruleta.py` | Script modular en Python para ejecución por consola o **PyCharm**. |
| `sim_kernel.c` | Núcleo ultra-optimizado en C (generador pseudoaleatorio *xoroshiro128+* y *splitmix64*). |
| `sim_kernel.so` | Biblioteca dinámica compilada usada por ctypes desde Python. |
| `server.py` | Servidor HTTP REST en Python para la interfaz interactiva. |
| `index.html` | Interfaz visual moderna (Tailwind CSS + Chart.js) para la exposición. |
| `resultados_agregados.csv` | Dataset de métricas consolidadas (Media, Mediana, P(ganar), P(ruina), VaR, CVaR, Drawdown). |
| `resultados_por_escenario.csv` | Dataset detallado de los 48 escenarios experimentales $\times$ 7 estrategias (336 filas). |
| `figura_resultados.png` | Gráfico de alta resolución con ganancia media, probabilidades y riesgo de cola. |
| `salida_simulacion.txt` | Registro de la salida estándar de la corrida de 3,36M de sesiones. |
| `requirements.txt` | Especificación de dependencias para entornos virtuales y PyCharm. |

---

## 📊 Síntesis de Resultados (Réplica vs Sarnecki 2026)

| Estrategia | Media (Paper) | Media (Mía) | Ruina (Paper) | Ruina (Mía) | P(Ganar) | CVaR 95% | Max Drawdown |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Flat betting** | **-24.1** | **-24.0** | **1.8%** | **1.8%** | 23.2% | -115.5 | 45.2 |
| **Martingale** | **-67.3** | **-65.2** | **39.5%** | **39.2%** | 40.6% | -635.6 | 283.2 |
| **Fibonacci** | **-58.0** | **-57.1** | **32.5%** | **32.8%** | 53.7% | -644.5 | 214.7 |
| **D’Alembert** | **-161.8** | **-160.4** | **54.2%** | **54.0%** | 31.2% | -1000.0 | 361.1 |
| **Labouchere** | **-153.8** | **-175.1** | **64.6%** | **70.0%** | 22.3% | -1000.0 | 537.2 |
| **Fixed-fractional** | **-150.1** | **-142.0** | **5.1%** | **2.7%** | 17.0% | -832.4 | 289.8 |

---

## 🎯 Conclusiones Académicas

1. **Ninguna estrategia supera a la casa:** La esperanza matemática por tiro es invariablemente $\mathbb{E}[X] = -1/37 \approx -2.70\%$. Todas las estrategias terminan con ganancia media negativa.
2. **Flat betting es la más conservadora:** Minimiza la probabilidad de ruina ($1.8\%$) y tiene el menor drawdown promedio.
3. **La paradoja de Fibonacci:** Aunque tiene un $53.7\%$ de probabilidad de terminar en positivo (la más alta), sufre una ruina del $32.8\%$ debido a la asimetría negativa de la distribución.
4. **Criterio de Kelly:** Sin una ventaja estadística intrínseca ($\mu \le 0$), Kelly no produce crecimiento del capital; actúa meramente como limitador de volatilidad.
