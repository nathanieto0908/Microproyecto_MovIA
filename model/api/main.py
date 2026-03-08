from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserPreferences(BaseModel):
    peliculas: list[str]

@app.post("/recommend")
def recommend(preferences: UserPreferences):
    seleccionadas = preferences.peliculas
    recomendaciones = [
        {"titulo": "Gladiator", "razon": "Por tu interés en acción y drama"},
        {"titulo": "Arrival", "razon": "Por tu interés en ciencia ficción"},
        {"titulo": "La La Land", "razon": "Por tu interés en romance y música"}
    ]
    return {"seleccionadas": seleccionadas, "recomendaciones": recomendaciones}

