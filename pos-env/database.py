import sqlite3
import os

class Database:
    def __init__(self, db_name="pos_pizzeria.db"):
        """Crea il database se non esiste e apre la connessione"""
        self.db_path = os.path.join(os.getcwd(), db_name)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Crea tutte le tabelle necessarie al funzionamento del POS"""
        self.cursor.executescript("""
            -- MENU: Pizze, panini, bibite, ecc.
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL
            );

            -- ORDINI: Asporto/Domicilio con stato e totale
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                total REAL DEFAULT 0,
                status TEXT DEFAULT 'In Attesa',
                order_type TEXT CHECK(order_type IN ('Asporto', 'Domicilio')),
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            );

            -- CLIENTI: Nome, telefono e indirizzo
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                address TEXT
            );

            -- DETTAGLI ORDINE: Pizze acquistate e modifiche ingredienti
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                item_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                price REAL NOT NULL,
                notes TEXT,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            );

            -- UTENTE ADMIN: Un solo admin con password sicura
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );

            -- PAGAMENTI: Metodo di pagamento e importo
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                payment_method TEXT CHECK(payment_method IN ('Contanti', 'Carta')),
                amount REAL NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            );

            -- LOG EVENTI: Traccia modifiche importanti (es. cambio prezzo)
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL,
                details TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- CATEGORIE: Per gestire le categorie di prodotto, inclusa la posizione nella griglia
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                grid_slot INTEGER DEFAULT NULL
            );

            -- CATEGORY_PRODUCTS: Prodotti associati ad una categoria
            CREATE TABLE IF NOT EXISTS category_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY(category_id) REFERENCES categories(id)
            );     
                                                                              
        """)
        self.conn.commit()

    def insert_menu_item(self, name, price, category):
        """Aggiunge un nuovo elemento al menu"""
        try:
            self.cursor.execute(
                "INSERT INTO menu (name, price, category) VALUES (?, ?, ?)", 
                (name, price, category)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Nome già esistente

    def update_menu_item(self, item_id, new_price):
        """Aggiorna il prezzo di un elemento nel menu"""
        self.cursor.execute(
            "UPDATE menu SET price = ? WHERE id = ?", 
            (new_price, item_id)
        )
        self.conn.commit()

    def delete_menu_item(self, item_id):
        """Elimina un elemento dal menu"""
        self.cursor.execute("DELETE FROM menu WHERE id = ?", (item_id,))
        self.conn.commit()

    def fetch_menu(self):
        """Ottiene l'intero menu"""
        self.cursor.execute("SELECT * FROM menu ORDER BY category, name")
        return self.cursor.fetchall()

    def search_menu(self, query):
        """Cerca piatti nel menu (ricerca live)"""
        self.cursor.execute("SELECT * FROM menu WHERE name LIKE ?", ('%' + query + '%',))
        return self.cursor.fetchall()

    def create_order(self, customer_id, order_type, delivery_time=None):
        """Crea un nuovo ordine di asporto o domicilio"""
        self.cursor.execute(
            "INSERT INTO orders (customer_id, order_type, status, timestamp) VALUES (?, ?, 'In Attesa', ?)",
            (customer_id, order_type, delivery_time if delivery_time else "Orario non specificato"),
        )
        self.conn.commit()
        return self.cursor.lastrowid  # Restituisce l'ID del nuovo ordine

    def add_order_item(self, order_id, item_name, quantity, price, notes=""):
        """Aggiunge un prodotto all'ordine"""
        self.cursor.execute(
            "INSERT INTO order_items (order_id, item_name, quantity, price, notes) VALUES (?, ?, ?, ?, ?)",
            (order_id, item_name, quantity, price, notes),
        )
        self.conn.commit()

    def fetch_orders(self, order_type=None):
        """Recupera tutti gli ordini o filtra per tipo"""
        if order_type:
            self.cursor.execute("SELECT * FROM orders WHERE order_type = ? ORDER BY timestamp DESC", (order_type,))
        else:
            self.cursor.execute("SELECT * FROM orders ORDER BY timestamp DESC")
        return self.cursor.fetchall()

    def fetch_order_details(self, order_id):
        """Recupera i dettagli di un ordine specifico"""
        self.cursor.execute("SELECT item_name, quantity, price, notes FROM order_items WHERE order_id = ?", (order_id,))
        return self.cursor.fetchall()

    # Nuove funzioni per le categorie

    def insert_category(self, name):
        """Inserisce una nuova categoria nel database"""
        try:
            self.cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Categoria già esistente

    def update_category(self, category_id, new_name):
        """Aggiorna il nome di una categoria"""
        try:
            self.cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (new_name, category_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def fetch_categories(self):
        self.cursor.execute("SELECT id, name, grid_slot FROM categories ORDER BY grid_slot ASC")
        return self.cursor.fetchall()
    
    def fetch_category_products(self, category_id):
        self.cursor.execute("SELECT * FROM category_products WHERE category_id = ?", (category_id,))
        return self.cursor.fetchall()
    
    def insert_category(self, name, grid_slot=None):
        """Inserisce una nuova categoria nel database.
           Restituisce l'ID della categoria se l'inserimento è andato a buon fine, altrimenti None."""
        try:
            self.cursor.execute("INSERT INTO categories (name, grid_slot) VALUES (?, ?)", (name, grid_slot))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_category_id(self, name):
        """Restituisce l'ID della categoria con il nome dato."""
        self.cursor.execute("SELECT id FROM categories WHERE name = ?", (name,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def insert_category_product(self, category_id, product_name, price):
        """Inserisce un prodotto associato a una categoria."""
        try:
            self.cursor.execute(
                "INSERT INTO category_products (category_id, product_name, price) VALUES (?, ?, ?)",
                (category_id, product_name, price)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
