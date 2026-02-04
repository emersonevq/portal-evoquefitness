"""
Calculadora de SLA com suporte a:
- Horário comercial configurável
- Dias úteis (seg-sex)
- Feriados
- Pausas
"""

from datetime import datetime, timedelta, date, time
from typing import List, Tuple, Optional, Dict, Set

from .config import settings
from .exceptions import HorarioInvalidoError


class SlaCalculator:
    """Calculadora de horas úteis para SLA"""
    
    def __init__(
        self,
        feriados: List[date] = None,
        hora_inicio: int = None,
        hora_fim: int = None,
        risco_percentual: int = None
    ):
        # Configurações
        self.hora_inicio = hora_inicio or settings.BUSINESS_HOUR_START
        self.hora_fim = hora_fim or settings.BUSINESS_HOUR_END
        self.risco_percentual = risco_percentual or settings.SLA_RISCO_PERCENTUAL
        
        # Validações
        if self.hora_inicio >= self.hora_fim:
            raise HorarioInvalidoError(self.hora_inicio, self.hora_fim)
        
        if not (0 <= self.hora_inicio <= 23) or not (0 <= self.hora_fim <= 23):
            raise ValueError("Horários devem estar entre 0 e 23")
        
        # Feriados
        self.feriados: Set[date] = set()
        if feriados:
            for f in feriados:
                if isinstance(f, datetime):
                    self.feriados.add(f.date())
                else:
                    self.feriados.add(f)
        
        # Dias úteis (seg-sex)
        self.dias_uteis: Set[int] = set(settings.BUSINESS_DAYS)
        self.horas_por_dia = self.hora_fim - self.hora_inicio
    
    def adicionar_feriados(self, feriados: List[date]) -> None:
        """Adiciona feriados à lista"""
        for f in feriados:
            if isinstance(f, datetime):
                f = f.date()
            self.feriados.add(f)
    
    def is_dia_util(self, data: date) -> bool:
        """Verifica se é dia útil"""
        if isinstance(data, datetime):
            data = data.date()
        return data.weekday() in self.dias_uteis and data not in self.feriados
    
    def is_horario_comercial(self, dt: datetime) -> bool:
        """Verifica se está dentro do horário comercial"""
        if not self.is_dia_util(dt.date()):
            return False
        return self.hora_inicio <= dt.hour < self.hora_fim
    
    def ajustar_para_horario_comercial(self, dt: datetime) -> datetime:
        """Ajusta para o próximo horário comercial válido"""
        if dt is None:
            dt = datetime.now()
        
        dt = dt.replace(second=0, microsecond=0)
        max_data = dt + timedelta(days=365)
        
        while not self.is_dia_util(dt.date()) and dt < max_data:
            dt = datetime.combine(dt.date() + timedelta(days=1), time(self.hora_inicio))
        
        if dt.hour < self.hora_inicio:
            dt = dt.replace(hour=self.hora_inicio, minute=0)
        elif dt.hour >= self.hora_fim:
            dt = datetime.combine(dt.date() + timedelta(days=1), time(self.hora_inicio))
            while not self.is_dia_util(dt.date()) and dt < max_data:
                dt = datetime.combine(dt.date() + timedelta(days=1), time(self.hora_inicio))
        
        return dt
    
    def calcular_horas_uteis(self, inicio: datetime, fim: datetime) -> float:
        """Calcula horas úteis entre duas datas"""
        if inicio is None or fim is None:
            return 0.0
        
        if inicio >= fim:
            return 0.0
        
        inicio = self.ajustar_para_horario_comercial(inicio)
        
        if inicio >= fim:
            return 0.0
        
        horas_totais = 0.0
        atual = inicio
        max_iteracoes = 365
        iteracao = 0
        
        while atual < fim and iteracao < max_iteracoes:
            iteracao += 1
            
            if not self.is_dia_util(atual.date()):
                atual = datetime.combine(
                    atual.date() + timedelta(days=1),
                    time(self.hora_inicio)
                )
                continue
            
            inicio_exp = atual.replace(hour=self.hora_inicio, minute=0, second=0, microsecond=0)
            fim_exp = atual.replace(hour=self.hora_fim, minute=0, second=0, microsecond=0)
            
            hora_inicio_calc = max(atual, inicio_exp)
            hora_fim_calc = min(fim, fim_exp)
            
            if hora_inicio_calc < hora_fim_calc:
                diff = (hora_fim_calc - hora_inicio_calc).total_seconds() / 3600
                horas_totais += diff
            
            atual = datetime.combine(
                atual.date() + timedelta(days=1),
                time(self.hora_inicio)
            )
        
        return round(horas_totais, 2)
    
    def calcular_horas_uteis_com_pausas(
        self,
        inicio: datetime,
        fim: datetime,
        pausas: List[Dict] = None
    ) -> Tuple[float, float]:
        """
        Calcula horas úteis descontando pausas.
        
        Returns:
            Tuple[horas_trabalhadas, horas_pausadas]
        """
        if inicio is None:
            return 0.0, 0.0
        
        if fim is None:
            fim = datetime.now()
        
        horas_totais = self.calcular_horas_uteis(inicio, fim)
        horas_pausadas = 0.0
        
        if pausas:
            for pausa in pausas:
                pausado_em = pausa.get('pausado_em')
                retomado_em = pausa.get('retomado_em')
                
                if retomado_em is None:
                    retomado_em = datetime.now()
                
                if pausado_em is None:
                    continue
                
                if pausado_em < fim:
                    pausa_inicio = max(pausado_em, inicio)
                    pausa_fim = min(retomado_em, fim)
                    
                    if pausa_inicio < pausa_fim:
                        horas_pausa = self.calcular_horas_uteis(pausa_inicio, pausa_fim)
                        horas_pausadas += horas_pausa
        
        horas_trabalhadas = max(0, horas_totais - horas_pausadas)
        
        return round(horas_trabalhadas, 2), round(horas_pausadas, 2)
    
    def calcular_prazo(self, inicio: datetime, horas: float) -> datetime:
        """Calcula data/hora limite dado horas úteis"""
        if inicio is None:
            inicio = datetime.now()
        
        if horas <= 0:
            return inicio
        
        inicio = self.ajustar_para_horario_comercial(inicio)
        horas_restantes = horas
        atual = inicio
        max_iteracoes = 365
        iteracao = 0
        
        while horas_restantes > 0 and iteracao < max_iteracoes:
            iteracao += 1
            
            if not self.is_dia_util(atual.date()):
                atual = datetime.combine(
                    atual.date() + timedelta(days=1),
                    time(self.hora_inicio)
                )
                continue
            
            fim_exp = atual.replace(hour=self.hora_fim, minute=0, second=0, microsecond=0)
            horas_disponiveis = (fim_exp - atual).total_seconds() / 3600
            
            if horas_restantes <= horas_disponiveis:
                return atual + timedelta(hours=horas_restantes)
            
            horas_restantes -= horas_disponiveis
            atual = datetime.combine(
                atual.date() + timedelta(days=1),
                time(self.hora_inicio)
            )
            
            while not self.is_dia_util(atual.date()) and iteracao < max_iteracoes:
                iteracao += 1
                atual = datetime.combine(
                    atual.date() + timedelta(days=1),
                    time(self.hora_inicio)
                )
        
        return atual
    
    def calcular_status_sla(
        self,
        inicio: datetime,
        tempo_limite_horas: float,
        pausas: List[Dict] = None,
        fim: datetime = None
    ) -> Dict:
        """Calcula status completo do SLA"""
        if fim is None:
            fim = datetime.now()
        
        horas_decorridas, horas_pausadas = self.calcular_horas_uteis_com_pausas(
            inicio, fim, pausas
        )
        
        if tempo_limite_horas > 0:
            percentual = (horas_decorridas / tempo_limite_horas) * 100
        else:
            percentual = 0
        
        tempo_restante = max(0, tempo_limite_horas - horas_decorridas)
        em_risco = self.risco_percentual <= percentual < 100
        vencido = percentual >= 100
        prazo_limite = self.calcular_prazo(inicio, tempo_limite_horas)
        
        return {
            "tempo_decorrido_horas": horas_decorridas,
            "tempo_pausado_horas": horas_pausadas,
            "tempo_restante_horas": round(tempo_restante, 2),
            "tempo_limite_horas": tempo_limite_horas,
            "percentual_consumido": round(percentual, 2),
            "em_risco": em_risco,
            "vencido": vencido,
            "prazo_limite": prazo_limite
        }
