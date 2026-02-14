import streamlit as st
import pdfplumber
import re
import pandas as pd
import unicodedata

# -----------------------------
# NORMALITZACIÓ TEXT
# -----------------------------

def normalize(text):
    import unicodedata

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")

    text = text.replace("\xa0", " ")
    text = text.replace("’", "'")
    text = text.replace("–", "-")

    text = re.sub(r"\s+", " ", text)

    return text.strip().lower()
    

# -----------------------------
# EXTREURE NOMÉS LÍNIA CATALANA
# -----------------------------

def extract_questions(pdf_file):
    questions = {}

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")

            for line in lines:
                line = line.strip()

                # Detectar línies que comencen amb número de pregunta
                match = re.match(r"^(\d+)\)\s+(.*)", line)

                if match:
                    number = int(match.group(1))
                    question_text = match.group(2)

                    # Ignorar capçaleres estranyes
                    if len(question_text) < 10:
                        continue

                    questions[normalize(question_text)] = number

    return questions


# -----------------------------
# STREAMLIT APP
# -----------------------------

st.title("Comparador de Models d'Examen (Català només)")

st.header("1️⃣ Pujar Model Base (Model A)")
base_pdf = st.file_uploader("Puja el PDF base", type="pdf")

st.header("2️⃣ Pujar Models a comparar (fins a 4)")
other_pdfs = st.file_uploader(
    "Puja la resta de models",
    type="pdf",
    accept_multiple_files=True
)

if base_pdf and other_pdfs:

    st.write("Processant models...")

    base_questions = extract_questions(base_pdf)
    st.success(f"Model base: {len(base_questions)} preguntes detectades")

    all_results = []

    for model_pdf in other_pdfs:

        model_questions = extract_questions(model_pdf)
        st.info(f"{model_pdf.name}: {len(model_questions)} preguntes detectades")

        for question_text, base_number in base_questions.items():

            model_number = model_questions.get(question_text, "NO TROBADA")

            all_results.append({
                "Pregunta_Model_A": base_number,
                f"Pregunta_{model_pdf.name}": model_number
            })

    df = pd.DataFrame(all_results)

    st.subheader("Resultat comparació")
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Descarregar CSV",
        data=csv,
        file_name="correspondencia_models.csv",
        mime="text/csv"
    )
    
