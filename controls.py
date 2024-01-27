import flet as ft
from storage import get_storage
from time import sleep


class DocumentField(ft.TextField):
    def __init__(self):
        super().__init__(
            multiline=True,
            border=ft.InputBorder.NONE
        )


class BackgroundImage(ft.Container):
    def __init__(self, src, content):
        super().__init__(
            image_src=src,
            image_fit=ft.ImageFit.COVER,
            expand=True,
            content=content
        ),


class CustomAlertDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page,
                 title: str, content: str,
                 confirm_action: ft.TextButton,
                 cancel_action: ft.TextButton = None):

        if not cancel_action:
            cancel_action = ft.TextButton("Отмена", on_click=lambda _: self.page.close_dialog())

        super().__init__(
            title=ft.Text(title),
            content=ft.Text(content),
            actions=[
                confirm_action,
                cancel_action
            ],
            modal=True
        )

        self.page = page

    def close_dlg(self):
        self.page.close_dialog()
        sleep(0.1)

    def open_dlg(self):
        self.page.dialog = self
        self.open = True
        self.page.update()


class CustomAppBar(ft.AppBar):
    def __init__(self, title: str, leading: str = None, actions=[]):
        super().__init__(title=ft.Text(title), bgcolor=ft.colors.BLACK26)

        if leading:
            self.leading = ft.Icon(leading)

        self.actions = [
            ft.IconButton(ft.icons.SUNNY, on_click=self.change_theme, tooltip="Поменять тему"),
            ft.IconButton(ft.icons.HIDE_SOURCE, on_click=self.toggle_background_appbar,
                          tooltip="Убрать панель (чтобы вернуть, нажмите Tab)"),
            *actions
        ]
        self.storage = get_storage()

    def toggle_background_appbar(self, _):
        self.visible = not self.visible
        self.page.update()

    def change_theme(self, _):
        theme_mode = self.page.theme_mode
        self.storage.theme_mode = "light" if theme_mode == "dark" else "dark"
        self.page.update()



