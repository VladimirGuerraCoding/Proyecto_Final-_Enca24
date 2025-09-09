from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import psycopg2
from passlib.context import CryptContext

from db import get_db_connection
from models.rol_user import Usuario  # Importamos el modelo Pydantic

# Configuración de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

# Dependencia para obtener la conexión a la base de datos
def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

# Ruta para registrar un nuevo usuario
@router.post("/registro/")
def registrar_usuario(usuario: Usuario, conn: psycopg2.extensions.connection = Depends(get_db)):
    try:
        cur = conn.cursor()
        # Verificar si el correo ya está registrado
        cur.execute('SELECT id FROM usuarios WHERE correo = %s', (usuario.correo,))
        existing_user = cur.fetchone()
        if existing_user:
            raise HTTPException(status_code=400, detail="El correo ya está registrado")

        # Encriptar la contraseña
        hashed_password = pwd_context.hash(usuario.contrasena)

        # Insertar en la tabla usuarios
        cur.execute(
            '''
            INSERT INTO usuarios (nombre, apellido, correo, contrasena, rol_id) 
            VALUES (%s, %s, %s, %s, %s) RETURNING id
            ''',
            (usuario.nombre, usuario.apellido, usuario.correo, hashed_password, usuario.rol_id)
        )
        usuario_id = cur.fetchone()['id']

        # Insertar en estudiantes si es rol estudiante
        if usuario.rol_id == 2:
            cur.execute(
                '''
                INSERT INTO estudiantes (nombre, apellido, correo, edad, direccion, usuario_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ''',
                (usuario.nombre, usuario.apellido, usuario.correo, usuario.edad, usuario.direccion, usuario_id)
            )

        # Insertar en profesores si es rol profesor
        elif usuario.rol_id == 1:
            cur.execute(
                '''
                INSERT INTO profesores (nombre, apellido, correo, especialidad, usuario_id)
                VALUES (%s, %s, %s, %s, %s)
                ''',
                (usuario.nombre, usuario.apellido, usuario.correo, usuario.especialidad, usuario_id)
            )

        conn.commit()
        cur.close()

    except HTTPException:
        # Relevamos el error específico
        raise
    except Exception as e:
        # Manejamos cualquier otro error
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar el usuario: {e}")

    return {"message": "Usuario registrado correctamente", "usuario_id": usuario_id}
