# create_test_db.py
import sqlite3

# Créer la base
conn = sqlite3.connect('test_database.db')
cursor = conn.cursor()

# Tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER DEFAULT 0,
    category TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    quantity INTEGER,
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total REAL,
    FOREIGN KEY (product_id) REFERENCES products (id)
)
''')

# Données
products = [
    ('Laptop Pro', 1299.99, 10, 'Électronique'),
    ('Smartphone X', 899.99, 25, 'Électronique'),
    ('Casque Audio', 199.99, 50, 'Accessoires'),
    ('Clavier Mécanique', 89.99, 30, 'Accessoires'),
]

cursor.executemany(
    'INSERT OR IGNORE INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)',
    products
)

conn.commit()
conn.close()

print("  Base de données SQLite créée: test_database.db")