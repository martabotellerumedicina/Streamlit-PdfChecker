import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import unicodedata

st.set_page_config(page_title="PDF Exam Matcher", layout="wide")
st.title("Comparador de Models d'Examen (només text en català)")

# --------------------------------------------------
# NORMALITZACIÓ
# --------------------------------------------------

def normalitzar(text):
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")
    text = text.replace("\n", " ")
    text = " ".join(text.split())
    return text.lower()

# --------------------------------------------------
# EXTREURE NOMÉS TEXT NO CURSIVA (català)
# --------------------------------------------------

def extreure_text_catala(pdf_file):
    text_total = ""

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            for ch in page.chars:
                fontname = ch.get("fontname", "")

                # Eliminem text en cursiva (castellà)
                if "Italic" not in fontname and "Oblique" not in fontname:
                    text_total += ch.get("text", "")

            text_total += "\n"

    return text_total

# --------------------------------------------------
# EXTREURE PREGUNTES
# --------------------------------------------------

def extreure_preguntes(pdf_file):
    text_complet = extreure_text_catala(pdf_file)

    preguntes = {}

    # Detecta format: 1) 2) 3)
    blocs = re.split(r"\n\s*(\d+)\)\s", text_complet)

    for i in range(1, len(blocs), 2):
        numero = blocs[i]
        contingut = blocs[i + 1]
        preguntes[numero] = normalitzar(contingut)

    return preguntes

# --------------------------------------------------
# COMPARAR MODELS
# --------------------------------------------------

def comparar_models(base, model):
    correspondencia = []

    for num_base, text_base in base.items():
        for num_model, text_model in model.items():
            if text_base == text_model:
                correspondencia.append({
                    "Pregunta_Model_Base": num_base,
                    "Pregunta_Model_Alt": num_model
                })
                break

    return correspondencia

# --------------------------------------------------
# INTERFÍCIE
# --------------------------------------------------

st.subheader("1️⃣ Pujar Model Base (Model A)")

model_base_file = st.file_uploader(
    "Puja el PDF del model base",
    type="pdf",
    key="base"
)

if model_base_file:

    base_preguntes = extreure_preguntes(model_base_file)
    st.success(f"Model base carregat. Preguntes trobades: {len(base_preguntes)}")

    st.subheader("2️⃣ Pujar Altres Models a Comparar")

    altres_models = st.file_uploader(
        "Puja un o més PDFs",
        type="pdf",
        accept_multiple_files=True
    )

    if altres_models:

        progress = st.progress(0)
        resultats_totals = []

        for idx, model_file in enumerate(altres_models):

            model_preguntes = extreure_preguntes(model_file)
            st.info(f"{model_file.name} → Preguntes trobades: {len(model_preguntes)}")

            correspondencia = comparar_models(base_preguntes, model_preguntes)

            for fila in correspondencia:
                fila["Model"] = model_file.name

            resultats_totals.extend(correspondencia)

            progress.progress((idx + 1) / len(altres_models))

        if resultats_totals:

            df = pd.DataFrame(resultats_totals)

            st.subheader("Resultats")
            st.dataframe(df)

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)

            st.download_button(
                label="Descarregar CSV",
                data=csv_buffer.getvalue(),
                file_name="correspondencia_models.csv",
                mime="text/csv"
            )

        else:
            st.warning("No s'han trobat coincidències exactes.")
            
