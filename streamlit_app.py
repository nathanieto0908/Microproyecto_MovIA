import streamlit as st
import requests

st.title("MovIA - Tu recomendador de películas")

peliculas = st.multiselect(
    "Selecciona tus películas favoritas",
    ["Interstellar", "Pulp Fiction", "The Matrix", "Inception", "The Dark Knight", "Gladiator"]
)

if len(peliculas) >= 5:
    st.success("¡Perfecto! Ya seleccionaste tus 5 películas.")
    if st.button("Obtener recomendaciones"):
        # Llamada al API
        try:
            response = requests.post("http://127.0.0.1:8000/recommend", json={"peliculas": peliculas})
            if response.status_code == 200:
                data = response.json()
                st.write("Tus recomendaciones:")
                for rec in data["recomendaciones"]:
                    st.subheader(rec["titulo"])
                    st.write(f"¿Por qué te gustará? {rec['razon']}")
            else:
                st.error("Error al obtener recomendaciones del API")
        except Exception as e:
            st.error(f"No se pudo conectar al API: {e}")
