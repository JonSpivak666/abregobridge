import streamlit as st
import torch
import os
import sys
import tempfile
from PIL import Image

# --------------------------------------------------------
# CONFIGURACIÓN DE RUTAS PARA YOLOV5 LOCAL
# --------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
YOLO_DIR = os.path.join(PROJECT_ROOT, "yolov5")

# Asegurar que las rutas estén disponibles para Python
if YOLO_DIR not in sys.path:
    sys.path.append(YOLO_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Importar los módulos del repositorio YOLOv5 local
from models.common import DetectMultiBackend
from utils.general import non_max_suppression, scale_boxes
from utils.plots import Annotator, colors
from utils.torch_utils import select_device


# --------------------------------------------------------
# CONFIGURACIÓN DE LA APP STREAMLIT
# --------------------------------------------------------
st.set_page_config(
    page_title="AbregoBridge - Detección de Grietas",
    page_icon="🧱",
    layout="centered"
)

st.title("🧱 AbregoBridge - Detección de Grietas con Inteligencia Artificial")
st.markdown("""
Sistema de detección de grietas en estructuras civiles basado en visión por computadora (**YOLOv5**).  
Desarrollado por **Jonathan Sordo **.
---
""")


# --------------------------------------------------------
# FUNCIÓN PARA CARGAR EL MODELO LOCALMENTE
# --------------------------------------------------------
@st.cache_resource
def load_model():
    try:
        model_path = os.path.join(YOLO_DIR, "best.pt")  # Modelo local
        device = select_device("cpu")  # Forzamos CPU
        model = DetectMultiBackend(model_path, device=device)
        st.success("✅ Modelo YOLOv5 cargado correctamente desde carpeta local.")
        return model, device
    except Exception as e:
        st.error(f"❌ Error al cargar el modelo local: {e}")
        return None, None


model, device = load_model()


# --------------------------------------------------------
# SUBIDA Y PROCESAMIENTO DE IMAGEN
# --------------------------------------------------------
uploaded_file = st.file_uploader("Sube una imagen de una estructura civil", type=["jpg", "jpeg", "png"])

if uploaded_file is not None and model is not None:
    # Guardar temporalmente la imagen subida
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())

    # Mostrar la imagen original
    image = Image.open(uploaded_file)
    st.image(image, caption="📸 Imagen cargada", use_column_width=True)

    # --------------------------------------------------------
    # DETECCIÓN DE GRIETAS
    # --------------------------------------------------------
    if st.button("🔍 Analizar imagen"):
        with st.spinner("Analizando grietas..."):
            im = Image.open(tfile.name).convert("RGB")
            im_tensor = model.transforms(im)[None]  # Preprocesamiento
            preds = model(im_tensor, augment=False, visualize=False)
            preds = non_max_suppression(preds, 0.25, 0.45, None, False, max_det=1000)

            annotator = Annotator(im, line_width=2, example=str(model.names))
            for i, det in enumerate(preds):
                if len(det):
                    det[:, :4] = scale_boxes(im_tensor.shape[2:], det[:, :4], im.size).round()
                    for *xyxy, conf, cls in reversed(det):
                        c = int(cls)
                        label = f'{model.names[c]} {conf:.2f}'
                        annotator.box_label(xyxy, label, color=colors(c, True))

            result_image = annotator.result()

            # Mostrar resultado en pantalla
            st.image(result_image, caption="🧩 Resultado del análisis", use_column_width=True)

            # Guardar resultado en carpeta "outputs"
            os.makedirs("outputs", exist_ok=True)
            output_path = os.path.join("outputs", uploaded_file.name)
            Image.fromarray(result_image).save(output_path)

            st.success(f"✅ Análisis completado. Imagen guardada en: `{output_path}`")

else:
    st.info("📷 Sube una imagen para comenzar el análisis.")
