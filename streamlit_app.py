import streamlit as st

st.title("MovIA - Tu recomendador de películas")

st.write("Primera Prueba del Tablero 🚀")

peliculas = st.multiselect(
    "Selecciona tus películas favoritas",
    ["Interstellar", "Pulp Fiction", "The Matrix", "Inception", "The Dark Knight", "Gladiator"]
)

if len(peliculas) >= 5:
    st.success("¡Perfecto! Ya seleccionaste tus 5 películas.")
    if st.button("Obtener recomendaciones"):
        st.write("Aquí aparecerán tus recomendaciones...")
