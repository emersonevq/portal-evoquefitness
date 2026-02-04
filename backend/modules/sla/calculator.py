"""Cálculos de SLA em horas úteis"""

from datetime import datetime, timedelta, time
from typing import Tuple, List
import logging

from .config import settings

logger = logging.getLogger("sla.calculator")


class SlaCalculator:
    """Calculador de SLA com suporte a horas úteis"""
    
    def __init__(self, feriados: List[datetime] = None):
        """
        Inicializa calculador
        
        Args:
            feriados: Lista de datas que são feriados
        """
        self.feriados = set()
        if feriados:
            # Normalizar feriados para apenas data (sem hora)
            for data in feriados:
                if isinstance(data, datetime):
                    self.feriados.add(data.date())
                else:
                    self.feriados.add(data)
        
        self.hour_start = settings.BUSINESS_HOUR_START
        self.hour_end = settings.BUSINESS_HOUR_END
        self.business_days = settings.BUSINESS_DAYS
    
    def _eh_dia_util(self, data: datetime) -> bool:
        """Verifica se é um dia útil (não é feriado e não é fim de semana)"""
        # Fim de semana
        if data.weekday() not in self.business_days:
            return False
        
        # Feriado
        if data.date() in self.feriados:
            return False
        
        return True
    
    def _eh_horario_comercial(self, dt: datetime) -> bool:
        """Verifica se está dentro do horário comercial"""
        return self.hour_start <= dt.hour < self.hour_end
    
    def _segundos_dia_util(self, data: datetime) -> int:
        """Retorna segundos úteis em um dia específico"""
        if not self._eh_dia_util(data):
            return 0
        
        # Um dia de 8h a 18h = 10 horas = 36000 segundos
        return (self.hour_end - self.hour_start) * 3600
    
    def calcular_horas_uteis(self, data_inicio: datetime, data_fim: datetime) -> float:
        """
        Calcula horas úteis entre duas datas
        
        Considera:
        - Apenas dias úteis (seg-sex)
        - Apenas horário comercial (8h-18h)
        - Exclui feriados
        
        Args:
            data_inicio: Início do período
            data_fim: Fim do período
        
        Returns:
            Horas úteis (float)
        """
        if data_fim <= data_inicio:
            return 0.0
        
        segundos_totais = 0
        
        # Se está no mesmo dia
        if data_inicio.date() == data_fim.date():
            if not self._eh_dia_util(data_inicio):
                return 0.0
            
            # Normalizar horários para dentro do período comercial
            hora_inicio = max(data_inicio.time(), time(self.hour_start, 0))
            hora_fim = min(data_fim.time(), time(self.hour_end, 0))
            
            if hora_fim <= hora_inicio:
                return 0.0
            
            # Converter para segundos
            dt_inicio = datetime.combine(data_inicio.date(), hora_inicio)
            dt_fim = datetime.combine(data_fim.date(), hora_fim)
            segundos_totais = int((dt_fim - dt_inicio).total_seconds())
        else:
            # Primeiro dia (partial)
            if self._eh_dia_util(data_inicio):
                hora_inicio = max(data_inicio.time(), time(self.hour_start, 0))
                hora_fim = time(self.hour_end, 0)
                
                dt_inicio = datetime.combine(data_inicio.date(), hora_inicio)
                dt_fim = datetime.combine(data_inicio.date(), hora_fim)
                segundos_totais += int((dt_fim - dt_inicio).total_seconds())
            
            # Dias intermediários (full)
            data_atual = data_inicio.date() + timedelta(days=1)
            while data_atual < data_fim.date():
                segundos_totais += self._segundos_dia_util(
                    datetime.combine(data_atual, time(self.hour_start))
                )
                data_atual += timedelta(days=1)
            
            # Último dia (partial)
            if self._eh_dia_util(data_fim):
                hora_inicio = time(self.hour_start, 0)
                hora_fim = min(data_fim.time(), time(self.hour_end, 0))
                
                dt_inicio = datetime.combine(data_fim.date(), hora_inicio)
                dt_fim = datetime.combine(data_fim.date(), hora_fim)
                segundos_totais += int((dt_fim - dt_inicio).total_seconds())
        
        # Converter para horas
        horas = segundos_totais / 3600
        return round(horas, 2)
    
    def calcular_horas_uteis_com_pausas(
        self,
        data_inicio: datetime,
        data_fim: datetime,
        pausas: List[Tuple[datetime, datetime]] = None
    ) -> Tuple[float, float]:
        """
        Calcula horas úteis descontando pausas
        
        Args:
            data_inicio: Início do período
            data_fim: Fim do período
            pausas: Lista de tuplas (pausado_em, retomado_em)
        
        Returns:
            Tupla (horas_trabalhadas, horas_pausadas)
        """
        if not pausas:
            horas_trabalhadas = self.calcular_horas_uteis(data_inicio, data_fim)
            return (horas_trabalhadas, 0.0)
        
        # Calcular horas totais
        horas_totais = self.calcular_horas_uteis(data_inicio, data_fim)
        
        # Calcular horas de pausa
        horas_pausadas = 0.0
        for pausado_em, retomado_em in pausas:
            if retomado_em:  # Só conta pausas que foram retomadas
                horas_pausadas += self.calcular_horas_uteis(pausado_em, retomado_em)
        
        horas_trabalhadas = max(0, horas_totais - horas_pausadas)
        return (round(horas_trabalhadas, 2), round(horas_pausadas, 2))
    
    def calcular_percentual_sla(
        self,
        horas_decorridas: float,
        horas_limite: float
    ) -> float:
        """
        Calcula percentual de SLA consumido
        
        Args:
            horas_decorridas: Horas decorridas
            horas_limite: Limite de horas do SLA
        
        Returns:
            Percentual (0-100)
        """
        if horas_limite <= 0:
            return 100.0
        
        percentual = (horas_decorridas / horas_limite) * 100
        return round(min(percentual, 100.0), 2)
    
    def eh_em_risco(
        self,
        horas_decorridas: float,
        horas_limite: float,
        limiar_risco: float = 80.0
    ) -> bool:
        """
        Verifica se está em risco (80% do SLA consumido)
        
        Args:
            horas_decorridas: Horas decorridas
            horas_limite: Limite de horas
            limiar_risco: Percentual limiar (padrão 80%)
        
        Returns:
            True se em risco
        """
        percentual = self.calcular_percentual_sla(horas_decorridas, horas_limite)
        return limiar_risco <= percentual < 100.0
    
    def eh_vencido(
        self,
        horas_decorridas: float,
        horas_limite: float
    ) -> bool:
        """
        Verifica se está vencido (100% do SLA consumido)
        
        Args:
            horas_decorridas: Horas decorridas
            horas_limite: Limite de horas
        
        Returns:
            True se vencido
        """
        return horas_decorridas >= horas_limite
