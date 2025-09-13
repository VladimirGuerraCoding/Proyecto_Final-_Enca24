from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

from db import get_db_connection
from models.rol_user import Usuario  # Asegúrate de que el modelo Usuario esté definido correctamente
from models.estudiante import Estudiante  # Asegúrate de que el modelo Estudiante esté definido correctamente
from models.profesores import Profesor  # Asegúrate de que el modelo Profesor esté definido correctamente

# Contexto de encriptación para las contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

# Roles válidos y sus IDs
ROLES_VALIDOS = [1, 2, 3]  # 1: Profesor, 2: Estudiante, 3: Admin

# Ruta para registrar un nuevo usuario
@router.post("/registro/")
def registrar_usuario(usuario: Usuario):
    conn = None
    cur = None
    try:
        # Conexión a la base de datos
        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar si el correo ya está registrado
        cur.execute('SELECT id FROM usuarios WHERE correo = %s', (usuario.correo,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="El correo ya está registrado")

        # Validar el rol antes de crear el usuario
        if usuario.rol_id not in ROLES_VALIDOS:
            raise HTTPException(status_code=400, detail="Rol inválido. Debe ser Profesor, Estudiante o Admin.")

        # Encriptar la contraseña antes de guardarla
        hashed_password = pwd_context.hash(usuario.contrasena)

        # Insertar nuevo usuario en la tabla 'usuarios' y obtener su ID
        cur.execute(
            'INSERT INTO usuarios (nombre, apellido, correo, contrasena, rol_id) VALUES (%s, %s, %s, %s, %s) RETURNING id',
            (usuario.nombre, usuario.apellido, usuario.correo, hashed_password, usuario.rol_id)
        )
        new_user_record = cur.fetchone()
        if not new_user_record:
            raise HTTPException(status_code=500, detail="No se pudo crear el usuario.")
        
        new_user_id = new_user_record['id']

        # Roles: 1: Profesor, 2: Estudiante, 3: Admin
        # Crear entrada en la tabla 'profesores' si el rol es Profesor (rol_id=1)
        if usuario.rol_id == 1:
            if not usuario.especialidad:
                raise HTTPException(status_code=400, detail="La especialidad es requerida para un profesor.")
            cur.execute(
                'INSERT INTO profesores (nombre, apellido, correo, especialidad, usuario_id) VALUES (%s, %s, %s, %s, %s)',
                (usuario.nombre, usuario.apellido, usuario.correo, usuario.especialidad, new_user_id)
            )
        # Crear entrada en la tabla 'estudiantes' si el rol es Estudiante (rol_id=2)
        elif usuario.rol_id == 2:
            if usuario.edad is None or not usuario.direccion:
                raise HTTPException(status_code=400, detail="La edad y la dirección son requeridas para un estudiante.")
            cur.execute(
                'INSERT INTO estudiantes (nombre, apellido, correo, edad, direccion, usuario_id) VALUES (%s, %s, %s, %s, %s, %s)',
                (usuario.nombre, usuario.apellido, usuario.correo, usuario.edad, usuario.direccion, new_user_id)
            )
        
        # Para el rol de admin (rol_id=3), no se necesita crear entrada en otra tabla.
        
        conn.commit()

        # Devolver el usuario recién creado desde la tabla 'usuarios'
        cur.execute('SELECT * FROM usuarios WHERE id = %s', (new_user_id,))
        new_usuario = cur.fetchone()
        
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar el usuario: {e}")
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    return new_usuario