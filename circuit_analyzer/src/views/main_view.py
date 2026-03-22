import flet as ft
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from ..core.components import Resistor, VoltageSource, ComponentType
from ..core.solver import CircuitSolver
from ..visualization.graphs import CircuitPlotter


class MainView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Анализ электрических цепей"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.components = []
        self.plotter = CircuitPlotter()
        self.last_result = None
        self.setup_ui()
    def setup_ui(self):
        """Создает интерфейс с прокруткой"""
        title = ft.Text(
            "Анализ электрических цепей постоянного тока",
            size=30,
            weight=ft.FontWeight.BOLD
        )
        self.component_input = ft.TextField(
            label="Добавить компонент",
            hint_text="Пример: R1, R, 1, 2, 100",
            width=400
        )
        add_button = ft.ElevatedButton(
            "Добавить",
            on_click=self.add_component
        )
        self.components_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Название")),
                ft.DataColumn(ft.Text("Тип")),
                ft.DataColumn(ft.Text("Узел 1")),
                ft.DataColumn(ft.Text("Узел 2")),
                ft.DataColumn(ft.Text("Значение")),
            ],
            rows=[],
            width=700,
        )
        table_container = ft.Container(
            content=self.components_table,
            height=250,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=5,
            padding=5,
        )
        self.example_dropdown = ft.Dropdown(
            label="Выберите пример",
            width=300,
            options=[
                ft.dropdown.Option("voltage_divider", "Делитель напряжения (12В, 1кΩ, 2кΩ)"),
                ft.dropdown.Option("three_resistors", "Три резистора последовательно"),
                ft.dropdown.Option("parallel_resistors", "Параллельные резисторы"),
                ft.dropdown.Option("wheatstone_bridge", "Мост Уитстона"),
            ],
            value="voltage_divider"
        )
        load_example_button = ft.ElevatedButton(
            "📂 Загрузить пример",
            on_click=self.load_example,
            bgcolor=ft.Colors.GREEN_700,
            color="white"
        )
        examples_row = ft.Row(
            [self.example_dropdown, load_example_button],
            alignment=ft.MainAxisAlignment.START,
            spacing=10
        )
        solve_button = ft.ElevatedButton(
            "Рассчитать цепь",
            on_click=self.solve_circuit,
            color="white",
            bgcolor="blue"
        )
        self.voltages_plot_button = ft.ElevatedButton(
            "График напряжений",
            on_click=self.show_voltages_plot,
            disabled=True
        )
        self.currents_plot_button = ft.ElevatedButton(
            "График токов",
            on_click=self.show_currents_plot,
            disabled=True
        )
        self.circuit_plot_button = ft.ElevatedButton(
            "Схема цепи",
            on_click=self.show_circuit_plot,
            disabled=True
        )
        self.results_text = ft.Text(
            "Результаты появятся здесь",
            size=14,
            selectable=True
        )
        self.image_container = ft.Container(
            content=ft.Text("Нажмите кнопку для построения графика"),
            width=800,
            height=500,
            border=ft.border.all(1, ft.Colors.GREY),
            border_radius=10,
            padding=10
        )
        self.page.add(
            ft.ListView(
                controls=[
                    title,
                    ft.Divider(),
                    ft.Row([self.component_input, add_button]),
                    ft.Text("Список компонентов:", size=18, weight=ft.FontWeight.BOLD),
                    table_container,
                    ft.Text("Быстрый старт:", size=18, weight=ft.FontWeight.BOLD),  # ← Добавляем заголовок
                    examples_row,  # ← ДОБАВЛЯЕМ ряд с примерами
                    solve_button,
                    ft.Row([self.voltages_plot_button,
                            self.currents_plot_button,
                            self.circuit_plot_button]),
                    ft.Text("Результаты:", size=18, weight=ft.FontWeight.BOLD),
                    self.results_text,
                    ft.Text("Визуализация:", size=18, weight=ft.FontWeight.BOLD),
                    self.image_container,
                ],
                spacing=15,
                height=600,
                expand=True,
            )
        )

    def add_component(self, e):
        """Добавляет компонент из текстового поля"""
        text = self.component_input.value
        if not text:
            return
        try:
            parts = text.replace(" ", "").split(",")
            if len(parts) != 5:
                raise ValueError("Нужно 5 параметров")
            name = parts[0]
            comp_type = parts[1].upper()
            node1 = int(parts[2])
            node2 = int(parts[3])
            value = float(parts[4])

            if comp_type == "R":
                comp = Resistor(name, node1, node2, value)
            elif comp_type == "V":
                comp = VoltageSource(name, node1, node2, value)
            else:
                raise ValueError(f"Неизвестный тип: {comp_type}")

            self.components.append(comp)
            self.update_components_table()
            self.component_input.value = ""
            self.page.update()

        except Exception as ex:
            self.results_text.value = f"Ошибка: {ex}"
            self.page.update()

    def update_components_table(self):
        """Обновляет таблицу компонентов"""
        rows = []
        for comp in self.components:
            rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(comp.name)),
                    ft.DataCell(ft.Text(comp.type.value)),
                    ft.DataCell(ft.Text(str(comp.node1))),
                    ft.DataCell(ft.Text(str(comp.node2))),
                    ft.DataCell(ft.Text(str(comp.value))),
                ])
            )
        self.components_table.rows = rows
        self.page.update()

    def solve_circuit(self, e):
        """Запускает расчет цепи"""
        if not self.components:
            self.results_text.value = "Добавьте хотя бы один компонент"
            self.page.update()
            return

        solver = CircuitSolver(self.components)
        self.last_result = solver.solve()

        if self.last_result["success"]:
            output = "=" * 50 + "\n"
            output += "РЕЗУЛЬТАТЫ РАСЧЕТА ЦЕПИ\n"
            output += "=" * 50 + "\n\n"
            output += "НАПРЯЖЕНИЯ В УЗЛАХ:\n"
            output += "-" * 30 + "\n"
            for node, voltage in sorted(self.last_result["voltages"].items()):
                output += f"Узел {node}: {abs(voltage):.3f} В\n"
            output += "\n"
            output += "ТОКИ В КОМПОНЕНТАХ:\n"
            output += "-" * 30 + "\n"
            for name, current in self.last_result["currents"].items():
                abs_current = abs(current)
                if abs_current < 0.001:
                    output += f"{name}: {abs_current * 1000:.2f} мА\n"
                else:
                    output += f"{name}: {abs_current:.3f} А\n"
            output += "\n"
            output += "МОЩНОСТИ:\n"
            output += "-" * 30 + "\n"
            for name, power in self.last_result["powers"].items():
                abs_power = abs(power)
                if abs_power < 1:
                    output += f"{name}: {abs_power * 1000:.2f} мВт\n"
                else:
                    output += f"{name}: {abs_power:.3f} Вт\n"

            output += "\n" + "-" * 30 + "\n"
            output += "ℹ️ Напряжения и токи показаны по модулю.\n"
            output += "   Направления токов определяются по правилам Кирхгофа."

            self.results_text.value = output

            # Активируем кнопки графиков
            self.voltages_plot_button.disabled = False
            self.currents_plot_button.disabled = False
            self.circuit_plot_button.disabled = False

        else:
            self.results_text.value = f"❌ ОШИБКА: {self.last_result.get('error', 'Неизвестная ошибка')}"
            self.voltages_plot_button.disabled = True
            self.currents_plot_button.disabled = True
            self.circuit_plot_button.disabled = True

        self.page.update()

    def show_voltages_plot(self, e):
        """Показывает график напряжений"""
        if not self.last_result or not self.last_result["success"]:
            return

        try:
            fig = self.plotter.plot_voltages(self.last_result["voltages"])
            self._display_figure(fig)
        except Exception as ex:
            self.results_text.value = f"Ошибка при построении графика: {ex}"
            self.page.update()

    def show_currents_plot(self, e):
        """Показывает график токов"""
        if not self.last_result or not self.last_result["success"]:
            return

        try:
            fig = self.plotter.plot_currents(self.last_result["currents"])
            self._display_figure(fig)
        except Exception as ex:
            self.results_text.value = f"Ошибка при построении графика: {ex}"
            self.page.update()

    def show_circuit_plot(self, e):
        """Показывает схему цепи"""
        if not self.last_result or not self.last_result["success"]:
            return

        try:
            fig = self.plotter.draw_circuit(
                self.components,
                self.last_result["voltages"],
                self.last_result["currents"]
            )
            self._display_figure(fig)
        except Exception as ex:
            self.results_text.value = f"Ошибка при построении схемы: {ex}"
            self.page.update()

    def load_example(self, e):
        """Загружает пример цепи из JSON файла"""
        import json
        import os

        # Получаем название выбранного примера
        example_name = self.example_dropdown.value
        if not example_name:
            return

        # Формируем путь к файлу
        example_path = os.path.join("examples", f"{example_name}.json")

        if not os.path.exists(example_path):
            self.results_text.value = f"❌ Файл примера не найден: {example_path}"
            self.page.update()
            return

        try:
            with open(example_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Очищаем текущие компоненты
            self.components = []

            # Добавляем компоненты из примера
            for comp_data in data["components"]:
                if comp_data["type"] == "R":
                    comp = Resistor(
                        comp_data["name"],
                        comp_data["node1"],
                        comp_data["node2"],
                        comp_data["value"]
                    )
                elif comp_data["type"] == "V":
                    comp = VoltageSource(
                        comp_data["name"],
                        comp_data["node1"],
                        comp_data["node2"],
                        comp_data["value"]
                    )
                else:
                    continue

                self.components.append(comp)
            self.update_components_table()

            info_text = f"Загружен пример: {data.get('name', example_name)}\n"
            info_text += f"{data.get('description', 'Описание отсутствует')}\n"
            info_text += f"Добавлено компонентов: {len(self.components)}"
            self.results_text.value = info_text
            self.image_container.content = ft.Text("Нажмите кнопку для построения графика")
            self.voltages_plot_button.disabled = True
            self.currents_plot_button.disabled = True
            self.circuit_plot_button.disabled = True
            self.page.update()

        except Exception as ex:
            self.results_text.value = f"Ошибка загрузки примера: {ex}"
            self.page.update()
    def _display_figure(self, fig):
        """Отображает matplotlib фигуру в Flet"""
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_data = base64.b64encode(buf.getvalue()).decode()
        # ВАРИАНТ 1: Используем src (без _base64)
        img = ft.Image(
            src=f"data:image/png;base64,{img_data}",  # Добавляем data:image/png;base64,
            width=780,
            height=480,
        )
        # Обновляем контейнер
        self.image_container.content = img
        self.page.update()
        # Закрываем фигуру
        plt.close(fig)