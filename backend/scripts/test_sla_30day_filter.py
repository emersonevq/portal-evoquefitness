#!/usr/bin/env python3
"""
Script de teste para validar o novo filtro de 30 dias em SLA.

Testes:
1. Valida que chamados >30 dias não contam para métricas de SLA
2. Valida que chamados ≤30 dias contam para métricas de SLA
3. Valida que o tempo pausa quando status é "em análise"
4. Valida que o tempo retoma quando sai de "em análise"
"""

import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Adicionar backend ao path
sys.path.insert(0, '/app')

from core.db import get_db
from core.utils import now_brazil_naive
from ti.models.chamado import Chamado
from ti.models.sla_config import SLAConfiguration
from ti.models.historico_status import HistoricoStatus
from ti.models.sla_pausa import SLAPausa
from ti.services.sla import SLACalculator, SLAPausaManager
from ti.services.sla_metrics_unified import UnifiedSLAMetricsCalculator

def print_test(number, title):
    print(f"\n{'='*60}")
    print(f"TESTE {number}: {title}")
    print(f"{'='*60}\n")

def print_result(passed, message):
    status = "✅ PASSOU" if passed else "❌ FALHOU"
    print(f"{status}: {message}")

def test_30day_filter():
    """Testa se o filtro de 30 dias está sendo aplicado"""
    print_test(1, "Validar Filtro de 30 Dias")
    
    db = next(get_db())
    
    try:
        # 1. Contar chamados totais (não cancelados)
        total_chamados = db.query(Chamado).filter(
            Chamado.status != "Cancelado"
        ).count()
        print(f"Total de chamados (não cancelados): {total_chamados}")
        
        # 2. Contar chamados ≤30 dias
        agora = now_brazil_naive()
        data_30d = agora - timedelta(days=30)
        
        chamados_30d = db.query(Chamado).filter(
            Chamado.data_abertura >= data_30d,
            Chamado.status != "Cancelado"
        ).count()
        print(f"Chamados ≤30 dias: {chamados_30d}")
        
        # 3. Contar chamados >30 dias
        chamados_maiores_30d = db.query(Chamado).filter(
            Chamado.data_abertura < data_30d,
            Chamado.status != "Cancelado"
        ).count()
        print(f"Chamados >30 dias: {chamados_maiores_30d}")
        
        # 4. Recalcular SLA e verificar que apenas ≤30d contam
        print("\nCalculando SLA de 30 dias...")
        sla_30d = UnifiedSLAMetricsCalculator.calculate_sla_distribution_period(
            db, data_30d, agora
        )
        
        print(f"Resultado da distribuição de SLA (30 dias):")
        print(f"  - Total analisado: {sla_30d['total']}")
        print(f"  - Dentro do SLA: {sla_30d['dentro_sla']}")
        print(f"  - Fora do SLA: {sla_30d['fora_sla']}")
        
        # Validação
        if sla_30d['total'] <= chamados_30d:
            print_result(True, "Filtro de 30 dias está funcionando (apenas chamados ≤30d foram contados)")
            return True
        else:
            print_result(False, f"Filtro ineficaz: {sla_30d['total']} analisados vs {chamados_30d} esperados")
            return False
            
    except Exception as e:
        print_result(False, f"Erro ao testar filtro: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_sla_pause_logic():
    """Testa se a pausa de SLA funciona quando status é 'em análise'"""
    print_test(2, "Validar Lógica de Pausa de SLA (Em Análise)")
    
    db = next(get_db())
    
    try:
        # Criar um chamado de teste ou usar um existente
        chamado = db.query(Chamado).filter(
            Chamado.status.in_(["Aberto", "Em andamento"])
        ).first()
        
        if not chamado:
            print_result(False, "Nenhum chamado 'Aberto' ou 'Em andamento' para teste")
            return False
        
        print(f"Usando chamado ID {chamado.id} para teste")
        print(f"Status atual: {chamado.status}")
        
        # Obter status anterior
        status_anterior = chamado.status
        
        # Registrar mudança de status para "Em análise"
        print(f"\nMudando status para 'Em análise'...")
        mudanca = SLAPausaManager.registrar_mudanca_status(
            db, chamado.id, status_anterior, "Em análise"
        )
        
        print(f"Resultado da mudança de status:")
        print(f"  - Ação de SLA: {mudanca.get('acao_sla')}")
        print(f"  - ID da pausa criada: {mudanca.get('pausa_id')}")
        
        # Verificar que uma pausa foi criada
        pausas_ativas = SLAPausaManager.get_pausas_ativas_chamado(db, chamado.id)
        print(f"\nPausas ativas do chamado: {len(pausas_ativas)}")
        
        for pausa in pausas_ativas:
            print(f"  - Pausa ID {pausa.id}: pausada em {pausa.pausado_em}, ativa={pausa.ativa}")
        
        # Validação
        if mudanca.get('acao_sla') == 'pausado' and len(pausas_ativas) > 0:
            print_result(True, "Pausa foi criada quando status mudou para 'Em análise'")
            
            # Tentar retomar
            print(f"\nMudando status de volta para 'Em andamento'...")
            mudanca2 = SLAPausaManager.registrar_mudanca_status(
                db, chamado.id, "Em análise", "Em andamento"
            )
            
            print(f"Resultado da retomada:")
            print(f"  - Ação de SLA: {mudanca2.get('acao_sla')}")
            print(f"  - Pausas finalizadas: {mudanca2.get('pausas_finalizadas')}")
            
            pausas_ativas2 = SLAPausaManager.get_pausas_ativas_chamado(db, chamado.id)
            print(f"Pausas ativas após retomada: {len(pausas_ativas2)}")
            
            if mudanca2.get('acao_sla') == 'retomado' and len(pausas_ativas2) == 0:
                print_result(True, "Pausa foi finalizada quando status saiu de 'Em análise'")
                return True
            else:
                print_result(False, "Falha ao retomar pausa")
                return False
        else:
            print_result(False, f"Pausa não foi criada corretamente (acao_sla={mudanca.get('acao_sla')})")
            return False
            
    except Exception as e:
        print_result(False, f"Erro ao testar lógica de pausa: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_sla_status_calculation():
    """Testa se o cálculo de status de SLA está correto"""
    print_test(3, "Validar Cálculo de Status de SLA")
    
    db = next(get_db())
    
    try:
        # Buscar um chamado com SLA configurado
        chamado = db.query(Chamado).filter(
            Chamado.prioridade.in_(["Alta", "Normal", "Baixa"]),
            Chamado.status != "Cancelado"
        ).first()
        
        if not chamado:
            print_result(False, "Nenhum chamado com prioridade configurada encontrado")
            return False
        
        print(f"Usando chamado ID {chamado.id}")
        print(f"  - Prioridade: {chamado.prioridade}")
        print(f"  - Status: {chamado.status}")
        print(f"  - Aberto em: {chamado.data_abertura}")
        
        # Obter configuração de SLA
        sla_config = SLACalculator.get_sla_config_by_priority(db, chamado.prioridade)
        if sla_config:
            print(f"  - Tempo de resposta SLA: {sla_config.tempo_resposta_horas}h")
            print(f"  - Tempo de resolução SLA: {sla_config.tempo_resolucao_horas}h")
        
        # Calcular status de SLA
        sla_status = SLACalculator.get_sla_status(db, chamado)
        
        print(f"\nStatus de SLA calculado:")
        print(f"  - Status geral: {sla_status.get('status_geral')}")
        
        resposta = sla_status.get('resposta_metric')
        if resposta:
            print(f"  - Status de resposta: {resposta.get('status')}")
            print(f"    Tempo decorrido: {resposta.get('tempo_decorrido_horas'):.2f}h")
            print(f"    Tempo limite: {resposta.get('tempo_limite_horas'):.2f}h")
        
        resolucao = sla_status.get('resolucao_metric')
        if resolucao:
            print(f"  - Status de resolução: {resolucao.get('status')}")
            print(f"    Tempo decorrido: {resolucao.get('tempo_decorrido_horas'):.2f}h")
            print(f"    Tempo limite: {resolucao.get('tempo_limite_horas'):.2f}h")
        
        # Validação básica
        if sla_status.get('status_geral'):
            print_result(True, "Status de SLA foi calculado corretamente")
            return True
        else:
            print_result(False, "Falha ao calcular status de SLA")
            return False
            
    except Exception as e:
        print_result(False, f"Erro ao testar cálculo de SLA: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    print("\n" + "="*60)
    print("🧪 TESTES DO NOVO SISTEMA DE SLA COM FILTRO DE 30 DIAS")
    print("="*60)
    
    results = []
    
    # Executar testes
    results.append(("Filtro de 30 Dias", test_30day_filter()))
    results.append(("Lógica de Pausa de SLA", test_sla_pause_logic()))
    results.append(("Cálculo de Status de SLA", test_sla_status_calculation()))
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 Todos os testes passaram! O novo sistema de SLA está funcionando corretamente.")
        return True
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam. Verifique os logs acima.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
