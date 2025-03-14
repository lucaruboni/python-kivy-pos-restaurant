from kaki.app import App
from kivy.factory import Factory
from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from pos_env.database import Database
from kivy.lang import Builder

class MDLive(App, MDApp):
    CLASSES = {
        "POSPizzeriaApp": "pos_env.main_screen",
    }


    AUTORELOADER_PATHS = [
        (".", {"recursive": True}),
    ]

    def build_app(self, **kwargs):
        print("Building app automatically")
        Builder.load_file("pos_env/pos.kv")
        self.db = Database()
        app_root = Factory.POSPizzeriaApp()
        return app_root
    


if __name__ == "__main__": 
    MDLive().run()