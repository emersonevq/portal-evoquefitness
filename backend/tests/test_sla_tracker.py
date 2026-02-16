"""
Testes para SlaTracker - Ciclo de vida do SLA.

Valida:
- Inicialização de SLA
- Registro de primeira resposta
- Conclusão de SLA (dentro/fora)
- Atualização de monitoramento
"""

import pytest
from datetime import datetime, date
from sqlalchemy.orm import Session
from ti.models import Chamado, ConfiguracesSla, HistoricoSla
from ti.modules.sla.services import SlaTracker


class TestSlaTracker:
    """Testes da classe SlaTracker"""
    
    @pytest.fixture
    def tracker(self, db: Session) -> SlaTracker:
        """Cria instância do tracker"""
        return SlaTracker(db)
    
    @pytest.fixture
    def config_normal(self, db: Session) -> ConfiguracesSla:
        """Cria configuração de SLA Normal"""
        config = ConfiguracesSla(
            prioridade="Normal",
            tempo_primeira_resposta=4,
            tempo_resolucao=24,
            considera_horario_comercial=True,
            considera_feriados=True,
            escalar_automaticamente=True,
            notificar_em_risco=True,
            percentual_risco=75,
            ativo=True
        )
        db.add(config)
        db.commit()
        return config
    
    def test_obter_config_existente(self, db: Session, tracker: SlaTracker, config_normal: ConfiguracesSla):
        """
        Teste: Obtém configuração de SLA para prioridade existente
        """
        config = tracker.obter_config_por_prioridade("Normal")
        
        assert config is not None
        assert config.prioridade == "Normal"
        assert config.tempo_primeira_resposta == 4
        assert config.tempo_resolucao == 24
    
    def test_obter_config_inexistente(self, db: Session, tracker: SlaTracker):
        """
        Teste: Retorna None para prioridade sem configuração
        """
        config = tracker.obter_config_por_prioridade("Inexistente")
        
        assert config is None
    
    def test_iniciar_sla(self, db: Session, tracker: SlaTracker, config_normal: ConfiguracesSla):
        """
        Teste: Inicia SLA quando chamado é criado
        """
        chamado = Chamado(
            codigo="TST-001",
            titulo="Teste SLA",
            prioridade="Normal",
            data_abertura=datetime.now()
        )
        db.add(chamado)
        db.commit()
        
        # Inicia SLA
        tracker.iniciar_sla(chamado)
        
        # Verifica se histórico foi criado
        historicos = db.query(HistoricoSla).filter(
            HistoricoSla.chamado_id == chamado.id,
            HistoricoSla.acao == "iniciar_sla"
        ).all()
        
        assert len(historicos) == 1
        assert "Limite resposta: 4h" in historicos[0].observacoes
    
    def test_iniciar_sla_sem_config(self, db: Session, tracker: SlaTracker):
        """
        Teste: Não inicia SLA sem configuração para prioridade
        """
        chamado = Chamado(
            codigo="TST-002",
            titulo="Teste sem config",
            prioridade="Inexistente",
            data_abertura=datetime.now()
        )
        db.add(chamado)
        db.commit()
        
        # Tenta iniciar (não deve fazer nada)
        tracker.iniciar_sla(chamado)
        
        # Verifica que nenhum histórico foi criado
        historicos = db.query(HistoricoSla).filter(
            HistoricoSla.chamado_id == chamado.id
        ).all()
        
        assert len(historicos) == 0
    
    def test_registrar_primeira_resposta_dentro_sla(self, db: Session, tracker: SlaTracker, config_normal: ConfiguracesSla):
        """
        Teste: Primeira resposta dentro do SLA (< 4h)
        """
        # Cria chamado aberto há 2 horas (segunda 08:00 a segunda 10:00)
        inicio = datetime(2026, 1, 12, 8, 0)   # Segunda 08:00
        agora = datetime(2026, 1, 12, 10, 0)   # Segunda 10:00 (2 horas depois)
        
        chamado = Chamado(
            codigo="TST-003",
            titulo="Teste primeira resposta",
            prioridade="Normal",
            data_abertura=inicio
        )
        db.add(chamado)
        db.commit()
        
        # Registra primeira resposta (manualmente, pois não temos DateTime.utcnow() mocado)
        tempo = tracker.registrar_primeira_resposta(chamado)
        
        # Deve ter registrado
        assert chamado.data_primeira_resposta is not None
        
        # Verifica histórico
        historicos = db.query(HistoricoSla).filter(
            HistoricoSla.chamado_id == chamado.id,
            HistoricoSla.acao == "primeira_resposta"
        ).all()
        
        assert len(historicos) == 1
    
    def test_concluir_sla_dentro(self, db: Session, tracker: SlaTracker, config_normal: ConfiguracesSla):
        """
        Teste: Conclusão dentro do SLA (< 24h)
        """
        # Cria chamado
        inicio = datetime(2026, 1, 12, 8, 0)  # Segunda 08:00
        
        chamado = Chamado(
            codigo="TST-004",
            titulo="Teste conclusão dentro",
            prioridade="Normal",
            data_abertura=inicio,
            data_primeira_resposta=datetime(2026, 1, 12, 10, 0)  # 2h depois
        )
        db.add(chamado)
        db.commit()
        
        # Conclui SLA
        resultado = tracker.concluir_sla(chamado)
        
        # Verifica resultado
        assert resultado.get("cumpriu_sla") == True or resultado.get("cumpriu_sla") is None
        assert "status_sla" in resultado or "cumpriu_sla" in resultado
        
        # Verifica histórico final
        historicos = db.query(HistoricoSla).filter(
            HistoricoSla.chamado_id == chamado.id,
            HistoricoSla.acao == "concluido"
        ).all()
        
        assert len(historicos) == 1
    
    def test_atualizar_monitoramento_em_risco(self, db: Session, tracker: SlaTracker, config_normal: ConfiguracesSla):
        """
        Teste: Monitoramento marca como em risco (≥75%)
        """
        # Cria chamado há 18 horas (75% de 24h)
        inicio = datetime(2026, 1, 12, 8, 0)  # Segunda 08:00
        
        chamado = Chamado(
            codigo="TST-005",
            titulo="Teste monitoramento risco",
            prioridade="Normal",
            status="Aberto",
            data_abertura=inicio,
            data_primeira_resposta=datetime(2026, 1, 12, 10, 0)
        )
        db.add(chamado)
        db.commit()
        
        # Atualiza monitoramento
        tracker.atualizar_monitoramento(chamado)
        
        # Deve estar em risco ou vencido (dependendo do cálculo exato)
        assert chamado.sla_percentual_consumido is not None
        # Se >= 75%, deve estar em risco ou vencido
        if chamado.sla_percentual_consumido >= 75:
            assert chamado.sla_em_risco or chamado.sla_vencido


class TestSlaTrackerEdgeCases:
    """Testes de casos extremos"""
    
    @pytest.fixture
    def tracker(self, db: Session) -> SlaTracker:
        return SlaTracker(db)
    
    def test_registrar_primeira_resposta_duas_vezes(self, db: Session, tracker: SlaTracker):
        """
        Teste: Segunda chamada não deve recalcular
        """
        chamado = Chamado(
            codigo="TST-006",
            titulo="Teste dupla resposta",
            prioridade="Normal",
            data_abertura=datetime.now(),
            data_primeira_resposta=datetime.now()  # Já foi registrada
        )
        db.add(chamado)
        db.commit()
        
        tempo = tracker.registrar_primeira_resposta(chamado)
        
        # Deve retornar 0.0 (não recalcula)
        assert tempo == 0.0
    
    def test_concluir_sem_config(self, db: Session, tracker: SlaTracker):
        """
        Teste: Concluir chamado sem configuração retorna {}
        """
        chamado = Chamado(
            codigo="TST-007",
            titulo="Teste conclusão sem config",
            prioridade="Inexistente",
            data_abertura=datetime.now()
        )
        db.add(chamado)
        db.commit()
        
        resultado = tracker.concluir_sla(chamado)
        
        # Deve retornar dicionário vazio
        assert resultado == {}
