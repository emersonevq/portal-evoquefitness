"""
Motor de cálculo de tempo útil para SLA.

Este módulo calcula o tempo decorrido considerando:
- Horário comercial definido
- Feriados (fixos e móveis)
- Fins de semana
- Pausas (aguardando, etc)
"""

from datetime import datetime, date, timedelta, time
from typing import Optional, List
from sqlalchemy.orm import Session
from ti.models import Feriado, HorarioComercial, SlaPausa

class SlaCalculator:
    def __init__(self, db: Session):
        self.db = db
    
    def get_horario_comercial_padrao(self) -> Optional[HorarioComercial]:
        """Obtém o horário comercial padrão"""
        return self.db.query(HorarioComercial).filter(
            HorarioComercial.ativo == True,
            HorarioComercial.padrao == True
        ).first()
    
    def is_feriado(self, data: date) -> bool:
        """Verifica se uma data é feriado"""
        feriado = self.db.query(Feriado).filter(
            Feriado.data == data,
            Feriado.ativo == True
        ).first()
        return feriado is not None
    
    def is_dia_util(self, data: date, horario: HorarioComercial) -> bool:
        """Verifica se é um dia útil (desconsiderando feriados)"""
        dia_semana = data.weekday()  # 0=seg, 1=ter, ..., 6=dom
        
        dias_semana_map = {
            0: horario.segunda,
            1: horario.terca,
            2: horario.quarta,
            3: horario.quinta,
            4: horario.sexta,
            5: horario.sabado,
            6: horario.domingo,
        }
        
        return dias_semana_map.get(dia_semana, False)
    
    def calcular_tempo_util(
        self,
        inicio: datetime,
        fim: datetime,
        considera_horario_comercial: bool = True,
        considera_feriados: bool = True
    ) -> float:
        """
        Calcula o tempo útil entre dois momentos em horas.
        
        Args:
            inicio: Data/hora de início
            fim: Data/hora de término
            considera_horario_comercial: Se deve descontar fora do horário comercial
            considera_feriados: Se deve descontar feriados
        
        Returns:
            Tempo útil em horas
        """
        if inicio >= fim:
            return 0.0
        
        horario = self.get_horario_comercial_padrao()
        if not horario:
            # Se não houver configuração, assume 24h
            return (fim - inicio).total_seconds() / 3600
        
        tempo_total_minutos = 0
        data_atual = inicio.date()
        fim_date = fim.date()
        
        while data_atual <= fim_date:
            # Pula feriados se configurado
            if considera_feriados and self.is_feriado(data_atual):
                data_atual += timedelta(days=1)
                continue
            
            # Pula dias que não são úteis
            if considera_horario_comercial and not self.is_dia_util(data_atual, horario):
                data_atual += timedelta(days=1)
                continue
            
            # Calcula o tempo útil para este dia
            if not considera_horario_comercial:
                # Se não considera horário comercial, conta 24h
                if data_atual == inicio.date() == fim_date:
                    tempo_total_minutos += (fim - inicio).total_seconds() / 60
                elif data_atual == inicio.date():
                    tempo_total_minutos += (
                        (datetime.combine(data_atual, time(23, 59, 59)) - inicio).total_seconds() / 60
                    )
                elif data_atual == fim_date:
                    tempo_total_minutos += (
                        (fim - datetime.combine(data_atual, time(0, 0, 0))).total_seconds() / 60
                    )
                else:
                    tempo_total_minutos += 24 * 60
            else:
                # Calcula considerando horário comercial
                hora_inicio_dia = datetime.combine(data_atual, horario.hora_inicio)
                hora_fim_dia = datetime.combine(data_atual, horario.hora_fim)
                
                # Ajusta para a primeira entrada
                if data_atual == inicio.date():
                    hora_inicio_dia = max(hora_inicio_dia, inicio)
                
                # Ajusta para a última saída
                if data_atual == fim_date:
                    hora_fim_dia = min(hora_fim_dia, fim)
                
                # Se há pausa de almoço, desconta
                if horario.considera_almoco and horario.almoco_inicio and horario.almoco_fim:
                    almoco_inicio = datetime.combine(data_atual, horario.almoco_inicio)
                    almoco_fim = datetime.combine(data_atual, horario.almoco_fim)
                    
                    # Verifica se a pausa de almoço sobrepõe o período
                    if hora_inicio_dia < almoco_fim and hora_fim_dia > almoco_inicio:
                        tempo_antes_almoco = (
                            max(almoco_inicio, hora_inicio_dia) - hora_inicio_dia
                        ).total_seconds() / 60
                        tempo_depois_almoco = (
                            hora_fim_dia - min(almoco_fim, hora_fim_dia)
                        ).total_seconds() / 60
                        tempo_total_minutos += tempo_antes_almoco + tempo_depois_almoco
                    else:
                        tempo_total_minutos += (hora_fim_dia - hora_inicio_dia).total_seconds() / 60
                else:
                    if hora_fim_dia > hora_inicio_dia:
                        tempo_total_minutos += (hora_fim_dia - hora_inicio_dia).total_seconds() / 60
            
            data_atual += timedelta(days=1)
        
        return tempo_total_minutos / 60
    
    def calcular_tempo_com_pausas(
        self,
        inicio: datetime,
        fim: datetime,
        chamado_id: int,
        considera_horario_comercial: bool = True,
        considera_feriados: bool = True
    ) -> float:
        """
        Calcula o tempo útil descontando as pausas do chamado.
        
        Args:
            inicio: Data/hora de início
            fim: Data/hora de término
            chamado_id: ID do chamado para buscar suas pausas
            considera_horario_comercial: Se deve descontar fora do horário comercial
            considera_feriados: Se deve descontar feriados
        
        Returns:
            Tempo útil em horas
        """
        # Calcula tempo bruto
        tempo_total = self.calcular_tempo_util(
            inicio,
            fim,
            considera_horario_comercial,
            considera_feriados
        )
        
        # Busca pausas do chamado
        pausas = self.db.query(SlaPausa).filter(
            SlaPausa.chamado_id == chamado_id,
            SlaPausa.pausado_em >= inicio,
            SlaPausa.pausado_em <= fim
        ).all()
        
        # Desconta tempo de pausa
        tempo_pausa_horas = 0.0
        for pausa in pausas:
            if pausa.duracao_minutos:
                tempo_pausa_horas += pausa.duracao_minutos / 60
        
        return max(0.0, tempo_total - tempo_pausa_horas)
    
    def calcular_horas_pausas(self, chamado_id: int) -> float:
        """Calcula o total de horas em pausa para um chamado"""
        pausas = self.db.query(SlaPausa).filter(
            SlaPausa.chamado_id == chamado_id,
            SlaPausa.duracao_minutos != None
        ).all()
        
        total_minutos = sum(p.duracao_minutos or 0 for p in pausas)
        return total_minutos / 60
