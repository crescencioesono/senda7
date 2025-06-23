from flask import Flask, render_template, request, redirect, flash, session
import re
import sqlite3

from crear_db import BaseDatos

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_flash'
app.secret_key = 'senda7_secret_key'

base_datos = BaseDatos()

@app.route('/', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['Usuario']
        #contrasena = request.form['contrasena'] completar la incritación primero
        password = request.form['password']
        confirmar = request.form['confirmar']
        país = request.form['país']
        
        #contrasena_segura = generate_password_hash(contrasena) #completar primero la parte de incripación de contraseña
        
        conexion = base_datos.devolver_conexion()
        cursor = conexion.cursor()
        
        cursor.execute("SELECT * FROM usuarios WHERE Usuario = ?", (usuario,))
        usuario_existente = cursor.fetchone()
        
        if usuario_existente:
            flash("Este Usuario ya está registrado. Intenta con otro.")
            return redirect('/')
        else:
            cursor.execute("INSERT INTO usuarios (Usuario, password, país) VALUES (?, ?, ?)", (usuario, password, país))
            conexion.commit()
            conexion.close()
            return redirect('/bienvenida')
        
        
        errores = []
        
        #validaciones
        if not nombre or not correo or not password or not confirmar:
            errores.append("Todos los Campos son obligatorios.")
        if password != confirmar:
            errores.append("las contraseñas no coinciden.")
        if len(password) < 8:
            errores.append("La contraseña debe tener almenos 8 caracteres.")
    
        if errores:
            for error in errores:
                flash(error)
                return render_template('registro.html')
        else:
            flash("Registro exitoso. ¡Bienvenido a Senda 7!") 
            return redirect('/bienvenida')       
    
    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['Usuario']
        password = request.form['password']
        
        conn = base_datos.devolver_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE Usuario = ? AND password = ?", (usuario, password))
        usuario = cursor.fetchone()
        conn.close()
        
        if usuario:
            session['usuario_id'] = usuario[0]
            return redirect('/panel')
        else:
            return render_template('login.html', error='Usuario o contraseña incorrectos.')
    return render_template('login.html')

@app.route('/panel')
def panel():
    if 'usuario_id' not in session:
        return redirect('/login') 
    
    usuario_id = session['usuario_id']
    conn = base_datos.devolver_conexion()
    cursor = conn.cursor()
    print(usuario_id)
    cursor.execute('SELECT Usuario FROM usuarios WHERE id = ?', (usuario_id))
    resultado = cursor.fetchone()
    conn.close()
    
    nombre_usuario = resultado[0] if resultado else 'Usuario'
    return render_template('panel.html', nombre_usuario=nombre_usuario) 
       
    
           


@app.route('/bienvenida')
def bienvenida():
    if 'usuario_id' not in session:
        return redirect('/login')
    
    return render_template('bienvenida.html')

@app.route('/objetivos', methods=['GET', 'POST'])
def objetivos():
    if 'usuario_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        objetivo = request.form['objetivos']
        conn = base_datos.devolver_conexion()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET objetivos = ? WHERE id = ?", (objetivo, session['usuario_id']))
        conn.commit()
        conn.close()
        return redirect('/panel')
    
    return render_template('objetivos.html')

@app.route('/organizacion', methods=['GET', 'POST'])
def organizacion():
    recomendacion = None
    if request.method == 'POST':
        materia = request.form['materia']
        horas = int(request.form['horas'])
        objetivo = request.form['objetivo']
        
        #recomendaciones personalizada
        if horas < 2:
            recomendacion = f"Te recomendamos estudiar al menos 2 horas diarias para obtener buenos resultados en {materia}. Recuerda hacer pausas cada 25 minutos. Eso te ayudara a ordenar la informaciñon."
        elif horas <= 4:
            recomendacion = f"Con {horas} horas al dia, puedes lograr tu objetivo en {materia}. Organiza tu estudio en bloques de 40 minutos con 10 minutos de descanso."
        else:
            recomendacion = f"¡Excelente compromiso! Con {horas} horas al dia, alcanzarás tu objrtivo '{objetivo}' rápidamente. No olvides repasar cada un dia o 2 dias para afianzar rl conocimiento."
    
    return render_template('organizacion.html', recomendacion=recomendacion)                
    
    
    
    
    
    
@app.route('/logout')
def logout():
    session.clear()
    flash("Session cerrada correctamente")
    return redirect('/login')




if __name__ == '__main__':
    app.run(debug=True)