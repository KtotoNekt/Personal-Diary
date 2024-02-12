import flet as ft
from storage import get_storage
from time import sleep
from json import loads, dumps
import os
import shutil
from os.path import splitext, isdir
import uuid


# class DocumentField(ft.TextField):
#     def __init__(self, storage: ClientStorage):
#         super().__init__(
#             multiline=True,
#             border=ft.InputBorder.NONE,
#             cursor_color=storage.font_color,
#             text_align=storage.text_align,
#             text_style=ft.TextStyle(
#                 font_family=storage.font_family,
#                 size=storage.font_size,
#                 color=storage.font_color
#             )
#         )
def validate_file_picker_result(files):
    return files and len(files) != 0 and not isdir(files[0].path)


class BackgroundImage(ft.Container):
    def __init__(self, src, content):
        super().__init__(
            image_src=src,
            image_fit=ft.ImageFit.COVER,
            expand=True,
            content=content
        )


class CustomAlertDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page,
                 title: str, content: str,
                 confirm_action: ft.TextButton = None,
                 cancel_action: ft.TextButton = None,):

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


class DocumentTextField(ft.TextField):
    def __init__(self, storage):
        self.storage = storage

        super().__init__(
            multiline=True,
            border=ft.InputBorder.NONE,
            cursor_color=storage.font_color,
            text_align=storage.text_align,
            text_style=ft.TextStyle(
                font_family=storage.font_family,
                size=storage.font_size,
                color=storage.font_color
            ),
            expand=True,
        )


class DocumentImage(ft.Image):
    def __init__(self, src, *args, **kwargs):
        super().__init__(
            src=src,
            border_radius=20,
            *args,
            **kwargs
        )


class SelectControl(ft.Checkbox):
    def __init__(self, control: ft.Control, on_change):
        super().__init__(visible=False, on_change=lambda _: on_change(self))

        self.control = control


class DocumentField(ft.Column):
    def __init__(self, page: ft.Page, storage, appbar: ft.AppBar):
        super().__init__(scroll=ft.ScrollMode.AUTO)

        self._read_only = False

        self.storage = storage
        self.page = page
        self.appbar = appbar

        self.selected_controls = []

        self.is_change_mode = False

        self.add_dropdown = ft.PopupMenuButton(items=[
            ft.PopupMenuItem(
                icon=ft.icons.IMAGE,
                text="Изображение",
                on_click=lambda _: self.file_picker.pick_files(
                    "Выберите изображение",
                    file_type=ft.FilePickerFileType.IMAGE,
                ),
            ),
            ft.PopupMenuItem(
                icon=ft.icons.TEXT_FIELDS,
                text="Текст",
                on_click=lambda _: self.add_text_field(),
            )
        ], visible=False, icon=ft.icons.ADD)
        self.delete_button = ft.ElevatedButton(
            icon=ft.icons.DELETE,
            text="Удалить",
            on_click=lambda _: self.delete_selected_controls(),
            visible=False
        )
        self.cancel_button = ft.ElevatedButton(
            icon=ft.icons.CANCEL,
            text="Назад",
            on_click=lambda _: self.change_mode_select(),
            visible=False
        )

        self.file_picker = ft.FilePicker(on_result=self._save_file)

        self.width_image = ft.TextField(label="Ширина", keyboard_type=ft.KeyboardType.NUMBER)
        self.height_image = ft.TextField(label="Высота", keyboard_type=ft.KeyboardType.NUMBER)
        self.image = ft.Image(width=300, border_radius=20)

        self.dlg_settings_image = ft.AlertDialog(
            title=ft.Text("Настройки изображения"),
            content=ft.Column(
                [
                    ft.Text("Размеры", size=18),
                    self.width_image,
                    self.height_image,
                    self.image
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            actions=[
                ft.ElevatedButton("Добавить", on_click=self._action_add),
                ft.ElevatedButton("Отменить", on_click=lambda _: self._close_dialog(self.dlg_settings_image))
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            modal=True
        )

        for control in [self.file_picker]:
            self.page.overlay.append(control)

        self.actions_selected_controls = [self.add_dropdown, self.delete_button, self.cancel_button]
        self.visible_actions = []

        for action in self.actions_selected_controls:
            self.appbar.actions.append(action)

        self.page.update()

    def _action_add(self, _):
        self.add_image(self.image.src, width=self.width_image.value, height=self.height_image.value)
        self._close_dialog(self.dlg_settings_image)

    def _open_dialog(self, dlg):
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def _close_dialog(self, dlg):
        dlg.open = False
        self.page.update()

    def _save_file(self, e: ft.FilePickerResultEvent):
        if validate_file_picker_result(e.files):
            file = e.files[0]
            _, ext = splitext(file.name)

            cdn_path = os.path.join("cdn", str(uuid.uuid4()) + ext)
            shutil.copy(file.path, cdn_path)

            match self.file_picker.file_type:
                case ft.FilePickerFileType.IMAGE:
                    self.image.src = cdn_path
                    self._open_dialog(self.dlg_settings_image)
                    # self.add_image(cdn_path)

    def clear_selected_controls(func):
        def clear(self, *args, **kwargs):
            result = func(self, *args, **kwargs)

            for row in self.selected_controls:
                row.controls[0].value = False

            self.selected_controls.clear()

            return result

        return clear

    def change_mode(func):
        def call_func(self, *args, **kwargs):
            result = func(self, *args, **kwargs)

            self.change_mode_select()

            return result

        return call_func

    def after_add_text(func):
        def call_func(self, *args, **kwargs):
            result = func(self, *args, **kwargs)

            doc_text_field = self.add_text_field()
            doc_text_field.focus()

            return result

        return call_func

    def view_content(self, content: str):
        self.controls.clear()
        for line in content.split("\n"):
            if not line.startswith("{\"control\": \""):
                text_field = self._add_text_field()
                text_field.value = line
                continue

            kwargs = loads(line)
            control = kwargs.pop("control")
            match control:
                case "img":
                    self._add_image(**kwargs)

    @property
    def read_only(self):
        return self._read_only

    @read_only.setter
    def read_only(self, value):
        for row in self.controls:
            control = row.controls[1]
            match control:
                case DocumentTextField():
                    control.read_only = value

        self._read_only = value
        self.page.update()

    @property
    def value(self):
        content = ""
        for row in self.controls:
            control = row.controls[1]
            match control:
                case DocumentTextField():
                    content += control.value
                case DocumentImage():
                    kwargs = {
                        "control": "img",
                        "src": control.src,
                    }
                    if control.width:
                        kwargs["width"] = control.width
                    if control.height:
                        kwargs["height"] = control.height
                    content += dumps(kwargs)

            if row != self.controls[-1]:
                content += "\n"

        return content

    @value.setter
    def value(self, content):
        self.view_content(content)

    def add_selected_controls(self, select_control: SelectControl):
        self.selected_controls.append(select_control.control)

    @change_mode
    @clear_selected_controls
    def delete_selected_controls(self):
        for control in self.selected_controls:
            self.controls.remove(control)

        self.page.update()

    @clear_selected_controls
    def change_mode_select(self):
        if self._read_only:
            return

        self.is_change_mode = not self.is_change_mode

        for control in self.controls:
            controls = control.controls
            controls[0].visible = self.is_change_mode
            controls[1].disabled = self.is_change_mode

        for action in self.appbar.actions:
            if action in self.actions_selected_controls:
                action.visible = not action.visible
            elif action.visible:
                self.visible_actions.append(action)

        for action in self.visible_actions:
            action.visible = not action.visible

        if not self.is_change_mode:
            self.visible_actions.clear()

        self.page.update()

    @change_mode
    def add_text_field(self):
        return self._add_text_field()

    def _add_text_field(self):
        doc_text_field = DocumentTextField(self.storage)
        self.add(doc_text_field)
        return doc_text_field

    @after_add_text
    def add_image(self, src, *args, **kwargs):
        self._add_image(src, *args, **kwargs)

    def _add_image(self, src, *args, **kwargs):
        self.add(DocumentImage(src, *args, **kwargs), alignment=ft.MainAxisAlignment.CENTER)

    def add(self, control: ft.Control, *args, **kwargs):
        row = ft.Row(*args, **kwargs)

        row.controls.append(SelectControl(row, self.add_selected_controls))
        row.controls.append(control)

        index = self.controls.index(self.selected_controls[-1]) + 1 if self.selected_controls else len(self.controls)

        self.controls.insert(index, row)
        self.page.update()

        return row
