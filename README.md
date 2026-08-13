# ⚽ Depor - Squad Demographic & Match Report Generator

Local tool with a lightweight web interface to automate the generation of **"Analysis | Player"** PowerPoint decks (`.pptx`) and PDF reports (`.pdf`) for football clubs, eliminating manual text-box editing in PowerPoint.

---

## 🌟 Características Principales

1. **Gestión de Plantilla de Jugadores**:
   - Formulario de alta rápida e importación masiva por **CSV/Excel** (arrastrar y soltar).
   - Cálculo automático de edad y mapeo inteligente de la posición en el campo a las 6 categorías principales (Porteros, Centrales, Laterales, Mediocentros, Int/Extremos, Delanteros).

2. **Editor Táctico de Partidos & Alineaciones**:
   - Selección de formación y posición de los 11 titulares en campo.
   - Registro de sustituciones con cronómetro por minutos (con flechas rojas de salida en titulares y verdes de entrada en suplentes).

3. **Vista Previa en Vivo (Dashboard Interactivo)**:
   - Renderizado en tiempo real de las 3 diapositivas (**Diapositiva A - Tabla Demográfica**, **Diapositiva B - Campograma de Plantilla**, **Diapositiva C - Informe de Partido**).

4. **Motor de Layout Anticolisión y Antidesbordamiento**:
   - **Posicionamiento relativo**: Proyección matemática sobre el trapecio del campo de fútbol.
   - **Ajuste dinámico de ancho y fuente**: Escala automáticamente el tamaño de fuente y ancho de caja para evitar que los nombres de los jugadores sobresalgan del césped.
   - **Detección de colisiones**: Valida la no-intersección de cajas y el margen mínimo de seguridad respecto al pie de página dorado (`MEDICAL & SPORTS SCIENCE DEPARTMENT`).

5. **Exportación Fiel a `.pptx` y `.pdf`**:
   - Diapositivas 100% editables en PowerPoint (`python-pptx`) respetando paleta de colores (Azul Marino `#002060`, Verde Pálido `#D9EAD3`, Melocotón `#FCE5CD`, Dorado `#D4AF37`).
   - Conversión automatizada a `.pdf` vía LibreOffice Headless.

---

## 🚀 Instrucciones de Instalación y Arranque

### Requisitos Previos
- **Python 3.11+**
- **LibreOffice** (opcional, necesario únicamente para la conversión automática a `.pdf`)

### 1. Clonar / Descargar el Repositorio e Instalar Dependencias

```bash
cd "Depor - Demographic"

# Crear y activar entorno virtual (opcional pero recomendado)
python -m venv venv
# En Windows:
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Ejecutar la Aplicación

```bash
python run.py
```

La aplicación se iniciará automáticamente en:
👉 **`http://localhost:8000`**

---

## 🧪 Ejecutar los Tests de Layout Anticolisión

Para ejecutar el test automatizado que comprueba que una plantilla de **30 jugadores con nombres especialmente largos** no genera solapamientos ni desbordamientos del polígono del campo:

```bash
pytest tests/test_layout_engine.py -v
```

---

## 📁 Estructura del Proyecto

```
Depor - Demographic/
├── backend/
│   ├── models.py            # Esquemas Pydantic y mapeo de categorías
│   ├── database.py          # Capa de persistencia SQLite e importación CSV
│   ├── layout_engine.py     # Motor geométrico de proyección y anticolisión
│   ├── pptx_generator.py    # Generador de diapositivas con python-pptx
│   ├── pdf_converter.py     # Wrapper de conversión a PDF con LibreOffice
│   └── main.py              # API servidor con FastAPI y endpoints REST
├── frontend/
│   ├── index.html           # Interfaz web responsiva con tabs y modal
│   ├── style.css            # Sistema de diseño, paleta y vista de campo
│   └── app.js               # Control de eventos, tablas e interactividad
├── tests/
│   └── test_layout_engine.py # Tests unitarios de colisión y límites
├── requirements.txt         # Librerías de Python requeridas
├── seed_data.py             # Semilla con datos reales del Deportivo de La Coruña
├── run.py                   # Script de inicio rápido en 1 solo comando
└── README.md                # Manual de usuario e instalación
```
