import flet as ft
from flet_contrib.color_picker import ColorPicker
from os.path import isdir
from diary import (
    get_date,
    read_record,
    create_record,
    exists_record,
    edit_record,
    import_record
)
from datetime import datetime
from storage import get_storage


class DocumentField(ft.TextField):
    def __init__(self):
        super().__init__(
            multiline=True,
            border=ft.InputBorder.NONE,
            text_align=ft.TextAlign.CENTER
        )


class BackgroundImage(ft.Container):
    def __init__(self, src, content):
        super().__init__(
            image_src=src,
            image_fit=ft.ImageFit.COVER,
            expand=True,
            content=content
        ),


class CustomAppBar(ft.AppBar):
    def __init__(self, title: str, leading: str = None, actions=[]):
        super().__init__(title=ft.Text(title), bgcolor=ft.colors.BLACK26)

        if leading:
            self.leading = ft.Icon(leading)

        self.actions = [
            ft.IconButton(ft.icons.SUNNY, on_click=self.change_theme, tooltip="Поменять тему"),
            ft.IconButton(ft.icons.HIDE_SOURCE, on_click=self.toggle_background_appbar, tooltip="Убрать панель (чтобы вернуть, нажмите Tab)"),
            *actions
        ]
        self.storage = get_storage()

    def toggle_background_appbar(self, _):
        self.visible = not self.visible
        self.page.update()

    def change_theme(self, e):
        theme_mode = self.page.theme_mode
        self.storage.theme_mode = "light" if theme_mode == "dark" else "dark"
        self.page.update()


class CustomView(ft.View):
    def __init__(self, handler_error, page):
        super().__init__()

        self.hadnler_error = handler_error
        self.page = page
        self.page.on_keyboard_event = self.keyboard_event_handler

        self.init()

    def keyboard_event_handler(self, e: ft.KeyboardEvent):
        if not self.page: return

        match e.key:
            case "Tab":
                self.appbar.visible = True
                self.page.update()

    def init(self):
        pass


class MainView(CustomView):
    def __init__(self, handler_error, page):
        self.date_picker = ft.DatePicker(on_change=self.select_date)
        self.import_date_picker = ft.DatePicker(on_change=self.select_import_date)
        self.file_picker = ft.FilePicker(on_result=self.select_file)
        self.dialog_success_import = ft.AlertDialog(
            title=ft.Text("Успех!"),
            content=ft.Text("Запись успешно импортирована!"),
            actions=[
                ft.TextButton("Ок", on_click=self.toggle_banner)
            ],
        )

        super().__init__(handler_error, page)

    def toggle_banner(self, e):
        self.dialog_success_import.open = not self.dialog_success_import.open
        self.page.update()

    def select_file(self, e):
        if e.files and len(e.files) != 0 and not isdir(e.files[0].path):
            self.import_date_picker.pick_date()

    def select_import_date(self, e):
        date = get_date(self.import_date_picker.value)
        if not exists_record(date):
            import_record(date, self.file_picker.result.files[0].path)
            self.toggle_banner(None)
        else:
            self.hadnler_error(f"Запись {date} существует")

    def select_date(self, e):
        date = get_date(self.date_picker.value)
        if exists_record(date):
            self.page.go("/records/" + date)
        else:
            self.hadnler_error("У вас нету записи " + date)

    def init(self):
        create_record_button = ft.ElevatedButton(
            "Новая запись",
            icon=ft.icons.ADD,
            on_click=lambda _: self.page.go("/create-record")
        )
        select_record_button = ft.ElevatedButton(
            "Выбрать запись",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: self.date_picker.pick_date(),
        )
        import_record_button = ft.ElevatedButton(
            "Импортировать запись",
            icon=ft.icons.IMPORT_EXPORT,
            on_click=lambda _: self.file_picker.pick_files(
                allowed_extensions=["odt", "txt"],
                file_type=ft.FilePickerFileType.ANY,
                allow_multiple=False
            ),
        )
        settings_button = ft.ElevatedButton(
            "Настройки",
            icon=ft.icons.SETTINGS,
            on_click=lambda _: self.page.go("/settings")
        )

        rows = []
        for btn in [create_record_button, select_record_button, import_record_button, settings_button]:
            rows.append(ft.Row(
                [btn],
                alignment=ft.MainAxisAlignment.CENTER
            ))

        self.route = "/"
        self.controls = [
                *rows,
                self.date_picker,
                self.file_picker,
                self.import_date_picker,
                self.dialog_success_import
        ]
        self.appbar = CustomAppBar("Личный дневник", ft.icons.MENU_BOOK)


class RecordView(CustomView):
    def __init__(self, handler_error, page):
        self.doc_field = DocumentField()
        self.storage = get_storage()

        self.doc_field.cursor_color = self.storage.font_color
        self.doc_field.text_style = ft.TextStyle(font_family=self.storage.font_family,
                                                 size=self.storage.font_size,
                                                 color=self.storage.font_color)

        super().__init__(handler_error, page)

        self.controls = [BackgroundImage(self.storage.background_image, self.doc_field)]
        self.padding = 0
        self.spacing = 51


class SelectRecordView(RecordView):
    def __init__(self, handler_error, page, date: str):
        self.date = date

        self.edit_button = ft.IconButton(ft.icons.EDIT, on_click=self.edit, tooltip="Редактировать")
        self.save_button = ft.IconButton(ft.icons.SAVE, on_click=self.save, tooltip="Сохранить", visible=False)
        self.cancel_button = ft.IconButton(ft.icons.CANCEL, visible=False, on_click=self.cancel, tooltip="Сбросить до первоначального вида")

        super().__init__(handler_error, page)

        self.doc_field.read_only = True
        self.doc_field.value = read_record(date)
        self.first_value = self.doc_field.value

    def cancel(self, e):
        self.doc_field.value = self.first_value
        self.toggle_buttons()

    def toggle_buttons(self):
        self.edit_button.visible = not self.edit_button.visible
        self.save_button.visible = not self.save_button.visible

        self.cancel_button.visible = not self.cancel_button.visible

        self.doc_field.read_only = not self.doc_field.read_only
        self.page.update()

    def edit(self, e):
        self.toggle_buttons()

    def save(self, e):
        content = self.doc_field.value
        edit_record(self.date, content)
        self.first_value = content

        self.toggle_buttons()

    def init(self):
        self.route = "/records/" + self.date
        self.appbar = CustomAppBar("Запись " + self.date, None, [self.edit_button, self.save_button, self.cancel_button])


class CreateRecordView(RecordView):
    def save(self, e):
        content = self.doc_field.value
        create_record(content)

        self.page.go("/records/" + get_date(datetime.now()))

    def init(self):
        self.route = "/create-record"
        self.appbar = CustomAppBar("Создание записи", None, [ft.IconButton(ft.icons.SAVE, on_click=self.save)])


class SettingsView(CustomView):
    def __init__(self, handler_error, page):
        self.file_picker = ft.FilePicker(on_result=self.select_background)
        self.storage = get_storage()

        self.bg_image = ft.Image(width=200,
                                 height=200,
                                 src=self.storage.background_image,
                                 fit=ft.ImageFit.COVER, border_radius=25)
        if not self.storage.background_image:
            self.bg_image.visible = False

        self.font_family_field = ft.TextField(label="Название шрифта",
                                              value=self.storage.font_family,
                                              on_change=self.change_font_family,
                                              text_style=ft.TextStyle(font_family=self.storage.font_family))
        self.font_size_field = ft.TextField(label="Размер шрифта",
                                            value=self.storage.font_size,
                                            keyboard_type=ft.KeyboardType.NUMBER,
                                            text_size=self.storage.font_size,
                                            on_change=self.change_font_size)
        self.font_color_picker = ColorPicker()
        self.font_color_picker.color = self.storage.font_color

        super().__init__(handler_error, page)

    def change_font_family(self, e):
        self.font_family_field.text_style.font_family = self.font_family_field.value
        self.font_family_field.update()

    def change_font_size(self, e):
        self.font_size_field.text_size = self.font_size_field.value
        self.font_size_field.update()

    def select_background(self, e: ft.FilePickerResultEvent):
        if e.files and len(e.files) != 0 and not isdir(e.files[0].path):
            self.storage.background_image = e.files[0].path
            self.bg_image.src = e.files[0].path

    def save(self, e):
        self.storage.font_family = self.font_family_field.value
        self.storage.font_size = self.font_size_field.value
        self.storage.font_color = self.font_color_picker.color

        self.storage.save()
        self.page.go("/")

    def init(self):
        background_image_text = ft.Text("Задний фон", size=18)

        background_image_button = ft.ElevatedButton(
            text="Изменить" if self.storage.background_image else "Задать",
            icon=ft.icons.IMAGE,
            on_click=lambda _: self.file_picker.pick_files(file_type=ft.FilePickerFileType.IMAGE)
        )

        font_text = ft.Text("Шрифт", size=18)
        font_color_text = ft.Text("Цвет шрифта")

        save_button = ft.ElevatedButton(
            text="Сохранить",
            icon=ft.icons.SAVE_ALT,
            on_click=self.save,
        )

        columns = []
        for controls in [[background_image_text, self.bg_image, background_image_button],
                         [font_text, self.font_family_field, self.font_size_field, font_color_text, self.font_color_picker]]:
            rows = []
            for control in controls:
                rows.append(ft.Row([control], alignment=ft.MainAxisAlignment.CENTER))

            columns.append(ft.Column(rows))

        self.route = "/settings"
        self.controls = [
                ft.GridView(columns, expand=1,
                            runs_count=3),
                ft.Row([save_button], alignment=ft.MainAxisAlignment.CENTER),
                self.file_picker
            ]
        self.appbar = CustomAppBar("Настройки")
