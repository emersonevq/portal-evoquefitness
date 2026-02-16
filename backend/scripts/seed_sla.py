#!/usr/bin/env python3
"""
Script para popular dados padrão de SLA no banco de dados.

Insere:
1. Configurações de SLA por prioridade (4 prioridades)
2. Horário comercial padrão (08h-18h, seg-sex)
3. Feriados fixos do Brasil para 2026

Uso:
    python backend/scripts/seed_sla.py
"""

import sys
from datetime import date, datetime
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from core.db import SessionLocal
from ti.models import ConfiguracesSla, HorarioComercial, Feriado


def seed_configuracoes_sla(db: Session) -> None:
    """Insere configurações padrão de SLA por prioridade."""
    print("\n📋 Inserindo Configurações de SLA...")
    
    configuracoes = [
        ConfiguracesSla(
            prioridade="Crítica",
            tempo_primeira_resposta=1,  # 1 hora
            tempo_resolucao=4,  # 4 horas
            considera_horario_comercial=True,
            considera_feriados=True,
            escalar_automaticamente=True,
            notificar_em_risco=True,
            percentual_risco=75,
            ativo=True,
        ),
        ConfiguracesSla(
            prioridade="Alta",
            tempo_primeira_resposta=2,  # 2 horas
            tempo_resolucao=8,  # 8 horas
            considera_horario_comercial=True,
            considera_feriados=True,
            escalar_automaticamente=True,
            notificar_em_risco=True,
            percentual_risco=75,
            ativo=True,
        ),
        ConfiguracesSla(
            prioridade="Normal",
            tempo_primeira_resposta=4,  # 4 horas
            tempo_resolucao=24,  # 24 horas
            considera_horario_comercial=True,
            considera_feriados=True,
            escalar_automaticamente=True,
            notificar_em_risco=True,
            percentual_risco=75,
            ativo=True,
        ),
        ConfiguracesSla(
            prioridade="Baixa",
            tempo_primeira_resposta=8,  # 8 horas
            tempo_resolucao=48,  # 48 horas
            considera_horario_comercial=True,
            considera_feriados=True,
            escalar_automaticamente=False,
            notificar_em_risco=True,
            percentual_risco=75,
            ativo=True,
        ),
    ]
    
    # Verificar se já existem
    for config in configuracoes:
        existing = db.query(ConfiguracesSla).filter(
            ConfiguracesSla.prioridade == config.prioridade
        ).first()
        
        if existing:
            print(f"  ⏭️  Configuração para '{config.prioridade}' já existe")
        else:
            db.add(config)
            print(f"  ✓ Adicionada configuração para '{config.prioridade}'")
    
    db.commit()
    print("✓ Configurações de SLA inseridas com sucesso")


def seed_horario_comercial(db: Session) -> None:
    """Insere horário comercial padrão."""
    print("\n⏰ Inserindo Horário Comercial...")
    
    # Verificar se já existe
    existing = db.query(HorarioComercial).filter(
        HorarioComercial.padrao == True
    ).first()
    
    if existing:
        print(f"  ⏭️  Horário comercial padrão já existe")
        return
    
    horario = HorarioComercial(
        nome="Comercial Padrão",
        descricao="Das 08h às 18h, segunda a sexta",
        hora_inicio="08:00:00",
        hora_fim="18:00:00",
        segunda=True,
        terca=True,
        quarta=True,
        quinta=True,
        sexta=True,
        sabado=False,
        domingo=False,
        considera_almoco=False,  # Sem pausa de almoço por enquanto
        almoco_inicio=None,
        almoco_fim=None,
        emergencia_ativo=False,
        timezone="America/Sao_Paulo",
        considera_feriados=True,
        ativo=True,
        padrao=True,
    )
    
    db.add(horario)
    db.commit()
    print("  ✓ Horário comercial padrão inserido com sucesso")


def seed_feriados(db: Session) -> None:
    """Insere feriados fixos do Brasil para 2026."""
    print("\n📅 Inserindo Feriados Nacionais...")
    
    feriados_fixos = [
        # Feriados fixos de 2026
        Feriado(
            data=date(2026, 1, 1),
            nome="Ano Novo",
            tipo="fixo",
            descricao="Feriado Nacional - Ano Novo",
            ativo=True,
        ),
        Feriado(
            data=date(2026, 4, 21),
            nome="Tiradentes",
            tipo="fixo",
            descricao="Feriado Nacional - Tiradentes",
            ativo=True,
        ),
        Feriado(
            data=date(2026, 5, 1),
            nome="Dia do Trabalho",
            tipo="fixo",
            descricao="Feriado Nacional - Dia do Trabalho",
            ativo=True,
        ),
        Feriado(
            data=date(2026, 9, 7),
            nome="Independência do Brasil",
            tipo="fixo",
            descricao="Feriado Nacional - Independência do Brasil",
            ativo=True,
        ),
        Feriado(
            data=date(2026, 10, 12),
            nome="Nossa Senhora Aparecida",
            tipo="fixo",
            descricao="Feriado Nacional - Nossa Senhora Aparecida",
            ativo=True,
        ),
        Feriado(
            data=date(2026, 11, 2),
            nome="Finados",
            tipo="fixo",
            descricao="Feriado Nacional - Finados",
            ativo=True,
        ),
        Feriado(
            data=date(2026, 11, 15),
            nome="Proclamação da República",
            tipo="fixo",
            descricao="Feriado Nacional - Proclamação da República",
            ativo=True,
        ),
        Feriado(
            data=date(2026, 12, 25),
            nome="Natal",
            tipo="fixo",
            descricao="Feriado Nacional - Natal",
            ativo=True,
        ),
        
        # Feriados móveis em 2026
        # Páscoa: 5 de abril
        Feriado(
            data=date(2026, 4, 3),
            nome="Sexta-feira Santa",
            tipo="movel",
            descricao="Feriado Móvel - Sexta-feira Santa (2 dias antes de Páscoa)",
            ativo=True,
        ),
        Feriado(
            data=date(2026, 4, 5),
            nome="Páscoa",
            tipo="movel",
            descricao="Feriado Móvel - Páscoa",
            ativo=True,
        ),
        # Corpus Christi: 59 dias depois de Páscoa = 3 de junho
        Feriado(
            data=date(2026, 6, 3),
            nome="Corpus Christi",
            tipo="movel",
            descricao="Feriado Móvel - Corpus Christi",
            ativo=True,
        ),
    ]
    
    inseridos = 0
    for feriado in feriados_fixos:
        existing = db.query(Feriado).filter(
            Feriado.data == feriado.data,
            Feriado.nome == feriado.nome
        ).first()
        
        if existing:
            print(f"  ⏭️  Feriado '{feriado.nome}' em {feriado.data} já existe")
        else:
            db.add(feriado)
            inseridos += 1
            print(f"  ✓ Adicionado feriado '{feriado.nome}' ({feriado.data})")
    
    db.commit()
    print(f"✓ {inseridos} novos feriados inseridos com sucesso")


def main():
    """Executa o seed de dados padrão de SLA."""
    print("=" * 60)
    print("🌱 SEED DE DADOS - MÓDULO SLA")
    print("=" * 60)
    print(f"Banco de dados: {backend_path.parent.parent}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    db = SessionLocal()
    
    try:
        seed_configuracoes_sla(db)
        seed_horario_comercial(db)
        seed_feriados(db)
        
        print("\n" + "=" * 60)
        print("✅ SEED CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print("\nDados inseridos:")
        print(f"  • 4 configurações de SLA (Crítica, Alta, Normal, Baixa)")
        print(f"  • 1 horário comercial padrão (08h-18h, seg-sex)")
        print(f"  • 11 feriados nacionais (8 fixos + 3 móveis em 2026)")
        print("\n💡 Próximos passos:")
        print("  1. Iniciar o servidor: python -m uvicorn main:app --reload")
        print("  2. Validar configurações em GET /api/sla/configuracoes")
        print("  3. Criar um chamado para testar o SLA")
        
    except Exception as e:
        print(f"\n❌ ERRO durante seed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
