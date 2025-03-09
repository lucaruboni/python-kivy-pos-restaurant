from kivy.config import Config
Config.set('graphics', 'fullscreen', '0')

from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.core.window import Window
from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.list import MDListItem
from kivymd.uix.button import MDButton
from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from database import Database
from kivy.uix.popup import Popup
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import MDListItem
from kivy.uix.label import Label
import sqlite3
import hashlib
import os

# Imposta una densità fissa per evitare lo scaling automatico su schermi ad alta risoluzione
os.environ['KIVY_METRICS_DENSITY'] = '0.8'

Window.left = 0
Window.top = 30
Window.size = (1920, 1001)

# Definizione delle schermate

class LoginScreen(Screen):
    pass

class OptionScreen(Screen):
    pass

class CreateCategoryScreen(Screen):
    pass

class MenuScreen(Screen):
    pass

class OrderScreen(Screen):
    pass

class TimeSelectionScreen(Screen):
    pass

class POSPizzeriaApp(MDApp):
    # Definiamo le proprietà come Kivy Properties in modo che siano osservabili dal KV
    num_articles = NumericProperty(0)
    delivery_time_text = StringProperty("Ora")
    customer_name_text = StringProperty("Cliente al banco")
    articles_text = StringProperty("0")


    def build(self):
        """Carica il file KV e inizializza il database"""
        self.db = Database()
        return Builder.load_file("pos.kv")  # Carica lo ScreenManager definito nel file KV
    
    def verify_credentials(self, username, password):
        """Verifica le credenziali confrontando il valore hash della password.
           Supponiamo di avere un database SQLite 'users.db' con una tabella 'users'
           contenente le colonne 'username' e 'password' (il campo password contiene l'hash SHA-256)."""
        try:
            conn = sqlite3.connect("pos_pizzeria.db")
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            conn.close()
            if row is None:
                return False
            stored_hash = row[0]
            hash_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            return stored_hash == hash_password
        except Exception as e:
            print("Error in verify_credentials:", e)
            return False

    def login(self, username, password):
        if self.verify_credentials(username, password):
            print("Login successful!")
            # Dopo il login, passa allo screen delle opzioni
            self.root.current = "option"
        else:
            print("Invalid credentials!")
            self.show_error_popup("Username or password incorrect.")

    def show_error_popup(self, message):
        popup = Popup(title="Authentication Error",
                      content=Label(text=message),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

    def create_category(self, cat_name):
        cat_name = cat_name.strip()
        if cat_name:
            print(f"Category '{cat_name}' created/updated successfully!")
            try:
                # Supponiamo di avere un database SQLite 'categories.db' e una tabella 'categories'
                conn = sqlite3.connect("pos_pizzeria.db")
                cursor = conn.cursor()
                # Crea la tabella se non esiste
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE
                    )
                """)
                cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat_name,))
                conn.commit()
                conn.close()
            except Exception as e:
                print("Error creating category:", e)
                self.show_error_popup("Error saving category.")
        else:
            print("Invalid category name!")
            self.show_error_popup("Please enter a valid category name.")

    def save_category(self, cat_name, grid_slot_text):
        cat_name = cat_name.strip()
        if not cat_name:
            self.show_error_popup("Inserisci un nome valido per la categoria.")
            return
        try:
            grid_slot = int(grid_slot_text) if grid_slot_text.strip() else None
        except ValueError:
            self.show_error_popup("La posizione deve essere un numero.")
            return

        # Usa il database per inserire la categoria
        cat_id = self.db.insert_category(cat_name, grid_slot)
        if cat_id:
            print(f"Categoria '{cat_name}' salvata con successo (slot: {grid_slot}).")
        else:
            self.show_error_popup("Errore: la categoria potrebbe già esistere.")

    def add_product_to_category(self, cat_name, prod_name, prod_price_text):
        cat_name = cat_name.strip()
        prod_name = prod_name.strip()
        if not (cat_name and prod_name and prod_price_text.strip()):
            self.show_error_popup("Compila tutti i campi per il prodotto.")
            return
        try:
            prod_price = float(prod_price_text)
        except ValueError:
            self.show_error_popup("Il prezzo deve essere un numero.")
            return

        # Trova l'ID della categoria
        cat_id = self.db.get_category_id(cat_name)
        if cat_id is None:
            self.show_error_popup("Categoria non trovata. Salva la categoria prima di aggiungere prodotti.")
            return

        result = self.db.insert_category_product(cat_id, prod_name, prod_price)
        if result:
            print(f"Prodotto '{prod_name}' aggiunto alla categoria '{cat_name}' con prezzo {prod_price}.")
        else:
            self.show_error_popup("Errore nell'aggiunta del prodotto.")

    def load_categories(self):
        # Recupera lo screen "menu" e la griglia
        menu_screen = self.root.get_screen("menu")
        grid = menu_screen.ids.top_product_grid
        grid.clear_widgets()  # Pulisce la griglia

        # Recupera le categorie dal database
        categories = self.db.fetch_categories()  # Supponiamo che restituisca tuple (id, name, grid_slot)

        # Ordina le categorie per grid_slot (se grid_slot è None, lo mettiamo in fondo)
        sorted_categories = sorted(categories, key=lambda x: x[2] if x[2] is not None else 999)

        # Per ogni categoria, crea un ClickableBox
        for cat in sorted_categories:
            box = ClickableBox(text=cat[1])
            # Quando il box viene cliccato, chiama il metodo per mostrare i prodotti
            box.bind(on_release=lambda instance, cat_id=cat[0]: self.show_category_products(cat_id))
            grid.add_widget(box)
        

    def open_category_menu(self, widget):
        # widget è il MDTextField che attiverà il menu
        categories = self.db.fetch_categories()  # Supponiamo che ritorni tuple (id, name, grid_slot)
        menu_items = [
            {"viewclass": "OneLineListItem",
             "text": cat[1],
             "md_bg_color": (0, 0, 0, 1),
             "on_release": lambda x=cat[1]: self.set_category(widget, x)}
            for cat in categories
        ]
        self.menu = MDDropdownMenu(
            caller=widget,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()

    def set_category(self, widget, category_name):
        widget.text = category_name
        self.menu.dismiss()

    # -----------------------------
    # Metodi per la cassa (MenuScreen)
    # -----------------------------

    def on_start(self):
        """Al termine del caricamento, carica gli ordini dal database"""
        Clock.schedule_once(self.load_orders, 1)

    def show_category_products(self, cat_id):
        products = self.db.fetch_category_products(cat_id)  # Assicurati di avere questo metodo nel tuo database
        if not products:
            content_text = "Nessun prodotto per questa categoria."
        else:
            # Supponendo che ogni prodotto sia una tupla con (id, category_id, product_name, price)
            content_text = "\n".join([f"{p[2]} - {p[3]:.2f}€" for p in products])

        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        popup = Popup(title="Prodotti della Categoria",
                      content=Label(text=content_text),
                      size_hint=(None, None), size=(400, 400))
        popup.open()


    def add_to_order(self, name, price):
        """Aggiunge un prodotto all'ordine e aggiorna il totale"""
        screen = self.root.get_screen("menu")
        order_list = screen.ids.order_list
        order_list.add_widget(MDListItem(text=f"{name} - {price}€"))
        self.update_total(price)

    def update_total(self, price):
        """Aggiorna il totale dell'ordine in tempo reale"""
        screen = self.root.get_screen("menu")
        total_label = screen.ids.total_label
        # Estrae il totale corrente dal testo (supponendo il formato "Totale: X.XX€")
        current_total = float(total_label.text.split(": ")[1].replace("€", ""))
        total_label.text = f"Totale: {current_total + price:.2f}€"

    def load_orders(self, *args):
        """Carica gli ordini dal database nello schermo degli ordini"""
        try:
            screen = self.root.get_screen("orders")
            if "order_list" not in screen.ids:
                print("❌ ERRORE: `order_list` non trovato in pos.kv!")
                return

            order_list = screen.ids.order_list
            order_list.clear_widgets()

            for order in self.db.fetch_orders():
                item = MDListItem(
                    text=f"Ordine {order[0]} - {order[4]}",
                    on_release=lambda x, order_id=order[0]: self.view_order(order_id)
                )
                order_list.add_widget(item)
    
        except Exception as e:
            print(f"❌ ERRORE load_orders(): {e}")

    def view_order(self, order_id):
        """Mostra i dettagli di un ordine (ad esempio in console)"""
        details = self.db.fetch_order_details(order_id)
        print(f"📝 Dettagli ordine {order_id}: {details}")

    def send_to_kitchen(self, order_id):
        """Invia la comanda alla cucina"""
        details = self.db.fetch_order_details(order_id)
        print(f"🍕 Stampo comanda per ordine {order_id}: {details}")

    def print_preconto(self, order_id):
        """Stampa il preconto per il cliente o rider"""
        details = self.db.fetch_order_details(order_id)
        print(f"🧾 Stampo preconto per ordine {order_id}: {details}")

    def num_press(self, number):
        """Gestisce la pressione di un numero sul tastierino"""
        print(f"Tasto premuto: {number}")

    def set_delivery_time(self, time):
        """Imposta l'orario di consegna e aggiorna il testo dinamico"""
        self.delivery_time_text = time
        print(f"Orario di consegna selezionato: {time}")


class OneLineListItem(MDListItem):
    pass

class ClickableBox(ButtonBehavior, BoxLayout):
    text = StringProperty("")  # Proprietà osservabile

    def on_release(self):
        print("Cella cliccata!", self)

if __name__ == "__main__":
    POSPizzeriaApp().run()
