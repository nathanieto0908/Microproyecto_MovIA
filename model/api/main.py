from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Modelo de entrada: lista de películas favoritas
class UserPreferences(BaseModel):
    peliculas: list[str]

# Endpoint de recomendación
@app.post("/recommend")
def recommend(preferences: UserPreferences):
    seleccionadas = preferences.peliculas
    # Simulación: luego aquí conectamos tu modelo real
    recomendaciones = [
        {"titulo": "Gladiator", "razon": "Por tu interés en acción y drama"},
        {"titulo": "Arrival", "razon": "Por tu interés en ciencia ficción"},
        {"titulo": "La La Land", "razon": "Por tu interés en romance y música"}
    ]
    return {"seleccionadas": seleccionadas, "recomendaciones": recomendaciones}

