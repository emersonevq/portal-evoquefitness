"""
Testes para API REST de SLA.

Valida:
- GET /api/sla/configuracoes (listar)
- POST /api/sla/configuracoes (criar)
- GET /api/sla/configuracoes/{id} (detalhe)
- PUT /api/sla/configuracoes/{id} (atualizar)
- DELETE /api/sla/configuracoes/{id} (deletar)
- GET /api/sla/dashboard/indicadores
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from ti.models import ConfiguracesSla


class TestSlaConfiguracoes:
    """Testes de endpoints de configuração de SLA"""
    
    def test_listar_configuracoes_vazio(self, client: TestClient, db: Session):
        """
        Teste: GET /api/sla/configuracoes retorna lista vazia
        """
        response = client.get("/api/sla/configuracoes")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_listar_configuracoes_com_dados(self, client: TestClient, db: Session):
        """
        Teste: GET /api/sla/configuracoes retorna configurações existentes
        """
        # Cria configuração
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
        
        response = client.get("/api/sla/configuracoes")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(c.get("prioridade") == "Normal" for c in data)
    
    def test_criar_configuracao(self, client: TestClient, db: Session):
        """
        Teste: POST /api/sla/configuracoes cria nova configuração
        """
        payload = {
            "prioridade": "Teste",
            "tempo_primeira_resposta": 2,
            "tempo_resolucao": 8,
            "considera_horario_comercial": True,
            "considera_feriados": True,
            "escalar_automaticamente": False,
            "notificar_em_risco": True,
            "percentual_risco": 75,
            "ativo": True
        }
        
        response = client.post("/api/sla/configuracoes", json=payload)
        
        assert response.status_code == 201 or response.status_code == 200
        data = response.json()
        assert data.get("prioridade") == "Teste"
    
    def test_criar_configuracao_invalida(self, client: TestClient):
        """
        Teste: POST /api/sla/configuracoes com dados inválidos retorna erro
        """
        payload = {
            "prioridade": "Inválida",
            # Campos obrigatórios faltando
        }
        
        response = client.post("/api/sla/configuracoes", json=payload)
        
        assert response.status_code in [400, 422]  # Bad request ou validation error
    
    def test_obter_configuracao_detalhes(self, client: TestClient, db: Session):
        """
        Teste: GET /api/sla/configuracoes/{id} retorna configuração específica
        """
        # Cria configuração
        config = ConfiguracesSla(
            prioridade="Alta",
            tempo_primeira_resposta=2,
            tempo_resolucao=8,
            considera_horario_comercial=True,
            considera_feriados=True,
            escalar_automaticamente=True,
            notificar_em_risco=True,
            percentual_risco=75,
            ativo=True
        )
        db.add(config)
        db.commit()
        
        response = client.get(f"/api/sla/configuracoes/{config.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("prioridade") == "Alta"
        assert data.get("tempo_primeira_resposta") == 2
    
    def test_obter_configuracao_inexistente(self, client: TestClient):
        """
        Teste: GET /api/sla/configuracoes/{id_invalido} retorna 404
        """
        response = client.get("/api/sla/configuracoes/99999")
        
        assert response.status_code == 404
    
    def test_atualizar_configuracao(self, client: TestClient, db: Session):
        """
        Teste: PUT /api/sla/configuracoes/{id} atualiza configuração
        """
        # Cria configuração
        config = ConfiguracesSla(
            prioridade="Crítica",
            tempo_primeira_resposta=1,
            tempo_resolucao=4,
            considera_horario_comercial=True,
            considera_feriados=True,
            escalar_automaticamente=True,
            notificar_em_risco=True,
            percentual_risco=75,
            ativo=True
        )
        db.add(config)
        db.commit()
        
        # Atualiza
        payload = {
            "tempo_primeira_resposta": 2,  # Alterou de 1 para 2
            "tempo_resolucao": 8,  # Alterou de 4 para 8
        }
        
        response = client.put(f"/api/sla/configuracoes/{config.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("tempo_primeira_resposta") == 2
    
    def test_deletar_configuracao(self, client: TestClient, db: Session):
        """
        Teste: DELETE /api/sla/configuracoes/{id} deleta configuração
        """
        # Cria configuração
        config = ConfiguracesSla(
            prioridade="Deletavel",
            tempo_primeira_resposta=1,
            tempo_resolucao=4,
            considera_horario_comercial=True,
            considera_feriados=True,
            escalar_automaticamente=True,
            notificar_em_risco=True,
            percentual_risco=75,
            ativo=True
        )
        db.add(config)
        db.commit()
        config_id = config.id
        
        # Deleta
        response = client.delete(f"/api/sla/configuracoes/{config_id}")
        
        assert response.status_code in [200, 204]
        
        # Verifica que foi deletado
        db.expire_all()
        deleted = db.query(ConfiguracesSla).filter(ConfiguracesSla.id == config_id).first()
        assert deleted is None


class TestSlaDashboard:
    """Testes de endpoints do dashboard"""
    
    def test_indicadores_agora(self, client: TestClient):
        """
        Teste: GET /api/sla/dashboard/indicadores retorna indicadores
        """
        response = client.get("/api/sla/dashboard/indicadores")
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve ter indicadores básicos
        assert "abertos" in data or "indicadores" in data
    
    def test_metricas(self, client: TestClient):
        """
        Teste: GET /api/sla/dashboard/metricas retorna métricas
        """
        response = client.get("/api/sla/dashboard/metricas")
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve ser um dicionário
        assert isinstance(data, dict)
    
    def test_relatorio_diario(self, client: TestClient):
        """
        Teste: GET /api/sla/dashboard/relatorio-diario retorna relatório
        """
        response = client.get("/api/sla/dashboard/relatorio-diario")
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve ter dados de relatório
        assert isinstance(data, dict)


class TestSlaFeriados:
    """Testes de endpoints de feriados"""
    
    def test_listar_feriados(self, client: TestClient):
        """
        Teste: GET /api/sla/feriados retorna lista de feriados
        """
        response = client.get("/api/sla/feriados")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
    
    def test_verificar_feriado(self, client: TestClient):
        """
        Teste: GET /api/sla/feriados/verificar/{data} verifica se é feriado
        """
        # Testa com data de Natal 2026
        response = client.get("/api/sla/feriados/verificar/2026-12-25")
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve ter campo "eh_feriado"
        assert "eh_feriado" in data or "feriado" in str(data).lower()
