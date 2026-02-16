"""
Modelos de banco de dados para o módulo SLA
Suporta cálculo de horas úteis, pausas automáticas e feriados móveis
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, 
    Float, Text, ForeignKey, Time, Date, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class TipoFeriado(str, enum.Enum):
    """Tipos de feriado"""
    NACIONAL = "nacional"  # Feriado nacional (não trabalha)
    PONTO_FACULTATIVO = "ponto_facultativo"  # Ponto facultativo
    MUNICIPIO = "municipio"  # Feriado municipal
    ESTADUAL = "estadual"  # Feriado estadual


class StatusChamado(str, enum.Enum):
    """Status válidos do chamado para SLA"""
    ABERTO = "Aberto"
    EM_ATENDIMENTO = "Em atendimento"
    AGUARDANDO = "Aguardando"
    EM_ANALISE = "Em análise"
    CANCELADO = "Expirado"
    CONCLUIDO = "Concluído"


class ConfiguracaoSLA(Base):
    """Configurações de SLA por prioridade"""
    __tablename__ = "sla_configuracao"
    
    id = Column(Integer, primary_key=True, index=True)
    prioridade = Column(String(50), unique=True, nullable=False, index=True)
    tempo_resposta_horas = Column(Float, nullable=False)
    tempo_resolucao_horas = Column(Float, nullable=False)
    percentual_risco = Column(Float, default=80.0)  # % para considerar em risco
    considera_horario_comercial = Column(Boolean, default=True)
    considera_feriados = Column(Boolean, default=True)
    escalar_automaticamente = Column(Boolean, default=False)
    notificar_em_risco = Column(Boolean, default=True)
    descricao = Column(Text)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HorarioComercial(Base):
    """Configuração de horário comercial por dia da semana"""
    __tablename__ = "sla_horario_comercial"
    
    id = Column(Integer, primary_key=True, index=True)
    dia_semana = Column(Integer, nullable=False, index=True)  # 0=seg, 1=ter, ..., 4=sex, 5=sab, 6=dom
    hora_inicio = Column(Time, nullable=False)
    hora_fim = Column(Time, nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Feriado(Base):
    """Feriados (fixos e móveis) para cálculo de SLA"""
    __tablename__ = "sla_feriado"
    
    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, nullable=False, index=True)
    nome = Column(String(200), nullable=False)
    descricao = Column(Text)
    tipo = Column(String(50), default=TipoFeriado.NACIONAL.value)  # tipo de feriado
    recorrente = Column(Boolean, default=False)  # Se repete todo ano (fixo)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        # Índice composto para buscas eficientes
        {'indexes': [
            'CREATE UNIQUE INDEX ix_feriado_data_ano ON sla_feriado(data, ativo)'
        ]},
    )


class PausaSLA(Base):
    """Pausas automáticas e manuais de SLA"""
    __tablename__ = "sla_pausa"
    
    id = Column(Integer, primary_key=True, index=True)
    chamado_id = Column(Integer, ForeignKey("chamado.id"), nullable=False, index=True)
    inicio = Column(DateTime, nullable=False)
    fim = Column(DateTime)  # NULL se ainda está pausado
    motivo = Column(String(500))
    tipo = Column(String(50))  # 'status' para pausas por status, 'manual' para pausas manuais
    status_pausante = Column(String(50))  # Status do chamado que causou a pausa
    duracao_horas = Column(Float, default=0.0)  # Recalculado quando finaliza
    criado_por_id = Column(Integer, ForeignKey("usuario.id"))
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InfoSLAChamado(Base):
    """Informações calculadas de SLA para cada chamado"""
    __tablename__ = "sla_info_chamado"
    
    id = Column(Integer, primary_key=True, index=True)
    chamado_id = Column(Integer, ForeignKey("chamado.id"), nullable=False, unique=True, index=True)
    
    # Tempos de resposta
    tempo_resposta_limite_horas = Column(Float)
    tempo_resposta_decorrido_horas = Column(Float, default=0.0)
    tempo_resposta_pausado_horas = Column(Float, default=0.0)
    percentual_resposta = Column(Float, default=0.0)
    resposta_em_risco = Column(Boolean, default=False, index=True)
    resposta_vencida = Column(Boolean, default=False, index=True)
    resposta_em_dia = Column(Boolean, default=True)
    
    # Tempos de resolução
    tempo_resolucao_limite_horas = Column(Float)
    tempo_resolucao_decorrido_horas = Column(Float, default=0.0)
    tempo_resolucao_pausado_horas = Column(Float, default=0.0)
    percentual_resolucao = Column(Float, default=0.0)
    resolucao_em_risco = Column(Boolean, default=False, index=True)
    resolucao_vencida = Column(Boolean, default=False, index=True)
    resolucao_em_dia = Column(Boolean, default=True)
    
    # Status
    pausado = Column(Boolean, default=False, index=True)
    ativo = Column(Boolean, default=True, index=True)
    
    # Timestamps
    ultima_atualizacao = Column(DateTime, default=datetime.utcnow)
    data_ultima_pausa = Column(DateTime)
    data_ultima_retomada = Column(DateTime)


class LogCalculoSLA(Base):
    """Histórico de cálculos de SLA"""
    __tablename__ = "sla_log_calculo"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50))  # 'batch', 'individual', 'reset'
    data_execucao = Column(DateTime, default=datetime.utcnow)
    chamados_processados = Column(Integer, default=0)
    tempo_execucao_ms = Column(Integer)
    chamados_em_risco = Column(Integer, default=0)
    chamados_vencidos = Column(Integer, default=0)
    chamados_pausados = Column(Integer, default=0)
    sucesso = Column(Boolean, default=True)
    mensagem_erro = Column(Text)


class Chamado(Base):
    """Modelo de chamado (referência para relacionamentos com SLA)"""
    __tablename__ = "chamado"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, index=True)
    protocolo = Column(String(50), unique=True)
    
    # Informações do solicitante
    solicitante = Column(String(200))
    cargo = Column(String(100))
    email = Column(String(200))
    telefone = Column(String(50))
    unidade = Column(String(200))
    
    # Detalhes do problema
    problema = Column(String(500))
    internet_item = Column(String(200))
    descricao = Column(Text)
    
    # Datas importantes
    data_abertura = Column(DateTime, nullable=False, index=True)
    data_primeira_resposta = Column(DateTime)
    data_visita = Column(DateTime)
    data_conclusao = Column(DateTime)
    
    # Status e prioridade
    status = Column(String(50), nullable=False, index=True)
    prioridade = Column(String(50), default="Normal", index=True)
    
    # Relacionamentos com usuários
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    atribuido_por_id = Column(Integer, ForeignKey("usuario.id"))
    fechado_por_id = Column(Integer, ForeignKey("usuario.id"))
    agente_atual_id = Column(Integer, ForeignKey("usuario.id"))
    status_assumido_por_id = Column(Integer, ForeignKey("usuario.id"))
    concluido_por_id = Column(Integer, ForeignKey("usuario.id"))
    cancelado_por_id = Column(Integer, ForeignKey("usuario.id"))
    
    # Dados adicionais
    observacoes = Column(Text)
    metadados_extras = Column(Text)
    
    # Controle de reaberturas e transferências
    qtd_reaberturas = Column(Integer, default=0)
    chamado_origem_id = Column(Integer, ForeignKey("chamado.id"))
    reaberto = Column(Boolean, default=False)
    numero_reaberturas = Column(Integer, default=0)
    numero_transferencias = Column(Integer, default=0)
    transferido = Column(Boolean, default=False)
    data_ultima_transferencia = Column(DateTime)
    
    # Controle de datas
    status_assumido_em = Column(DateTime)
    concluido_em = Column(DateTime)
    cancelado_em = Column(DateTime)
    session_revoked_at = Column(DateTime)
    deletado_em = Column(DateTime)
    
    # Timestamps
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Usuario(Base):
    """Modelo de usuário (referência para FK)"""
    __tablename__ = "usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200))
    email = Column(String(200), unique=True)
    ativo = Column(Boolean, default=True)
