from kivy.config import Config
Config.set('graphics', 'fullscreen', '0')

from kivymd.app import MDApp
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
from kivy.uix.popup import Popup
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import MDListItem
from kivy.uix.label import Label
from kivymd.uix.chip import MDChip, MDChipText
from kivy.properties import ListProperty
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


class CategoryChip(MDChip):
    my_text = StringProperty("")

    def __init__(self, **kwargs):
        if "text" in kwargs:
            self.my_text = kwargs.pop("text")
        # Imposta il tipo filter e il colore selezionato:
        kwargs.setdefault("type", "filter")
        kwargs.setdefault("selected_color", [0, 0.5, 1, 1])  # ad esempio un blu acceso
        kwargs.setdefault("md_bg_color", [1, 1, 1, 1])
        super().__init__(**kwargs)
        chip_text = MDChipText(
            text=self.my_text,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 1],
        )
        self.add_widget(chip_text)

class MenuScreen(Screen):
    pass

class SearchProductScreen(Screen):
    pass

class OrderScreen(Screen):
    pass

class TimeSelectionScreen(Screen):
    pass

class POSPizzeriaApp(ScreenManager):
    # Definiamo le proprietà come Kivy Properties in modo che siano osservabili dal KV
    num_articles = NumericProperty(0)
    delivery_time_text = StringProperty("Ora")
    customer_name_text = StringProperty("Cliente al banco")
    articles_text = StringProperty("0")
    selected_category = StringProperty("")
    current_category = StringProperty("")  
    order_items = ListProperty([])  # Questa lista conterrà gli articoli dell'ordine
    db = MDApp.get_running_app().db


    def verify_credentials(self, username, password):
        """Verifica le credenziali confrontando il valore hash della password.
           Supponiamo di avere un database SQLite 'users.db' con una tabella 'users'
           contenente le colonne 'username' e 'password' (il campo password contiene l'hash SHA-256)."""
        try:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(BASE_DIR, "pos_pizzeria.db")
            conn = sqlite3.connect(db_path)
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
            self.current = "option"
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

    def add_product_to_category(self, product_name, product_price_text):
        category_name = self.selected_category.strip()
        product_name = product_name.strip()
        if not (category_name and product_name and product_price_text.strip()):
            self.show_error_popup("Compila tutti i campi per il prodotto.")
            return
        try:
            prod_price = float(product_price_text)
        except ValueError:
            self.show_error_popup("Il prezzo deve essere un numero.")
            return

        cat_id = self.db.get_category_id(category_name)
        if cat_id is None:
            self.show_error_popup("Categoria non trovata. Salva la categoria prima di aggiungere prodotti.")
            return

        result = self.db.insert_category_product(cat_id, product_name, prod_price)
        if result:
            print(f"Prodotto '{product_name}' aggiunto alla categoria '{category_name}' con prezzo {prod_price}.")
        else:
            self.show_error_popup("Errore nell'aggiunta del prodotto.")

    def go_to_search_screen_with_hero(self, category_name):
        self.current_category = category_name
        self.current_heroes = ["order_summary"]
        self.current = "search_product"  # Assicurati che il nome dello screen sia corretto
        self.load_products(category_name)

    def load_categories(self):
        # Recupera lo screen "menu" e la griglia
        menu_screen = self.get_screen("menu")
        grid = menu_screen.ids.top_product_grid
        grid.clear_widgets()  # Pulisce la griglia

        db = MDApp.get_running_app().db
        categories = db.fetch_categories()

        # Ordina le categorie per grid_slot (se grid_slot è None, lo mettiamo in fondo)
        sorted_categories = sorted(categories, key=lambda x: x[2] if x[2] is not None else 999)

        # Per ogni categoria, crea un ClickableBox
        for cat in sorted_categories:
            box = ClickableBox(text=cat[1])
            # Quando il box viene cliccato, chiama il metodo per mostrare i prodotti
            box.bind(on_release=lambda instance, cat_name=cat[1]: self.go_to_search_screen_with_hero(cat_name))
            grid.add_widget(box)

    def load_category_chips(self):
        screen = self.get_screen("create_category")
        chip_box = screen.ids.category_chip_box
        chip_box.clear_widgets()
        db = MDApp.get_running_app().db
        categories = db.fetch_categories()  # Supponiamo che ritorni tuple (id, name, grid_slot)
        # Ordina per grid_slot (se None, lo posizioniamo alla fine)
        sorted_categories = sorted(categories, key=lambda x: x[2] if x[2] is not None else 999)
        for cat in sorted_categories:
            chip = CategoryChip(text=cat[1])
            chip.bind(on_release=lambda instance, cat_name=cat[1]: self.select_chip(instance, cat_name))
            chip_box.add_widget(chip)

    def select_chip(self, selected_chip, cat_name):
        screen = self.get_screen("create_category")
        chip_box = screen.ids.category_chip_box
        # Imposta tutti i chip come non attivi
        for chip in chip_box.children:
            chip.active = False
        # Imposta il chip cliccato come attivo
        selected_chip.active = True
        self.selected_category = cat_name
        print("Categoria selezionata:", cat_name)
        self.load_products_for_category(cat_name)

    def load_products_for_category(self, cat_name):
        screen = self.get_screen("create_category")
        product_box = screen.ids.product_list_box
        product_box.clear_widgets()
        db = MDApp.get_running_app().db
        cat_id = db.get_category_id(cat_name)
        if not cat_id:
            return
        products = db.fetch_category_products(cat_id)
        if not products:
            from kivy.uix.label import Label
            product_box.add_widget(Label(text="Nessun prodotto", color=(0,0,0,1)))
        else:
            for prod in products:
                # Supponiamo che prod sia una tupla (id, category_id, product_name, price)
                from kivy.uix.label import Label
                product_box.add_widget(Label(text=f"{prod[2]} - {prod[3]:.2f}€", color=(0,0,0,1)))        

    # -----------------------------
    # Metodi per la cassa (MenuScreen)
    # -----------------------------


    def show_category_products(self, cat_id):
        db = MDApp.get_running_app().db
        products = db.fetch_category_products(cat_id)  # Assicurati di avere questo metodo nel tuo database
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

    def show_search_product_screen(self, category_name):
        # Salva la categoria corrente in un attributo dell'app
        self.current_category = category_name
        # Passa allo screen "search_product"
        self.current = "search_product"
        # Carica i prodotti di questa categoria
        self.load_products(category_name)

    def load_products(self, category_name):
        screen = self.get_screen("search_product")
        product_grid = screen.ids.product_grid_search
        product_grid.clear_widgets()

        # Recupera i prodotti della categoria dalla tabella category_products
        db = MDApp.get_running_app().db
        products = db.fetch_products_by_category(category_name)
        if not products:
            from kivy.uix.label import Label
            product_grid.add_widget(Label(text="Nessun prodotto trovato", color=(0,0,0,1)))
        else:
            for prod in products:
                # Assumiamo che prod sia una tupla (id, category_id, product_name, price)
                try:
                    price = float(prod[3])
                except Exception:
                    price = 0.0
                # Crea un clickable box con il nome e il prezzo formattato
                item_box = ClickableBoxSearch(text=f"{prod[2]}\n{price:.2f}€")
                # Quando il box viene cliccato, aggiungi il prodotto all'ordine
                item_box.bind(on_release=lambda instance, p=prod: self.add_to_order(p))
                product_grid.add_widget(item_box)


    def filter_products(self, letter):
        # Recupera i prodotti della categoria corrente
        # e filtra quelli che iniziano per lettera
        screen = self.get_screen("search_product")
        product_grid = screen.ids.product_grid_search
        product_grid.clear_widgets()

        if letter == "":
            # Mostra tutti i prodotti
            db = MDApp.get_running_app().db
            products = db.fetch_products_by_category(self.current_category)
        else:
            products = db.fetch_products_by_first_letter(self.current_category, letter)

        for prod in products:
            item_box = ClickableBoxSearch(text=f"{prod[2]}\n{prod[3]:.2f}€")
            item_box.bind(on_release=lambda instance, p=prod: self.add_to_order(p))
            product_grid.add_widget(item_box)

    def add_to_order(self, product):
        # product è una tupla (id, nome, prezzo, ...)
        screen = self.get_screen("search_product")
        order_list = screen.ids.order_list
        # Aggiungi un item alla lista
        from kivymd.uix.list import MDListItem
        order_list.add_widget(MDListItem(text=f"{product[2]} - {product[3]:.2f}€"))
        # Aggiorna il totale
        self.update_total(product[2])

    def go_to_search_product_screen(self):
        # Diciamo che il tag del hero e' "order_summary"
        self.current_heroes = ["order_summary"]
        self.current = "search_product"

    def add_to_order(self, product):
        """
        product è una tupla o un dizionario contenente i dati del prodotto, ad esempio
        (id, nome, prezzo). Qui salviamo i dettagli che ci interessano.
        """
        self.order_items.append({
            "id": product[1],
            "name": product[2],
            "price": product[3]
        })
        print("Articolo aggiunto all'ordine:", self.order_items)
        self.update_order_summary()  # Aggiorna la vista del riepilogo ordine

    def update_order_summary(self):
        # Supponiamo che il riepilogo ordine sia nello screen "menu" oppure in "search_product"
        # e che l'id della MDList sia "order_list"
        try:
            # Prova ad ottenere lo screen corrente; se vuoi usare uno screen specifico, ad esempio "menu":
            screen = self.get_screen("menu")
            order_list = screen.ids.order_list
        except Exception:
            # Se lo screen "menu" non è disponibile, prova un altro (es. "search_product")
            screen = self.get_screen("search_product")
            order_list = screen.ids.order_list

        order_list.clear_widgets()
        total = 0.0
        from kivymd.uix.list import MDListItem
        for item in self.order_items:
            # Crea un widget per ogni articolo; ad esempio, usando MDListItem
            order_list.add_widget(MDListItem(text=f"{item['name']} - {item['price']:.2f}€"))
            total += item['price']
        # Aggiorna anche il totale
        screen.ids.total_label.text = f"Totale: {total:.2f}€"


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

class ClickableBoxSearch(ButtonBehavior, BoxLayout):
    text = StringProperty("")
    def on_release(self):
        print("Cella cliccata!", self)

