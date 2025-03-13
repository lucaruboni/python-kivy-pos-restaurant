from kaki.app import App
from kivy.factory import Factory
from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout

class MDLive(App, MDApp):
    CLASSES = {
        "POSPizzeriaApp": "pos_env.pos"
    }


    AUTORELOADER_PATHS = [
        (".", {"recursive": True}),
    ]

    def build_app(self, **kwargs):
        print("Building app automatically")
        # Crea l'istanza del widget radice tramite Factory
        app_root = Factory.POSPizzeriaApp()
        # Avvolgi in un contenitore (BoxLayout, FloatLayout, ecc.) per essere sicuri che abbia le proprietà necessarie
        container = BoxLayout()
        container.add_widget(app_root)
        return container
    


if __name__ == "__main__": 
    MDLive().run()