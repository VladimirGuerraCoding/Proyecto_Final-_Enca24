from pydantic import BaseModel, validator
from typing import Optional

class Estudiante(BaseModel):
    id : Optional[int] = None
    nombre: str
    apellido: str
    correo: str
    edad: int
    direccion: str
    usuario_id: Optional[int] = None

    @validator('correo')
    def validar_correo(cls, v):
        if "@" not in v or "." not in v:
            raise ValueError('El correo debe ser válido')
        return v
    