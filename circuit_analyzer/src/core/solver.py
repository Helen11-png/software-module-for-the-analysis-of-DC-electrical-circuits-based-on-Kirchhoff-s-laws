import numpy as np
from typing import List, Dict, Tuple, Any
from .components import Component, ComponentType

class CircuitSolver:
    """
    Решает электрическую цепь методом узловых потенциалов
    1. Находим все уникальные узлы в цепи
    2. Выбираем опорный узел (землю) - обычно узел 0
    3. Составляем матрицу проводимостей G и вектор токов I
    4. Решаем систему G * V = I, находим напряжения в узлах
    5. По напряжениям вычисляем токи через компоненты
    """
    def __init__(self, components: List[Component]):
        self.components = components
        self.nodes = self._extract_nodes()
        self.ground_node = 0 if 0 in self.nodes else self.nodes[0]
        self.node_to_index = {node: idx for idx, node in enumerate(self.nodes)}
        self.n_nodes = len(self.nodes)
        self.n_unknowns = self.n_nodes - 1
        self.voltages = {} # Словарь: узел -> напряжение (Вольты)
        self.currents = {} # Словарь: имя компонента -> ток (Амперы)
        self.powers = {}   # Словарь: имя компонента -> мощность (Ватты)
    def _extract_nodes(self) -> List[int]:
        nodes = set()
        for comp in self.components:
            nodes.add(comp.node1)
            nodes.add(comp.node2)
        return sorted(nodes)
    def solve(self) -> Dict[str, Any]:
        if not self.components:
            return {
                "success": False,
                "error": "Цепь не содержит компонентов",
                "voltages": {},
                "currents": {},
                "powers": {},
                "nodes": []}
        try:
            # ШАГ 1: Составляем матрицу проводимостей и вектор токов
            G,I = self._build_matrix()
            # ШАГ 2: Решаем систему линейных уравнений G * V = I
            voltages_unknown = self._solve_linear_system(G, I)
            # ШАГ 3: Восстанавливаем напряжения во всех узлах
            self._reconstruct_voltages(voltages_unknown)
            # ШАГ 4: Вычисляем токи через компоненты
            self._calculate_currents()
            # ШАГ 5: Вычисляем мощности
            self._calculate_powers()

            return {
                "success": True,
                "voltages": self.voltages,
                "currents": self.currents,
                "powers": self.powers,
                "nodes": self.nodes,
                "ground_node": self.ground_node
            }
        except np.linalg.LinAlgError as e:
            # Если матрица вырождена (не имеет решения)
            return {
                "success": False,
                "error": f"Ошибка решения: матрица вырождена. {e}",
                "voltages": {},
                "currents": {},
                "powers": {},
                "nodes": self.nodes
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Ошибка: {e}",
                "voltages": {},
                "currents": {},
                "powers": {},
                "nodes": self.nodes
            }


    def _build_matrix(self) -> Tuple[np.ndarray, np.ndarray]:
            """
        Строит матрицу проводимостей G и вектор токов I
        Метод узловых потенциалов:
            Для каждого узла i: сумма(G_ij * (V_i - V_j)) = сумма(I_источников)
            В матричной форме: G * V = I
        Возвращает:
            Tuple[np.ndarray, np.ndarray] — матрица G и вектор I
        """
            if self.n_unknowns == 0:
                return np.array([[1]]), np.array([0])

            G = np.zeros((self.n_unknowns, self.n_unknowns))
            I = np.zeros(self.n_unknowns)

            # Сначала обрабатываем ВСЕ резисторы
            for comp in self.components:
                if comp.type == ComponentType.RESISTOR:
                    idx1 = self._get_matrix_index(comp.node1)
                    idx2 = self._get_matrix_index(comp.node2)
                    conductance = 1.0 / comp.value

                    if idx1 is not None and idx2 is not None:
                        G[idx1][idx1] += conductance
                        G[idx2][idx2] += conductance
                        G[idx1][idx2] -= conductance
                        G[idx2][idx1] -= conductance
                    elif idx1 is not None and idx2 is None:
                        G[idx1][idx1] += conductance
                    elif idx1 is None and idx2 is not None:
                        G[idx2][idx2] += conductance

            # Затем обрабатываем источники напряжения
            for comp in self.components:
                if comp.type == ComponentType.VOLTAGE_SOURCE:
                    idx1 = self._get_matrix_index(comp.node1)
                    idx2 = self._get_matrix_index(comp.node2)

                    # Если один конец источника заземлен
                    if idx1 is not None and idx2 is None:
                        G[idx1][idx1] += 1e12
                        I[idx1] += 1e12 * comp.value
                    elif idx1 is None and idx2 is not None:
                        G[idx2][idx2] += 1e12
                        I[idx2] += 1e12 * comp.value
                    # Если оба конца не заземлены, пока игнорируем для простоты

            # Затем обрабатываем источники тока
            for comp in self.components:
                if comp.type == ComponentType.CURRENT_SOURCE:
                    idx1 = self._get_matrix_index(comp.node1)
                    idx2 = self._get_matrix_index(comp.node2)
                    if idx1 is not None:
                        I[idx1] += comp.value
                    if idx2 is not None:
                        I[idx2] -= comp.value

            return G, I

    def _get_matrix_index(self, node: int) -> int | None:
        if node == self.ground_node:
            return None

        full_index = self.node_to_index[node]
        ground_full_index = self.node_to_index[self.ground_node]
        if full_index < ground_full_index:
            return full_index
        else:
            return full_index - 1
    def _solve_linear_system(self, G: np.ndarray, I: np.ndarray) -> np.ndarray:
        if self.n_unknowns == 0:
            return np.array([])
        if self.n_unknowns == 1:
            return np.array([I[0] / G[0][0] if G[0][0] != 0 else 0])
        # Используем numpy.linalg.solve для решения СЛАУ
        return np.linalg.solve(G, I)

    def _reconstruct_voltages(self, voltages_unknown: np.ndarray):
        # Напряжение заземленного узла = 0
        self.voltages = {self.ground_node: 0.0}
        # Получаем список всех узлов, кроме заземленного
        unknown_nodes = [node for node in self.nodes if node != self.ground_node]
        # Заполняем напряжения для остальных узлов
        for node, voltage in zip(unknown_nodes, voltages_unknown):
            self.voltages[node] = voltage
    def _calculate_currents(self):
        for comp in self.components:
            v1 = self.voltages.get(comp.node1, 0)
            v2 = self.voltages.get(comp.node2, 0)
            delta_v = v1 - v2
            if comp.type == ComponentType.RESISTOR:
                # По закону Ома: I = U / R
                current = delta_v / comp.value
                self.currents[comp.name] = current
            elif comp.type == ComponentType.VOLTAGE_SOURCE:
                current = self._estimate_source_current(comp, delta_v)
                self.currents[comp.name] = current
            elif comp.type == ComponentType.CURRENT_SOURCE:
                self.currents[comp.name] = comp.value

    def _estimate_source_current(self, comp: Component, delta_v: float) -> float:
        """
        Вычисляет ток через источник напряжения
        По первому закону Кирхгофа: сумма токов в узле = 0
        Ток через источник равен сумме токов, выходящих из его узла
        """
        # Находим узел, к которому подключен источник (не заземленный)
        if comp.node1 == self.ground_node:
            node = comp.node2
            sign = 1  # Ток течет от земли к узлу
        elif comp.node2 == self.ground_node:
            node = comp.node1
            sign = -1  # Ток течет от узла к земле
        else:
            # Если источник не заземлен (сложный случай), возвращаем 0
            return 0.0

        # Суммируем все токи, выходящие из этого узла через другие компоненты
        total_current = 0.0

        for other in self.components:
            if other.name == comp.name:
                continue

            # Проверяем, подключен ли компонент к этому узлу
            if other.node1 == node or other.node2 == node:
                # Находим напряжение на другом конце
                other_node = other.node2 if other.node1 == node else other.node1
                v_other = self.voltages.get(other_node, 0)
                v_node = self.voltages.get(node, 0)

                if other.type == ComponentType.RESISTOR:
                    # Ток через резистор (от узла к другому узлу)
                    current = (v_node - v_other) / other.value
                    total_current += current

                elif other.type == ComponentType.CURRENT_SOURCE:
                    # Источник тока
                    if other.node1 == node:
                        total_current += other.value
                    else:
                        total_current -= other.value
        return -total_current * sign
    def _calculate_powers(self):
        #Вычисляет мощность на каждом компоненте P = U * I
        for comp in self.components:
            if comp.name in self.currents:
                v1 = self.voltages.get(comp.node1, 0)
                v2 = self.voltages.get(comp.node2, 0)
                voltage = v1 - v2
                current = self.currents[comp.name]
                # Мощность = напряжение * ток
                power = voltage * current
                self.powers[comp.name] = power