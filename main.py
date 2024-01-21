import flet as ft

from controls import MainView, CreateRecordView, SelectRecordView, SettingsView
from diary import exists_record, get_date
from datetime import datetime
from storage import init_storage


def main(page: ft.Page):
    def route_change(e):
        page.views.clear()
        page.views.append(
            MainView(open_dialog_error, page)
            # ft.View()
        )

        troute = ft.TemplateRoute(page.route)

        if troute.route == "/create-record":
            if exists_record(get_date(datetime.now())):
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


ft.app(target=main)
