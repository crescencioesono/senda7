import os
import sqlite3


class BaseDatos:
    def __init__(self):
        self.crear_tablas()

    def crear_tablas(self):
        #conectar (crear un archivo db dentro de la carpeta database si no existe)
        conn = sqlite3.connect("usuarios.db")
        cursor = conn.cursor()

        #crear la tabla
        cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Usuario TEXT NOT NULL,
            password TEXT NOT NULL,
            país TEXT NOT NULL    
        )
        ''')  
        cursor.execute('''CREATE TABLE IF NOT EXISTS objetivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            objetivos TEXT NOT NULL,
            id_usuario INTEGER,
            FOREIGN KEY(id_usuario) REFERENCES usuarios(id)              
        )
        ''')    
        conn.commit()
        conn.close()
        print("base de datos creada correctamente.")

    def devolver_conexion(self):
        return sqlite3.connect("usuarios.db")