import sqlite3
import datetime
from functools import wraps
from flask import Flask, request, render_template, redirect, flash, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

# --- CONFIGURACIÓN DE LA APLICACIÓN ---
app = Flask(__name__)
# ¡IMPORTANTE! Carga esta clave desde una variable de entorno en producción.
app.config['SECRET_KEY'] = 'tu-super-secreto-y-largo-string-aleatorio' 
app.config['DATABASE'] = 'db.db'

# --- GESTIÓN Y CREACIÓN DE LA BASE DE DATOS ---

def crear_tablas():
    """
    Se conecta a la base de datos y crea las tablas si no existen.
    Esta función se ejecuta una vez al iniciar la aplicación.
    """
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()

    # Crear la tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            pais TEXT NOT NULL,
            objetivos TEXT,
            fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Crear la tabla de objetivos (aunque no se usa directamente en esta versión para almacenar múltiples objetivos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS objetivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            objetivo_texto TEXT NOT NULL,
            completado BOOLEAN NOT NULL DEFAULT 0,
            fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_usuario) REFERENCES usuarios (id)
        );
    ''')

    conn.commit()
    conn.close()
    print("Base de datos y tablas verificadas/creadas en 'db.db'.")

# Ejecuta la función para asegurar que las tablas existan al iniciar
crear_tablas()


# --- DECORADOR PARA AUTENTICACIÓN JWT ---

def token_required(f):
    """
    Decorador que verifica la validez de un token JWT en las cabeceras (o en este caso, cookies).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')

        if not token:
            flash("Se requiere un token para acceder a esta página. Por favor, inicia sesión.", "warning")
            return redirect('/login')

        try:
            # Decodificar el token con la clave secreta y algoritmo
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            
            # Conexión a la BD dentro del decorador para obtener el usuario actual
            conn = sqlite3.connect(app.config['DATABASE'])
            conn.row_factory = sqlite3.Row # Permite acceder a las columnas como diccionario
            current_user = conn.execute(
                'SELECT * FROM usuarios WHERE id = ?', (data['user_id'],)
            ).fetchone()
            conn.close()
            
            if not current_user:
                flash("Token inválido. Usuario no encontrado.", "danger")
                return redirect('/login')

        except jwt.ExpiredSignatureError:
            flash("Tu sesión ha expirado. Por favor, inicia sesión de nuevo.", "warning")
            # Redirige al login y borra la cookie si ha expirado
            response = redirect('/login')
            response.delete_cookie('token')
            return response
        except jwt.InvalidTokenError:
            flash("Token inválido. Por favor, inicia sesión de nuevo.", "danger")
            # Redirige al login y borra la cookie si es inválido
            response = redirect('/login')
            response.delete_cookie('token')
            return response

        # Si el token es válido, pasa el objeto de usuario a la función decorada
        return f(current_user, *args, **kwargs)

    return decorated

def generar_recomendacion(materia, horas, objetivo):
    recomendaciones = []

    recomendaciones.append(f"¡Excelente elección estudiando {materia}! Aquí tienes algunas recomendaciones para alcanzar tu objetivo de {objetivo}:")

    # Recomendaciones basadas en horas de estudio
    if horas < 2:
        recomendaciones.append("Con menos de 2 horas al día, te recomendamos enfocarte en tareas clave y utilizar técnicas de estudio eficientes.")
    elif horas < 4:
        recomendaciones.append("Con 2 a 4 horas al día, puedes profundizar en el material y practicar con ejercicios adicionales.")
    else:
        recomendaciones.append("Con más de 4 horas al día, asegúrate de incluir descansos regulares para mantener la concentración y evitar el agotamiento.")

    # Recomendaciones generales
    recomendaciones.append("- Utiliza el método Pomodoro: 25 minutos de estudio seguidos de 5 minutos de descanso.")
    recomendaciones.append("- Realiza resúmenes y repite la información en voz alta para reforzar el aprendizaje.")
    recomendaciones.append("- Haz pruebas prácticas regularmente para evaluar tu comprensión.")
    recomendaciones.append("- Revisa tus notas al final de cada sesión para consolidar el conocimiento.")

    recomendaciones.append(f"Recuerda que el objetivo de {objetivo} es alcanzable con dedicación y una buena estrategia de estudio. ¡Buena suerte!")

    return "\n".join(recomendaciones)

def generar_recomendacion_tiempo(tareas, prioridades, bloques):
    recomendaciones = []
    recomendaciones.append("¡Excelente trabajo planificando tu tiempo! Aquí tienes algunas recomendaciones para mejorar tu gestión del tiempo:")

    # Recomendaciones basadas en el número de bloques
    if bloques < 4:
        recomendaciones.append("Con menos de 4 bloques de tiempo, te recomendamos priorizar tareas importantes y evitar distracciones.")
    elif bloques < 8:
        recomendaciones.append("Con 4 a 8 bloques de tiempo, puedes abordar tareas más detalladas y complejas.")
    else:
        recomendaciones.append("Con más de 8 bloques de tiempo, asegúrate de incluir descansos regulares para mantener la productividad.")

    # Otras recomendaciones generales
    recomendaciones.append("- Utiliza la técnica Pomodoro para mantener la concentración.")
    recomendaciones.append("- Revisa tus prioridades diariamente y ajústalas según sea necesario.")
    recomendaciones.append("- Considera el uso de herramientas de gestión de tareas para mantenerte organizado.")

    recomendaciones.append("Recuerda que la gestión efectiva del tiempo es clave para el éxito académico. ¡Buena suerte!")

    return "\n".join(recomendaciones)

def generar_recomendacion_emocional(emociones, estrategias, actividades):
    recomendaciones = []
    recomendaciones.append("¡Es fantástico que te enfoques en tu bienestar emocional! Aquí tienes algunas recomendaciones para mejorar tu bienestar:")

    # Recomendaciones basadas en las estrategias y actividades
    recomendaciones.append("- Practica regularmente las estrategias de manejo emocional que has mencionado.")
    recomendaciones.append("- Incorpora actividades de relajación en tu rutina diaria para reducir el estrés.")
    recomendaciones.append("- Considera la posibilidad de hablar con un profesional si sientes que tus emociones son abrumadoras.")

    recomendaciones.append("Recuerda que el bienestar emocional es fundamental para una vida equilibrada. ¡Cuídate!")

    return "\n".join(recomendaciones)

def generar_recomendacion_espiritual(practicas, reflexiones, metas):
    recomendaciones = []
    recomendaciones.append("¡Es maravilloso que te enfoques en tu crecimiento espiritual! Aquí tienes algunas recomendaciones para avanzar en tu camino espiritual:")

    # Recomendaciones basadas en las prácticas y reflexiones
    recomendaciones.append("- Dedica tiempo diariamente a tus prácticas espirituales.")
    recomendaciones.append("- Reflexiona sobre tus reflexiones diarias y cómo puedes aplicarlas en tu vida.")
    recomendaciones.append("- Establece metas espirituales alcanzables y revísalas regularmente.")

    recomendaciones.append("Recuerda que el crecimiento espiritual es un viaje continuo. ¡Sigue adelante!")

    return "\n".join(recomendaciones)

def generar_recomendacion_habitos(habitos, acciones, duracion):
    recomendaciones = []
    recomendaciones.append("¡Es genial que te enfoques en desarrollar nuevos hábitos! Aquí tienes algunas recomendaciones para facilitar el proceso:")

    # Recomendaciones basadas en la duración y acciones
    recomendaciones.append(f"- Comienza con una duración de {duracion} minutos y aumenta gradualmente según sea necesario.")
    recomendaciones.append("- Realiza las acciones diarias de manera consistente para consolidar el hábito.")
    recomendaciones.append("- Establece recordatorios o alarmas para no olvidar tus hábitos diarios.")

    recomendaciones.append("Recuerda que el desarrollo de hábitos lleva tiempo y esfuerzo. ¡Persevera!")

    return "\n".join(recomendaciones)

def generar_recomendacion_reflexion_proposito(reflexion, proposito):
    recomendaciones = []
    recomendaciones.append("¡Es importante reflexionar sobre tu propósito! Aquí tienes algunas recomendaciones para profundizar en tu reflexión y propósito:")

    # Recomendaciones basadas en la reflexión y propósito
    recomendaciones.append("- Tómate un tiempo cada semana para revisar tus reflexiones y ajustar tu propósito según sea necesario.")
    recomendaciones.append("- Considera la posibilidad de compartir tus reflexiones con alguien de confianza para obtener perspectivas adicionales.")
    recomendaciones.append("- Establece acciones concretas basadas en tu propósito para avanzar hacia tus metas.")

    recomendaciones.append("Recuerda que la reflexión constante y el propósito claro son fundamentales para una vida significativa. ¡Sigue reflexionando!")

    return "\n".join(recomendaciones)

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def home():
    """Página de inicio que redirige al registro."""
    return redirect('/registro')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """
    Página de registro de nuevos usuarios.
    Ahora, al registrarse exitosamente, inicia sesión automáticamente y redirige a /bienvenida.
    """
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        confirmar = request.form['confirmar']
        pais = request.form['pais']
        
        errores = []

        if not usuario or not password or not confirmar or not pais:
            errores.append("Todos los campos son obligatorios.")
        if password != confirmar:
            errores.append("Las contraseñas no coinciden.")
        
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row # Para obtener el usuario por su nombre más tarde
        
        usuario_existente = conn.execute(
            'SELECT id FROM usuarios WHERE usuario = ?', (usuario,)
        ).fetchone()

        if usuario_existente:
            errores.append(f"El usuario '{usuario}' ya está registrado. Intenta con otro.")

        if errores:
            conn.close()
            for error in errores:
                flash(error, 'danger')
            return render_template('registro.html')

        try:
            # Insertar el nuevo usuario
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usuarios (usuario, password, pais) VALUES (?, ?, ?)",
                (usuario, generate_password_hash(password), pais),
            )
            conn.commit()

            # Obtener el ID del usuario recién registrado
            new_user_id = cursor.lastrowid
            
            # Obtener el objeto de usuario completo para generar el token
            new_user = conn.execute(
                'SELECT * FROM usuarios WHERE id = ?', (new_user_id,)
            ).fetchone()

            if new_user:
                # Generar el token JWT para el nuevo usuario
                token = jwt.encode({
                    'user_id': new_user['id'],
                    'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1) # Token válido por 1 hora
                }, app.config['SECRET_KEY'], algorithm="HS256")
                
                # Crear la respuesta de redirección y establecer la cookie
                response = make_response(redirect('/bienvenida'))
                response.set_cookie('token', token, httponly=True, samesite='Lax') # httponly para seguridad, samesite para protección CSRF
                
                flash(f"¡Registro exitoso! Bienvenido, {new_user['Usuario']}.", 'success')
                return response
            else:
                flash("Error al recuperar el usuario registrado para iniciar sesión.", "danger")
                return render_template('registro.html')

        except sqlite3.Error as e:
            flash(f"Error en la base de datos: {e}", "danger")
            print(e)
            return render_template('registro.html')
        finally:
            conn.close()

    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Página de inicio de sesión.
    Ahora, al iniciar sesión exitosamente, redirige a /bienvenida.
    """
    if request.method == 'POST':
        usuario_form = request.form['usuario']
        password_form = request.form['password']
        
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row
        user = conn.execute(
            'SELECT * FROM usuarios WHERE usuario = ?', (usuario_form,)
        ).fetchone()
        conn.close()

        if not user or not check_password_hash(user['password'], password_form):
            flash('Usuario o contraseña incorrectos.', 'danger')
            return render_template('login.html')

        # Generar el token JWT
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1) # Token válido por 1 hora
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        # Crear la respuesta de redirección y establecer la cookie
        response = make_response(redirect('/panel')) # Redirige a bienvenida
        response.set_cookie('token', token, httponly=True, samesite='Lax')
        flash(f"¡Bienvenido de nuevo, {user['Usuario']}!", 'success')
        return response

    return render_template('login.html')

@app.route('/bienvenida')
@token_required
def bienvenida(current_user):
    """Página de bienvenida después de iniciar sesión o registrarse."""
    return render_template('bienvenida.html', nombre_usuario=current_user['Usuario'])

@app.route('/panel')
@token_required
def panel(current_user):
    """Panel de usuario, ruta protegida por JWT."""
    db = sqlite3.connect(app.config['DATABASE'])
    cursor = db.cursor()
    try:
        # Obtener los objetivos del usuario actual
        cursor.execute("SELECT objetivos FROM usuarios WHERE usuario = ?", (current_user['Usuario'],))
        result = cursor.fetchone()
        if result:
            objetivos = result[0].split(";")
        else:
            objetivos = "No se encontraron objetivos para este usuario."
    except sqlite3.Error as e:
        flash("Error al acceder a la base de datos.")
        objetivos = "Error al cargar los objetivos."
    finally:
        cursor.close()
    
    return render_template('panel.html', nombre_usuario=current_user['Usuario'], objetivos=objetivos)


@app.route('/seleccionar_objetivos', methods=['GET', 'POST'])
@token_required
def seleccionar_objetivos(current_user):
    """Página para establecer objetivos, ruta protegida."""
    if request.method == 'POST':       
        objetivos_seleccionados = request.form.getlist('objetivos')
        if not objetivos_seleccionados:
            flash("Por favor, selecciona al menos un objetivo.")
            return redirect('/panel')
        
        if len(objetivos_seleccionados) < 2:
            flash("Selecciona al menos dos objetivos.")
            return redirect('/panel')
        if objetivos_seleccionados:
            objetivos_str = ";".join(objetivos_seleccionados)
            conn = sqlite3.connect(app.config['DATABASE'])
            try:
                # Actualizar el campo 'objetivos' del usuario actual
                conn.execute('UPDATE usuarios SET objetivos = ? WHERE id = ?', 
                             (objetivos_str, current_user['id']))
                conn.commit()
                flash('Objetivo guardado correctamente.', 'success')
                return redirect('/panel')
            except sqlite3.Error as e:
                flash(f"Error al guardar el objetivo: {e}", "danger")
            finally:
                conn.close()
        else:
            flash("Debes escribir un objetivo.", "warning")

    # Obtener el objetivo actual del usuario para mostrarlo en el formulario
    current_objetivo = current_user['objetivos'] if current_user and 'objetivos' in current_user else ''
    return render_template('objetivos.html', nombre_usuario=current_user['Usuario'], current_objetivo=current_objetivo)

@app.route('/organizacion', methods=['GET', 'POST'])
@token_required
def organizacion(current_user):
    """Página de organización, ruta protegida."""
    recomendacion = None
    if request.method == 'POST':
        # Obtener datos del formulario
        materia = request.form.get('materia')
        horas = request.form.get('horas')
        objetivo = request.form.get('objetivo')

        # Validar datos
        if not materia or not horas or not objetivo:
            recomendacion = "Por favor, completa todos los campos del formulario."
        else:
            try:
                horas = int(horas)
                if horas <= 0:
                    recomendacion = "Por favor, ingresa un número de horas válido."
                else:
                    # Lógica de recomendación
                    recomendacion = generar_recomendacion(materia, horas, objetivo)
            except ValueError:
                recomendacion = "Por favor, ingresa un número válido para las horas de estudio."

    return render_template('organizacion.html', recomendacion=recomendacion, nombre_usuario=current_user['Usuario'])

@app.route('/bienestar_emocional', methods=['GET', 'POST'])
@token_required
def bienestar_emocional(current_user):
    """Página de bienestar emocional, ruta protegida."""
    recomendacion = None
    if request.method == 'POST':
        emociones = request.form.get('emociones')
        estrategias = request.form.get('estrategias')
        actividades = request.form.get('actividades')

        # Validación básica
        if not emociones or not estrategias or not actividades:
            recomendacion = "Por favor, completa todos los campos."
        else:
            # Lógica de recomendación
            recomendacion = generar_recomendacion_emocional(emociones, estrategias, actividades)

    return render_template('bienestar_emocional.html', recomendacion=recomendacion, nombre_usuario=current_user['Usuario'])

# Endpoint para la gestión de tiempo
@app.route('/gestion_tiempo', methods=['GET', 'POST'])
@token_required
def gestion_tiempo(current_user):
    """Página de gestión de tiempo, ruta protegida."""
    recomendacion = None
    if request.method == 'POST':
        tareas = request.form.get('tareas')
        prioridades = request.form.get('prioridades')
        bloques = request.form.get('bloques')

        # Validación básica
        if not tareas or not prioridades or not bloques:
            recomendacion = "Por favor, completa todos los campos."
        else:
            try:
                bloques = int(bloques)
                if bloques <= 0:
                    recomendacion = "Por favor, ingresa un número válido de bloques de tiempo."
                else:
                    # Lógica de recomendación
                    recomendacion = generar_recomendacion_tiempo(tareas, prioridades, bloques)
            except ValueError:
                recomendacion = "Por favor, ingresa un número válido para los bloques de tiempo."

    return render_template('gestion_tiempo.html', recomendacion=recomendacion, nombre_usuario=current_user['Usuario'])

# Endpoint para el crecimiento espiritual
@app.route('/crecimiento_espiritual', methods=['GET', 'POST'])
@token_required
def crecimiento_espiritual(current_user):
    """Página de crecimiento espiritual, ruta protegida."""
    recomendacion = None
    if request.method == 'POST':
        practicas = request.form.get('practicas')
        reflexiones = request.form.get('reflexiones')
        metas = request.form.get('metas')

        # Validación básica
        if not practicas or not reflexiones or not metas:
            recomendacion = "Por favor, completa todos los campos."
        else:
            # Lógica de recomendación
            recomendacion = generar_recomendacion_espiritual(practicas, reflexiones, metas)

    return render_template('crecimiento_espiritual.html', recomendacion=recomendacion, nombre_usuario=current_user['Usuario'])

# Endpoint para el desarrollo de hábitos
@app.route('/desarrollo_habitos', methods=['GET', 'POST'])
@token_required
def desarrollo_habitos(current_user):
    """Página de desarrollo de hábitos, ruta protegida."""
    recomendacion = None
    if request.method == 'POST':
        habitos = request.form.get('habitos')
        acciones = request.form.get('acciones')
        duracion = request.form.get('duracion')

        # Validación básica
        if not habitos or not acciones or not duracion:
            recomendacion = "Por favor, completa todos los campos."
        else:
            try:
                duracion = int(duracion)
                if duracion <= 0:
                    recomendacion = "Por favor, ingresa un número válido para la duración del hábito."
                else:
                    # Lógica de recomendación
                    recomendacion = generar_recomendacion_habitos(habitos, acciones, duracion)
            except ValueError:
                recomendacion = "Por favor, ingresa un número válido para la duración del hábito."

    return render_template('desarrollo_habitos.html', recomendacion=recomendacion, nombre_usuario=current_user['Usuario'])

# Endpoint para la reflexión y propósito
@app.route('/reflexion_proposito', methods=['GET', 'POST'])
@token_required
def reflexion_proposito(current_user):
    """Página de reflexión y propósito, ruta protegida."""
    recomendacion = None
    if request.method == 'POST':
        reflexion = request.form.get('reflexion')
        proposito = request.form.get('proposito')

        # Validación básica
        if not reflexion or not proposito:
            recomendacion = "Por favor, completa todos los campos."
        else:
            # Lógica de recomendación
            recomendacion = generar_recomendacion_reflexion_proposito(reflexion, proposito)

    return render_template('reflexion_proposito.html', recomendacion=recomendacion, nombre_usuario=current_user['Usuario'])

@app.route('/logout')
def logout():
    """Cierra la sesión eliminando la cookie del token."""
    response = redirect('/login')
    response.delete_cookie('token')
    flash("Has cerrado sesión correctamente.", 'info')
    return response

if __name__ == '__main__':
    # Asegurarse de que la base de datos y las tablas existan al iniciar
    crear_tablas() 
    app.run(debug=True)