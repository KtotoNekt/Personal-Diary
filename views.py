from flet_contrib.color_picker import ColorPicker
from controls import *
from encryption import *
from diary import *
from abc import ABC, abstractmethod


class CustomView(ft.View, ABC):
    def __init__(self, handler_error, page):
        super().__init__()

        self.hadnler_error = handler_error

        self.page = page
        self.page.on_keyboard_event = self._keyboard_event_handler
        self.page.overlay.clear()

        self.init()

    def _keyboard_event_handler(self, e: ft.KeyboardEvent):
        if not self.page:
            return

        match e.key:
            case "Tab":
                self.appbar.visible = True
                self.page.update()

        self.keyboard_event_handler(e)

    def keyboard_event_handler(self, e):
        pass

    @abstractmethod
    def init(self):
        pass


class MainView(CustomView):
    def __init__(self, handler_error, page):
        self.date_picker = ft.DatePicker(on_change=self.select_date)
        self.import_date_picker = ft.DatePicker(on_change=self.select_import_date)
        self.file_picker = ft.FilePicker(on_result=self.select_file)
        self.dialog_success_import = ft.AlertDialog(
            title=ft.Text("Успех!"),
            content=ft.Text("Запись успешно импортирована!")
        )

        super().__init__(handler_error, page)

    def toggle_banner(self, _):
        self.dialog_success_import.open = not self.dialog_success_import.open
        self.page.dialog = self.dialog_success_import
        self.page.update()

    def select_file(self, e):
        if validate_file_picker_result(e.files):
            self.import_date_picker.pick_date()

    def select_import_date(self, _):
        date = get_date(self.import_date_picker.value)
        if not exists_record(date):
            import_record(date, self.file_picker.result.files[0].path)
            self.toggle_banner(None)
        else:
            self.hadnler_error(f"Запись {date} существует")

    def select_date(self, _):
        date = get_date(self.date_picker.value)
        if exists_record(date):
            self.page.go("/records/" + date)
        else:
            self.hadnler_error("У вас нету записи " + date)

    def init(self):
        scale = 1.3
        create_record_button = ft.ElevatedButton(
            "Новая запись",
            icon=ft.icons.ADD,
            on_click=lambda _: self.page.go("/create-record"),
            # width=200,
            # height=50
            scale=scale
        )
        select_record_button = ft.ElevatedButton(
            "Выбрать запись",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: self.date_picker.pick_date(),
            scale=scale
        )
        import_record_button = ft.ElevatedButton(
            "Импортировать запись",
            icon=ft.icons.IMPORT_EXPORT,
            on_click=lambda _: self.file_picker.pick_files(
                allowed_extensions=["odt", "txt"],
                file_type=ft.FilePickerFileType.ANY,
                allow_multiple=False
            ),
            scale=scale
        )
        settings_button = ft.ElevatedButton(
            "Настройки",
            icon=ft.icons.SETTINGS,
            on_click=lambda _: self.page.go("/settings"),
            scale=scale
        )

        rows = []
        for btn in [create_record_button, select_record_button, import_record_button, settings_button]:
            rows.append(ft.Row(
                [btn],
                alignment=ft.MainAxisAlignment.CENTER,
            ))
        column = ft.Column(rows, alignment=ft.MainAxisAlignment.CENTER, spacing=20)

        self.route = "/"
        for control in [self.date_picker, self.file_picker, self.import_date_picker,]:
            self.page.overlay.append(control)
        self.controls = [
                ft.Container(column, height=500),
        ]
        self.appbar = CustomAppBar("Личный дневник", ft.icons.MENU_BOOK)


class RecordView(CustomView, ABC):
    def __init__(self, handler_error, page):
        self.storage = get_storage()

        super().__init__(handler_error, page)

        self.page.overlay.clear()

        self.doc_field = DocumentField(self.page, self.storage, self.appbar)
        self.change_mode_select_button = ft.IconButton(
            icon=ft.icons.CHECK_BOX,
            tooltip="Режим выбора элементов (Ctrl + D)",
            on_click=lambda _: self.doc_field.change_mode_select()
        )

        self.controls.append(BackgroundImage(self.storage.background_image, self.doc_field))

        self.appbar.actions.append(self.change_mode_select_button)

        self.padding = 0
        self.spacing = 51

    def keyboard_event_handler(self, e: ft.KeyboardEvent):
        if e.key == "D" and e.ctrl:
            self.doc_field.change_mode_select()


class SelectRecordView(RecordView):
    def __init__(self, handler_error, page, date: str):
        self.date = date

        self.edit_button = ft.IconButton(ft.icons.EDIT, on_click=lambda _: self.toggle_buttons(), tooltip="Редактировать")
        self.save_button = ft.IconButton(ft.icons.SAVE, on_click=self.save, tooltip="Сохранить", visible=False)
        self.cancel_button = ft.IconButton(ft.icons.CANCEL, visible=False,
                                           on_click=self.cancel, tooltip="Сбросить до первоначального вида")

        super().__init__(handler_error, page)

        self.dlg_confirm = CustomAlertDialog(
            page,
            title="Подтверждение",
            content="Данная операция не обратима. Вы точно хотите удалить данную запись?",
            confirm_action=ft.TextButton("Да, удалите эту запись", on_click=self.delete_record),
        )
        self.change_mode_select_button.visible = False

        content = read_record(date, self.storage.crypto_key)
        self.doc_field.value = content
        self.doc_field.read_only = True
        self.first_value = self.doc_field.value

    def cancel(self, _):
        self.doc_field.value = self.first_value
        self.toggle_buttons()

    def toggle_buttons(self):
        self.edit_button.visible = not self.edit_button.visible
        self.save_button.visible = not self.save_button.visible
        self.change_mode_select_button.visible = not self.change_mode_select_button.visible

        self.cancel_button.visible = not self.cancel_button.visible

        self.doc_field.read_only = not self.doc_field.read_only
        self.page.update()

    def save(self, _):
        content = self.doc_field.value
        edit_record(self.date, content)
        if_encryption_enable(self.storage, self.date)

        self.first_value = content

        self.toggle_buttons()

    def delete_record(self, _):
        delete_record(self.date)
        self.dlg_confirm.close_dlg()
        self.page.go("/")

    def keyboard_event_handler(self, e: ft.KeyboardEvent):
        super().keyboard_event_handler(e)
        if e.ctrl and e.key == "S" and not self.doc_field.read_only:
            self.save(e)

    def init(self):
        delete_button = ft.IconButton(
            ft.icons.DELETE_FOREVER,
            on_click=lambda _: self.dlg_confirm.open_dlg(),
            tooltip="Удалить запись"
        )

        self.route = "/records/" + self.date
        self.appbar = CustomAppBar("Запись " + self.date, None,
                                   [delete_button, self.edit_button, self.save_button, self.cancel_button])


class CreateRecordView(RecordView):
    def __init__(self, handler_error, page):
        self.date_picker = ft.DatePicker(on_change=self.select_date)
        self.dlg_view_record = CustomAlertDialog(
            page,
            "Просмотр",
            "Вы хотите просмотреть свою запись?",
            ft.TextButton("Да", on_click=self.view_record),
            ft.TextButton("Не сейчас", on_click=self.go_home)
        )

        super().__init__(handler_error, page)

        self.page.overlay.append(self.date_picker)

        self.doc_field._add_text_field()

    def go_home(self, _):
        self.dlg_view_record.close_dlg()
        self.page.go("/")

    def view_record(self, _):
        self.dlg_view_record.close_dlg()
        self.page.go("/records/" + get_date(datetime.now()))

    def save(self, _):
        create_record(self.doc_field.value)
        if_encryption_enable(self.storage, get_date(datetime.now()))
        self.dlg_view_record.open_dlg()

    def select_date(self, _):
        date = get_date(self.date_picker.value)
        if exists_record(date):
            self.hadnler_error("Под этой датой уже есть запись")
        else:
            edit_record(date, self.doc_field.value)
            if_encryption_enable(self.storage, date)
            self.page.go("/records/" + date)

    def keyboard_event_handler(self, e: ft.KeyboardEvent):
        super().keyboard_event_handler(e)
        if e.ctrl and e.key == "S":
            self.save(e)

    def init(self):
        self.route = "/create-record"
        self.appbar = CustomAppBar("Создание записи", None,
                                   [ft.IconButton(ft.icons.SAVE, on_click=self.save, tooltip="Сохранить"),
                                    ft.IconButton(ft.icons.SAVE_AS,
                                                  on_click=lambda _: self.date_picker.pick_date(),
                                                  tooltip="Сохранить под датой")])


class SettingsView(CustomView):
    def __init__(self, handler_error, page):
        self.file_picker = ft.FilePicker(on_result=self.select_background)
        self.storage = get_storage()

        self.bg_image = ft.Image(width=200,
                                 height=200,
                                 fit=ft.ImageFit.COVER, border_radius=25)
        self.bg_image.visible = bool(self.storage.background_image)
        if self.storage.background_image:
            self.bg_image.src = self.storage.background_image

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
        self.text_align_dropdown = ft.Dropdown(options=[
            ft.dropdown.Option("center", "По центру"),
            ft.dropdown.Option("right", "По праву"),
            ft.dropdown.Option("left", "По леву"),
            ft.dropdown.Option(None, "Нету"),
            ft.dropdown.Option("justify", "По ширине"),
            ft.dropdown.Option("start", "По началу"),
            ft.dropdown.Option("end", "По концу"),
        ], value=self.storage.text_align)

        self.encryption_enable = ft.Checkbox(label="Включить шифрование записей",
                                             value=self.storage.encryption_enable,
                                             on_change=self.toggle_visible_encryption_container)
        self.file_save_key_picker = ft.FilePicker(on_result=self.select_file_key, )
        self.file_load_key_picker = ft.FilePicker(on_result=self.load_crypto_key)
        self.column_encryption = ft.Column([
            ft.ElevatedButton(
                "Выбрать файл с ключем",
                on_click=lambda _: self.file_load_key_picker.pick_files(dialog_title="Выберите файл с ключем")
            ),
            ft.ElevatedButton(
                "Сгенерировать и сохранить ключ",
                on_click=lambda _: self.file_save_key_picker.save_file(dialog_title="Сохраните ключ шифрования"))
        ], visible=self.storage.encryption_enable, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.dlg_warning = ft.AlertDialog(title=ft.Text("Предупреждение"),
                                          content=ft.Text("При включенном шифровании при каждом заходе в приложение "
                                                          "будет требоваться выбрать файл с ключем, который будет "
                                                          "использоваться для расшифровки зашифрованых записей, "
                                                          "и для шифрования новых записей"))

        super().__init__(handler_error, page)

    def load_crypto_key(self, e):
        if validate_file_picker_result(e.files):
            try:
                self.storage.crypto_key = get_key(e.files[0].path)
            except ValueError:
                self.hadnler_error("Неверный формат ключа")

    def open_dlg(self):
        self.dlg_warning.open = True
        self.page.dialog = self.dlg_warning

    def select_file_key(self, e: ft.FilePickerResultEvent):
        if e.path:
            crypto_key = generate_and_save_key(e.path)
            self.storage.crypto_key = crypto_key

    def toggle_visible_encryption_container(self, _):
        self.column_encryption.visible = not self.column_encryption.visible
        if self.column_encryption.visible:
            self.open_dlg()
        self.page.update()

    def change_font_family(self, _):
        self.font_family_field.text_style.font_family = self.font_family_field.value
        self.font_family_field.update()

    def change_font_size(self, _):
        self.font_size_field.text_size = self.font_size_field.value
        self.font_size_field.update()

    def select_background(self, e: ft.FilePickerResultEvent):
        if validate_file_picker_result(e.files):
            self.storage.background_image = e.files[0].path
            self.bg_image.src = e.files[0].path
            self.bg_image.visible = bool(self.storage.background_image)
            self.page.update(self.bg_image)

    def save(self, _):
        self.storage.font_family = self.font_family_field.value
        self.storage.font_size = self.font_size_field.value
        self.storage.font_color = self.font_color_picker.color
        self.storage.text_align = self.text_align_dropdown.value
        self.storage.encryption_enable = self.encryption_enable.value

        self.storage.save()
        self.page.go("/")

    def delete_background(self, _):
        self.storage.background_image = ""
        self.bg_image.visible = bool(self.storage.background_image)
        self.page.update(self.bg_image)

    def init(self):
        background_image_text = ft.Text("Задний фон", size=18)

        background_image_button = ft.ElevatedButton(
            text="Изменить" if self.storage.background_image else "Задать",
            icon=ft.icons.IMAGE,
            on_click=lambda _: self.file_picker.pick_files(file_type=ft.FilePickerFileType.IMAGE)
        )
        background_image_delete_button = ft.ElevatedButton(
            "Удалить задний фон",
            on_click=self.delete_background
        )

        font_text = ft.Text("Шрифт", size=18)
        font_color_text = ft.Text("Цвет шрифта")

        text_align_title = ft.Text("Выравнивание", size=18)

        save_button = ft.ElevatedButton(
            text="Сохранить",
            icon=ft.icons.SAVE_ALT,
            on_click=self.save,
        )

        text_encryption = ft.Text("Шифрование", size=18)

        columns = []
        for controls in [[background_image_text, self.bg_image, background_image_button, background_image_delete_button],
                         [font_text, self.font_family_field, self.font_size_field,
                          font_color_text, self.font_color_picker],
                         [text_align_title, self.text_align_dropdown,
                          text_encryption, self.encryption_enable, self.column_encryption]]:
            rows = []
            for control in controls:
                rows.append(ft.Row([control], alignment=ft.MainAxisAlignment.CENTER))

            columns.append(ft.Column(rows))

        self.route = "/settings"
        for control in [self.file_picker, self.file_save_key_picker, self.file_load_key_picker]:
            self.page.overlay.append(control)
        self.controls = [
                ft.GridView(columns, expand=1,
                            runs_count=3),
                ft.Row([save_button], alignment=ft.MainAxisAlignment.CENTER),
            ]
        self.appbar = CustomAppBar("Настройки")