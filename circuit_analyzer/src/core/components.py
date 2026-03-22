"""Модели компонентов электрической цепи"""
from dataclasses import dataclass
from enum import Enum #Создает перечисление констант с понятными именами
from typing import Optional

class ComponentType(Enum):
    RESISTOR = "R"
    VOLTAGE_SOURCE = "V"
    CURRENT_SOURCE = "I"

@dataclass
class Component:
    name: str
    type: ComponentType
    node1: int
    node2: int
    value: float
    def __post_init__(self):
        """Валидация после создания"""
        if self.value <= 0 and self.type == ComponentType.RESISTOR:
            raise ValueError(f"Сопротивление {self.name} должно быть > 0")
        # Для источников значение может быть отрицательным (направление)
        # Отрицательное напряжение означает, что источник включен в обратном направлении

# Для удобства создадим фабричные функции (функции, которые создают объекты определенного типа)
def Resistor(name: str, node1: int, node2: int, ohms: float) -> Component:
    return Component(name, ComponentType.RESISTOR, node1, node2, ohms)

def VoltageSource(name: str, node1: int, node2: int, volts: float) -> Component:     #источник напряжения
    return Component(name, ComponentType.VOLTAGE_SOURCE, node1, node2, volts)