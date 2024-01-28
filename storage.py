import flet as ft


storage = ""


class ClientStorage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.storage = page.client_storage

        self.background_image = self.get("background-image", "")
        self.font_family = self.get("font-family", "Times New Roman")
        self.font_size = self.get('font-size', 18)
        self.font_color = self.get("font-color", "#000000")
        self.text_align = self.get("text-align", "center")
        self.encryption_enable = self.get("encryption-enable", False)

        self.crypto_key = None

    def save(self):
        for attribute in self.__dir__()[2:]:
            if attribute == "crypto_key":
                break

            self.set(attribute.replace("_", "-"), self.__getattribute__(attribute))

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
