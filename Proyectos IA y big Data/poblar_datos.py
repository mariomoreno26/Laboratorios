import mysql.connector

config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'sqoopuser',
    'password': 'sqooppassword',
    'database': 'ventas_db'
}

try:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

   
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(100),
        email VARCHAR(100)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        cliente_id INT,
        producto VARCHAR(100),
        monto DECIMAL(10, 2),
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    
    clientes_datos = [(f"Usuario_{i}", f"usuario{i}@example.com") for i in range(1, 1001)]
    pedidos_datos = [(i, f"Producto_{i}", round(10.5 * (i % 50 + 1), 2)) for i in range(1, 1001)]

    
    cursor.executemany("INSERT INTO clientes (nombre, email) VALUES (%s, %s);", clientes_datos)
    cursor.executemany("INSERT INTO pedidos (cliente_id, producto, monto) VALUES (%s, %s, %s);", pedidos_datos)

    conn.commit()
    print("¡Éxito! Se han creado las tablas e insertado 1000 registros en 'clientes' y 'pedidos'.")

except mysql.connector.Error as err:
    print(f"Error al conectar o insertar en MySQL: {err}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()