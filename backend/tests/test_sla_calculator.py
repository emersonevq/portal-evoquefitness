"""
Testes para SlaCalculator - Cálculos de tempo útil e pausas.

Valida:
- Cálculo de tempo útil respeitando horário comercial
- Cálculo de tempo com pausas descontadas
- Cálculo de horas em pausas
- Horários comerciais e feriados
"""

import pytest
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from ti.models import ConfiguracesSla, HorarioComercial, Feriado, SlaPausa, Chamado
from ti.modules.sla.services import SlaCalculator


class TestSlaCalculator:
    """Testes da classe SlaCalculator"""
    
    @pytest.fixture
    def calc(self, db: Session) -> SlaCalculator:
        """Cria instância do calculator"""
        return SlaCalculator(db)
    
    @pytest.fixture
    def setup_data(self, db: Session) -> None:
        """Configura dados para os testes"""
        # Criar horário comercial (08h-18h, seg-sex)
        horario = HorarioComercial(
            nome="Comercial",
            hora_inicio="08:00:00",
            hora_fim="18:00:00",
            segunda=True, terca=True, quarta=True, quinta=True, sexta=True,
            sabado=False, domingo=False,
            timezone="America/Sao_Paulo",
            ativo=True,
            padrao=True
        )
        db.add(horario)
        db.commit()
    
    def test_tempo_util_dia_completo(self, calc: SlaCalculator):
        """
        Teste: Um dia comercial completo = 10 horas úteis
        De segunda 08:00 até segunda 18:00
        """
        inicio = datetime(2026, 1, 12, 8, 0)  # Segunda 08:00
        fim = datetime(2026, 1, 12, 18, 0)     # Segunda 18:00
        
        tempo = calc.calcular_tempo_util(
            inicio, fim,
            considera_horario_comercial=True,
            considera_feriados=True
        )
        
        # Deve ser 10 horas (08:00-18:00)
        assert abs(tempo - 10.0) < 0.1, f"Esperado 10h, obteve {tempo}h"
    
    def test_tempo_util_meio_dia(self, calc: SlaCalculator):
        """
        Teste: Meio dia comercial = 5 horas úteis
        De segunda 08:00 até segunda 13:00
        """
        inicio = datetime(2026, 1, 12, 8, 0)   # Segunda 08:00
        fim = datetime(2026, 1, 12, 13, 0)     # Segunda 13:00
        
        tempo = calc.calcular_tempo_util(
            inicio, fim,
            considera_horario_comercial=True,
            considera_feriados=True
        )
        
        # Deve ser 5 horas (08:00-13:00)
        assert abs(tempo - 5.0) < 0.1, f"Esperado 5h, obteve {tempo}h"
    
    def test_tempo_util_fora_horario(self, calc: SlaCalculator):
        """
        Teste: Fora do horário comercial = 0 horas
        De segunda 18:00 até segunda 20:00 (após expediente)
        """
        inicio = datetime(2026, 1, 12, 18, 0)  # Segunda 18:00 (fim)
        fim = datetime(2026, 1, 12, 20, 0)     # Segunda 20:00 (fora)
        
        tempo = calc.calcular_tempo_util(
            inicio, fim,
            considera_horario_comercial=True,
            considera_feriados=True
        )
        
        # Deve ser 0 horas (fora do horário)
        assert abs(tempo - 0.0) < 0.1, f"Esperado 0h, obteve {tempo}h"
    
    def test_tempo_util_fim_de_semana(self, calc: SlaCalculator):
        """
        Teste: Sábado e domingo = 0 horas úteis
        De sábado 10:00 até domingo 17:00
        """
        inicio = datetime(2026, 1, 10, 10, 0)  # Sábado 10:00
        fim = datetime(2026, 1, 11, 17, 0)     # Domingo 17:00
        
        tempo = calc.calcular_tempo_util(
            inicio, fim,
            considera_horario_comercial=True,
            considera_feriados=True
        )
        
        # Deve ser 0 horas (fim de semana)
        assert abs(tempo - 0.0) < 0.1, f"Esperado 0h, obteve {tempo}h"
    
    def test_tempo_util_cross_days(self, calc: SlaCalculator):
        """
        Teste: Múltiplos dias comerciais
        De segunda 15:00 até terça 10:00 = 3h seg + 2h ter = 5h
        """
        inicio = datetime(2026, 1, 12, 15, 0)  # Segunda 15:00
        fim = datetime(2026, 1, 13, 10, 0)     # Terça 10:00
        
        tempo = calc.calcular_tempo_util(
            inicio, fim,
            considera_horario_comercial=True,
            considera_feriados=True
        )
        
        # 15:00-18:00 (3h) + 08:00-10:00 (2h) = 5h
        assert abs(tempo - 5.0) < 0.1, f"Esperado 5h, obteve {tempo}h"


class TestSlaCalculatorComPausas:
    """Testes de cálculo com pausas"""
    
    @pytest.fixture
    def calc(self, db: Session) -> SlaCalculator:
        return SlaCalculator(db)
    
    def test_horas_pausadas(self, db: Session, calc: SlaCalculator):
        """
        Teste: Calcula horas em pausa
        Uma pausa de 2 horas deve retornar 2.0
        """
        chamado = Chamado(
            codigo="TST-001",
            titulo="Teste",
            prioridade="Normal",
            data_abertura=datetime.now()
        )
        db.add(chamado)
        db.commit()
        
        pausa = SlaPausa(
            chamado_id=chamado.id,
            pausado_em=datetime(2026, 1, 12, 10, 0),
            retomado_em=datetime(2026, 1, 12, 12, 0)  # 2 horas
        )
        db.add(pausa)
        db.commit()
        
        horas = calc.calcular_horas_pausas(chamado.id)
        
        # Deve ser 2 horas
        assert abs(horas - 2.0) < 0.1, f"Esperado 2h, obteve {horas}h"
    
    def test_multiplas_pausas(self, db: Session, calc: SlaCalculator):
        """
        Teste: Múltiplas pausas são somadas
        Pausa 1: 2h, Pausa 2: 3h = 5h total
        """
        chamado = Chamado(
            codigo="TST-002",
            titulo="Teste",
            prioridade="Normal",
            data_abertura=datetime.now()
        )
        db.add(chamado)
        db.commit()
        
        pausa1 = SlaPausa(
            chamado_id=chamado.id,
            pausado_em=datetime(2026, 1, 12, 10, 0),
            retomado_em=datetime(2026, 1, 12, 12, 0)  # 2 horas
        )
        pausa2 = SlaPausa(
            chamado_id=chamado.id,
            pausado_em=datetime(2026, 1, 12, 14, 0),
            retomado_em=datetime(2026, 1, 12, 17, 0)  # 3 horas
        )
        db.add(pausa1)
        db.add(pausa2)
        db.commit()
        
        horas = calc.calcular_horas_pausas(chamado.id)
        
        # Deve ser 5 horas (2 + 3)
        assert abs(horas - 5.0) < 0.1, f"Esperado 5h, obteve {horas}h"
    
    def test_pausa_aberta(self, db: Session, calc: SlaCalculator):
        """
        Teste: Pausa aberta (sem retomado_em) não conta
        """
        chamado = Chamado(
            codigo="TST-003",
            titulo="Teste",
            prioridade="Normal",
            data_abertura=datetime.now()
        )
        db.add(chamado)
        db.commit()
        
        pausa = SlaPausa(
            chamado_id=chamado.id,
            pausado_em=datetime(2026, 1, 12, 10, 0),
            retomado_em=None  # Pausa ainda aberta
        )
        db.add(pausa)
        db.commit()
        
        horas = calc.calcular_horas_pausas(chamado.id)
        
        # Não deve contar (pausa aberta)
        assert abs(horas - 0.0) < 0.1, f"Esperado 0h (aberta), obteve {horas}h"
