import flet as ft
from src.views.main_view import MainView

def main(page: ft.Page):
    page.title = "Анализ электрических цепей"
    page.window_width = 950
    page.window_height = 750
    page.window_min_width = 800
    page.window_min_height = 600
    page.theme_mode = ft.ThemeMode.LIGHT
    MainView(page)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)

