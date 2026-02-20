import streamlit as st

st.title("MovIA - Tus recomendaciones")

# Simulación de recomendaciones (más adelante se conectará al modelo real)
recomendaciones = [
    {"titulo": "Gladiator", "razon": "Por tu interés en acción y drama"},
    {"titulo": "Arrival", "razon": "Por tu interés en ciencia ficción"},
    {"titulo": "La La Land", "razon": "Por tu interés en romance y música"}
]

st.write("Basado en tus gustos, encontramos estas películas:")

for rec in recomendaciones:
    st.subheader(rec["titulo"])
    st.write(f"¿Por qué te gustará? {rec['razon']}")

