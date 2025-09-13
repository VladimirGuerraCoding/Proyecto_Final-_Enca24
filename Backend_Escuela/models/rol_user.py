from pydantic import BaseModel, validator
from typing import Optional

class Usuario(BaseModel):
    nombre: str
    apellido: str
    correo: str
    contrasena: str
    rol_id: int

    # Campos opcionales para estudiantes (rol_id=2)
    edad: Optional[int] = None
    direccion: Optional[str] = None

    # Campo opcional para profesores (rol_id=1)
    especialidad: Optional[str] = None
    
    @validator('correo')
    def validar_correo(cls, v):
        if "@" not in v or "." not in v:
            raise ValueError('El correo debe ser válido')
        return v

    @validator('contrasena')
    def validar_contrasena(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v
