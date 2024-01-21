import flet as ft


storage = ""


class ClientStorage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.storage = page.client_storage

        self.background_image = self.get("background-image", "Не задан")
        self.font_family = self.get("font-family", "Times New Roman")
        self.font_size = self.get('font-size', 18)
        self.font_color = self.get("font-color", "#000000")

    def save(self):
        self.set("background-image", self.background_image)
        self.set("font-family", self.font_family)
        self.set("font-size", self.font_size)
        self.set("font-color", self.font_color)

    @property
    def theme_mode(self):
        return self.get("theme-mode", "dark")

    @theme_mode.setter
    def theme_mode(self, value):
        self.page.theme_mode = value
        self.set("theme-mode", value)

    def get(self, key, default=None):
        if self.storage.contains_key(key):
            return self.storage.get(key)
        return default

    def set(self, key, value):
        return self.storage.set(key, value)


def get_storage() -> ClientStorage:
    return storage


def init_storage(page: ft.Page):
    global storage
    storage = ClientStorage(page)
    return storage
