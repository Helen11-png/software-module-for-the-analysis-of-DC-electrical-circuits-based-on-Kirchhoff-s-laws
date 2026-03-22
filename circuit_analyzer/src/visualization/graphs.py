"""
Модуль визуализации электрических цепей
Рисует схему цепи и графики напряжений/токов
"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from typing import Dict, List, Any
import matplotlib
matplotlib.use('Agg')

class CircuitPlotter:
    """Класс для визуализации цепей и результатов"""
    def __init__(self):
        self.fig = None
        self.ax = None
    def draw_circuit(self, components: List[Any], voltages: Dict[int, float],
                     currents: Dict[str, float], title: str = "Схема цепи"):
        """
        Рисует граф электрической цепи

        Аргументы:
            components: список компонентов
            voltages: напряжения в узлах
            currents: токи через компоненты
            title: заголовок графика
        """
        G = nx.Graph()
        nodes = set()
        for comp in components:
            nodes.add(comp.node1)
            nodes.add(comp.node2)
        for node in nodes:
            G.add_node(node)
        edge_labels = {}
        for comp in components:
            if comp.type.value == "R":
                color = 'blue'
                style = 'solid'
                label = f"{comp.name}\n{comp.value}Ω"
            elif comp.type.value == "V":
                color = 'red'
                style = 'solid'
                label = f"{comp.name}\n{comp.value}V"
            else:
                color = 'green'
                style = 'dashed'
                label = f"{comp.name}\n{comp.value}A"
            G.add_edge(comp.node1, comp.node2, color=color, style=style)
            edge_labels[(comp.node1, comp.node2)] = label
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        pos = nx.spring_layout(G, k=2, iterations=50)
        nx.draw_networkx_nodes(G, pos, node_size=500, node_color='lightblue',
                               node_shape='o', ax=self.ax)
        edges = G.edges()
        colors = [G[u][v]['color'] for u, v in edges]
        styles = [G[u][v]['style'] for u, v in edges]
        for (u, v), color, style in zip(edges, colors, styles):
            nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], edge_color=color,
                                   style=style, width=2, ax=self.ax)
        node_labels = {}
        for node in nodes:
            voltage = voltages.get(node, 0)
            node_labels[node] = f"{node}\n{voltage:.1f}V"
        nx.draw_networkx_labels(G, pos, node_labels, font_size=10, ax=self.ax)
        nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8, ax=self.ax)
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.axis('off')
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='blue', edgecolor='blue', label='Резистор'),
            Patch(facecolor='red', edgecolor='red', label='Источник напряжения'),
            Patch(facecolor='green', edgecolor='green', label='Источник тока')
        ]
        self.ax.legend(handles=legend_elements, loc='upper right')
        plt.tight_layout()
        return self.fig
    def plot_voltages(self, voltages: Dict[int, float], title: str = "Напряжения в узлах"):
        """
        Строит столбчатую диаграмму напряжений
        """
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        nodes = sorted(voltages.keys())
        voltage_values = [voltages[node] for node in nodes]
        colors = ['red' if v >= 0 else 'blue' for v in voltage_values]
        bars = self.ax.bar(nodes, voltage_values, color=colors, alpha=0.7)
        for bar, v in zip(bars, voltage_values):
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                         f'{v:.2f}V', ha='center', va='bottom')

        self.ax.set_xlabel('Номер узла', fontsize=12)
        self.ax.set_ylabel('Напряжение (В)', fontsize=12)
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        self.ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        plt.tight_layout()
        return self.fig

    def plot_currents(self, currents: Dict[str, float], title: str = "Токи в компонентах"):
        """
        Строит горизонтальную столбчатую диаграмму токов
        """
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        sorted_items = sorted(currents.items(), key=lambda x: abs(x[1]), reverse=True)
        names = [item[0] for item in sorted_items]
        current_values = [abs(item[1]) for item in sorted_items]
        colors = []
        for name in names:
            if name.startswith('R'):
                colors.append('blue')
            elif name.startswith('V'):
                colors.append('red')
            else:
                colors.append('green')
        bars = self.ax.barh(names, current_values, color=colors, alpha=0.7)
        for bar, val in zip(bars, current_values):
            if val >= 0.001:
                text = f'{val * 1000:.1f} мА' if val < 1 else f'{val:.2f} А'
            else:
                text = f'{val * 1e6:.0f} мкА'
            self.ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height() / 2,
                         text, ha='left', va='center')

        self.ax.set_xlabel('Ток (А)', fontsize=12)
        self.ax.set_ylabel('Компонент', fontsize=12)
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3, axis='x')

        plt.tight_layout()
        return self.fig

    def plot_power_balance(self, voltages: Dict[int, float], currents: Dict[str, float],
                           components: List[Any], title: str = "Баланс мощностей"):
        """
        Строит диаграмму баланса мощностей
        """
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        source_power = 0
        resistor_power = 0
        for comp in components:
            if comp.name in currents:
                v1 = voltages.get(comp.node1, 0)
                v2 = voltages.get(comp.node2, 0)
                voltage = abs(v1 - v2)
                current = abs(currents[comp.name])
                power = voltage * current

                if comp.type.value == "V":
                    source_power += power
                else:
                    resistor_power += power
        labels = ['Источники', 'Резисторы']
        sizes = [source_power, resistor_power]
        colors = ['red', 'blue']
        explode = (0.05, 0)
        balance_error = abs(source_power - resistor_power)

        wedges, texts, autotexts = self.ax.pie(sizes, explode=explode, labels=labels,
                                               colors=colors, autopct='%1.1f%%',
                                               shadow=True, startangle=90)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        balance_text = f"Мощность источника: {source_power * 1000:.1f} мВт\n"
        balance_text += f"Мощность резисторов: {resistor_power * 1000:.1f} мВт\n"
        balance_text += f"Погрешность: {balance_error * 1000:.2f} мкВт"

        self.ax.text(1.2, -0.2, balance_text, transform=self.ax.transAxes,
                     fontsize=10, verticalalignment='top')

        plt.tight_layout()
        return self.fig

    def plot_voltage_distribution(self, voltages: Dict[int, float],
                                  title: str = "Распределение напряжений"):
        """
        Строит график распределения напряжений вдоль цепи
        """
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        nodes = sorted(voltages.keys())
        voltage_values = [voltages[node] for node in nodes]
        x = np.array(nodes)
        y = np.array(voltage_values)
        self.ax.plot(x, y, 'o-', color='blue', linewidth=2, markersize=8, label='Напряжение')
        self.ax.fill_between(x, y, alpha=0.3)
        for node, voltage in zip(nodes, voltage_values):
            self.ax.annotate(f'{voltage:.1f}V', (node, voltage),
                             textcoords="offset points", xytext=(0, 10), ha='center')

        self.ax.set_xlabel('Номер узла', fontsize=12)
        self.ax.set_ylabel('Напряжение (В)', fontsize=12)
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()

        plt.tight_layout()
        return self.fig