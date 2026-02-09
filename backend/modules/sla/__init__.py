"""
Módulo SLA (Service Level Agreement)
Sistema completo de gerenciamento de SLA para chamados
"""
from .routes import router
from .calculator import CalculadorSLA
from .metrics import ServicoMetricasSLA
from .models import (
    ConfiguracaoSLA,
    HorarioComercial,
    Feriado,
    PausaSLA,
    InfoSLAChamado,
    Chamado
)
from .holidays import (
    calcular_feriados_fixos,
    calcular_feriados_moveis,
    gerar_todos_feriados,
    gerar_feriados_intervalo
)

__all__ = [
    "router",
    "CalculadorSLA",
    "ServicoMetricasSLA",
    "ConfiguracaoSLA",
    "HorarioComercial",
    "Feriado",
    "PausaSLA",
    "InfoSLAChamado",
    "Chamado",
    "calcular_feriados_fixos",
    "calcular_feriados_moveis",
    "gerar_todos_feriados",
    "gerar_feriados_intervalo"
]

__version__ = "2.0.0"
__description__ = "Sistema avançado de SLA com suporte a feriados móveis, pausas automáticas por status e cálculo preciso de horas úteis"
