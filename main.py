from views import *
from diary import exists_record, get_date
from datetime import datetime
from storage import init_storage


if not exists("records"):
    os.mkdir("records")
if not exists("cdn"):
    os.mkdir("cdn")


def main(page: ft.Page):
    def route_change(e):
        print(page.route)
        page.views.clear()
        page.views.append(
            MainView(open_dialog_error, page)
        )

        troute = ft.TemplateRoute(page.route)

        if troute.route == "/create-record":
            if exists_record(get_date(datetime.now())):
                page.go("/")
                open_dialog_error("Вы сегодня сделали запись! Для ее редактирования вам нужно нажать на \"Выбрать "
                                  "запись\" и выбрать соответствующую дату")
            else:
                page.views.append(CreateRecordView(open_dialog_error, page))
        elif troute.match("/records/:date"):
            page.views.append(SelectRecordView(open_dialog_error, page, troute.date))
        elif troute.route == "/settings":
            page.views.append(SettingsView(open_dialog_error, page))

        page.update()

    def open_dialog_error(error: str):
        dlg_error.open = True
        dlg_error.content = ft.Text(error)
        page.dialog = dlg_error
        page.update()

    def view_pop(e):
        print("Pop")
        page.views.pop()
        page.go(page.views[-1].route)

    dlg_error = ft.AlertDialog(title=ft.Text("Ошибка"))
    storage = init_storage(page)

    page.title = "Личный дневник"
    page.theme_mode = storage.theme_mode

    # page.window_width = 400
    # page.window_height = 500
    page.padding = 0

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go("/")

    if storage.encryption_enable and not storage.crypto_key:
        def select_crypt_key(e: ft.FilePickerResultEvent):
            if validate_file_picker_result(e.files):
                storage.crypto_key = get_key(e.files[0].path)

        file_crypt_key_picker = ft.FilePicker(on_result=select_crypt_key)
        page.overlay.append(file_crypt_key_picker)
        page.update()
        file_crypt_key_picker.pick_files("Ключ шифрования")


ft.app(target=main)
