from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.list import MDListItem
from kivymd.uix.button import MDButton
from kivy.clock import Clock
from database import Database

# Definizione delle schermate
class MenuScreen(Screen):
    pass

class OrderScreen(Screen):
    pass

class TimeSelectionScreen(Screen):
    pass

class POSPizzeriaApp(MDApp):
    def build(self):
        """Carica il file KV e inizializza il database"""
        self.db = Database()
        return Builder.load_file("pos.kv")  # ✅ Carica lo ScreenManager dal KV

    def on_start(self):
        """Attende il caricamento e poi mostra gli ordini"""
        Clock.schedule_once(self.load_orders, 1)

    def show_category(self, category):
        """Mostra i prodotti di una categoria quando clicco un bottone"""
        screen = self.root.get_screen("menu")
        search_field = screen.ids.search_field
        menu_grid = screen.ids.menu_grid

        search_field.opacity = 1  # ✨ Mostriamo la ricerca
        menu_grid.clear_widgets()

        prodotti = self.db.fetch_menu_by_category(category)

        for item in prodotti:
            btn = MDButton(
                text=item[1],
                md_bg_color=(0, 0, 1, 1),  # Blu per differenziare
                text_color="black",
                on_release=lambda x, name=item[1], price=item[2]: self.add_to_order(name, price)
            )
            menu_grid.add_widget(btn)

    def add_to_order(self, name, price):
        """Aggiunge un prodotto all'ordine"""
        screen = self.root.get_screen("menu")  # ✅ Accedi allo schermo corretto
        order_list = screen.ids.order_list
        order_list.add_widget(MDListItem(text=f"{name} - {price}€"))
        self.update_total(price)

    def update_total(self, price):
        """Aggiorna il totale in tempo reale"""
        screen = self.root.get_screen("menu")  # ✅ Accedi allo schermo corretto
        total_label = screen.ids.total_label
        current_total = float(total_label.text.split(": ")[1].replace("€", ""))
        total_label.text = f"Totale: {current_total + price:.2f}€"

    def load_orders(self, *args):
        """Carica gli ordini dal database"""
        try:
            screen = self.root.get_screen("orders")  # ✅ Accedi allo schermo KV

            # ✅ Controllo se `order_list` esiste
            if "order_list" not in screen.ids:
                print("❌ ERRORE: `order_list` non trovato in pos.kv!")
                return

            order_list = screen.ids.order_list
            order_list.clear_widgets()

            for order in self.db.fetch_orders():
                item = MDListItem(
                    text=f"Ordine {order[0]} - {order[4]}",
                    on_release=lambda x, order_id=order[0]: self.view_order(order_id),
                )
                order_list.add_widget(item)
    
        except Exception as e:
            print(f"❌ ERRORE load_orders(): {e}")

    def view_order(self, order_id):
        """Mostra i dettagli di un ordine"""
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
        """Gestisce la pressione di un numero nel tastierino"""
        print(f"Tasto premuto: {number}")

    def set_delivery_time(self, time):
        """Imposta l'orario di consegna"""
        print(f"Orario di consegna selezionato: {time}")

# Avvio dell'app
if __name__ == "__main__":
    POSPizzeriaApp().run()
