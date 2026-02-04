"""
Serviço principal de SLA - VERSÃO CORRIGIDA
- Pausas funcionando com persistência no banco
- Cache de feriados
- Validações completas
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import time
import logging

from sqlalchemy.orm import Session

from .repository import SlaRepository
from .calculator import SlaCalculator
from .cache import sla_cache
from .schemas import (
    SlaDashboard, SlaDashboardResumo, SlaChamadoStatus,
    SlaConfigCreate, SlaConfigUpdate, RecalculoResponse,
    MudancaStatusResponse, PausasChamadoResponse, PausaResponse
)
from .constants import (
    is_status_pausado, is_status_finalizado, normalizar_status
)
from .exceptions import (
    ConfiguracaoDuplicadaError, FeriadoDuplicadoError,
    ChamadoNaoEncontradoError, ConfiguracaoNaoEncontradaError
)
from .config import settings

logger = logging.getLogger("sla.service")


class SlaService:
    """Serviço principal de SLA"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = SlaRepository(db)
        self._calculator: Optional[SlaCalculator] = None
    
    # ==================== Calculator com Cache ====================
    
    @property
    def calculator(self) -> SlaCalculator:
        """Calculator com cache de feriados"""
        if self._calculator is None:
            # Tenta cache primeiro
            feriados = sla_cache.get_feriados()
            
            if feriados is None:
                # Busca do banco
                feriados = self.repo.get_feriados_between(
                    datetime.now() - timedelta(days=365),
                    datetime.now() + timedelta(days=365)
                )
                sla_cache.set_feriados(feriados)
            
            self._calculator = SlaCalculator(feriados)
        
        return self._calculator
    
    def _get_configs_cached(self) -> Dict[str, Any]:
        """Retorna configs com cache"""
        configs = sla_cache.get_configs()
        
        if configs is None:
            configs = self.repo.get_configs_map()
            sla_cache.set_configs(configs)
        
        return configs
    
    def invalidar_cache(self) -> None:
        """Invalida todo o cache"""
        self._calculator = None
        sla_cache.invalidate_all()
        logger.info("[SLA] Cache invalidado")
    
    # ==================== Configurações ====================
    
    def get_configs(self) -> List:
        """Retorna todas as configurações de SLA"""
        return self.repo.get_all_configs()
    
    def create_config(self, data: SlaConfigCreate):
        """Cria nova configuração com validação de duplicata"""
        # Valida duplicata
        if self.repo.config_exists(data.prioridade):
            raise ConfiguracaoDuplicadaError(data.prioridade)
        
        config = self.repo.create_config(data.model_dump())
        sla_cache.invalidate_configs()
        
        logger.info(f"[SLA] Config criada: {data.prioridade}")
        return config
    
    def update_config(self, config_id: int, data: SlaConfigUpdate):
        """Atualiza configuração de SLA"""
        config = self.repo.update_config(config_id, data.model_dump(exclude_unset=True))
        
        if config:
            sla_cache.invalidate_configs()
            logger.info(f"[SLA] Config atualizada: {config.prioridade}")
        
        return config
    
    def delete_config(self, config_id: int) -> bool:
        """Remove (soft delete) configuração"""
        result = self.repo.delete_config(config_id)
        
        if result:
            sla_cache.invalidate_configs()
            logger.info(f"[SLA] Config removida: ID {config_id}")
        
        return result
    
    # ==================== Feriados ====================
    
    def get_feriados(self, ano: int = None) -> List:
        """Retorna feriados cadastrados"""
        return self.repo.get_feriados(ano)
    
    def create_feriado(self, data: Dict[str, Any]):
        """Cria novo feriado com validação"""
        # Valida duplicata
        if self.repo.feriado_exists(data['data']):
            raise FeriadoDuplicadoError(str(data['data']))
        
        feriado = self.repo.create_feriado(data)
        
        # Invalida cache para recarregar feriados
        self.invalidar_cache()
        
        logger.info(f"[SLA] Feriado criado: {data['nome']}")
        return feriado
    
    def delete_feriado(self, feriado_id: int) -> bool:
        """Remove feriado"""
        result = self.repo.delete_feriado(feriado_id)
        
        if result:
            self.invalidar_cache()
            logger.info(f"[SLA] Feriado removido: ID {feriado_id}")
        
        return result
    
    # ==================== Pausas ====================
    
    def get_pausas_chamado(self, chamado_id: int) -> PausasChamadoResponse:
        """Retorna todas as pausas de um chamado"""
        # Valida se chamado existe
        chamado = self.repo.get_chamado_by_id(chamado_id)
        if not chamado:
            raise ChamadoNaoEncontradoError(chamado_id)
        
        pausas = self.repo.get_pausas_chamado(chamado_id)
        tempo_total = self.repo.get_tempo_total_pausado(chamado_id)
        pausa_ativa = self.repo.get_pausa_ativa(chamado_id)
        
        return PausasChamadoResponse(
            chamado_id=chamado_id,
            total_pausas=len(pausas),
            pausas=[
                PausaResponse(
                    id=p.id,
                    chamado_id=p.chamado_id,
                    pausado_em=p.pausado_em,
                    retomado_em=p.retomado_em,
                    motivo=p.motivo or "Em análise",
                    duracao_minutos=p.duracao_minutos,
                    ativa=p.ativa
                )
                for p in pausas
            ],
            tempo_total_pausado_minutos=tempo_total,
            tempo_total_pausado_horas=round(tempo_total / 60, 2),
            pausa_ativa=pausa_ativa is not None
        )
    
    # ==================== Mudança de Status ====================
    
    def registrar_mudanca_status(
        self,
        chamado_id: int,
        status_anterior: str,
        status_novo: str,
        usuario_id: int = None
    ) -> MudancaStatusResponse:
        """
        Gerencia pausa do SLA quando status muda.
        
        CORRIGIDO: Agora persiste pausas no banco!
        """
        # Normaliza status
        status_ant_norm = normalizar_status(status_anterior)
        status_novo_norm = normalizar_status(status_novo)
        
        acao = None
        pausa_id = None
        tempo_pausado = None
        
        era_pausado = is_status_pausado(status_anterior)
        vai_pausar = is_status_pausado(status_novo)
        
        # CASO 1: Entrou em análise → CRIAR PAUSA
        if vai_pausar and not era_pausado:
            pausa = self.repo.criar_pausa(
                chamado_id=chamado_id,
                motivo=status_novo,
                usuario_id=usuario_id
            )
            
            pausa_id = pausa.id
            acao = "pausado"
            
            logger.info(
                f"[SLA] Chamado {chamado_id} PAUSADO | "
                f"Pausa ID: {pausa_id} | Motivo: {status_novo}"
            )
        
        # CASO 2: Saiu de análise → FINALIZAR PAUSA
        elif era_pausado and not vai_pausar:
            pausa = self.repo.finalizar_pausa(chamado_id)
            
            if pausa:
                pausa_id = pausa.id
                tempo_pausado = pausa.duracao_minutos
                acao = "retomado"
                
                logger.info(
                    f"[SLA] Chamado {chamado_id} RETOMADO | "
                    f"Tempo pausado: {tempo_pausado}min"
                )
            
            # Recalcula SLA imediatamente
            self._recalcular_chamado_interno(chamado_id)
        
        # Monta mensagem
        if acao == "pausado":
            mensagem = f"SLA pausado. Aguardando: {status_novo}"
        elif acao == "retomado":
            mensagem = f"SLA retomado após {tempo_pausado or 0} minutos"
        else:
            mensagem = "Status atualizado. SLA não afetado."
        
        return MudancaStatusResponse(
            chamado_id=chamado_id,
            status_anterior=status_anterior,
            status_novo=status_novo,
            status_anterior_normalizado=status_ant_norm,
            status_novo_normalizado=status_novo_norm,
            acao_sla=acao,
            pausa_id=pausa_id,
            tempo_pausado_minutos=tempo_pausado,
            mensagem=mensagem
        )
    
    def _recalcular_chamado_interno(self, chamado_id: int) -> bool:
        """Recalcula SLA de um chamado específico (interno)"""
        chamado = self.repo.get_chamado_by_id(chamado_id)
        if not chamado:
            return False
        
        if is_status_finalizado(chamado.status):
            return False
        
        configs = self._get_configs_cached()
        prioridade = chamado.prioridade.lower() if chamado.prioridade else "media"
        config = configs.get(prioridade) or configs.get("media")
        
        if not config:
            logger.warning(f"[SLA] Sem config para prioridade: {prioridade}")
            return False
        
        # Busca pausas do banco
        pausas = self.repo.get_pausas_para_calculo(chamado_id)
        
        # Calcula status
        status_sla = self.calculator.calcular_status_sla(
            chamado.data_abertura,
            config.tempo_resolucao_horas,
            pausas
        )
        
        # Atualiza no banco
        self.repo.update_chamado_sla(
            chamado_id,
            em_risco=status_sla["em_risco"],
            vencido=status_sla["vencido"],
            tempo_decorrido=status_sla["tempo_decorrido_horas"],
            tempo_pausado=status_sla["tempo_pausado_horas"],
            percentual=status_sla["percentual_consumido"]
        )
        
        return True
    
    # ==================== Dashboard ====================
    
    def get_dashboard(
        self,
        data_inicio: datetime = None,
        data_fim: datetime = None,
        prioridade: str = None
    ) -> SlaDashboard:
        """Gera dashboard completo de SLA"""
        
        # Período padrão: últimos 30 dias
        if not data_fim:
            data_fim = datetime.now()
        if not data_inicio:
            data_inicio = data_fim - timedelta(days=30)
        
        # Validação
        if data_inicio > data_fim:
            data_inicio, data_fim = data_fim, data_inicio
        
        # Busca dados
        chamados = self.repo.get_chamados_periodo(data_inicio, data_fim, prioridade)
        configs = self._get_configs_cached()
        
        # Contadores
        total = len(chamados)
        total_ativos = 0
        total_concluidos = 0
        
        dentro_sla_resposta = 0
        fora_sla_resposta = 0
        dentro_sla_resolucao = 0
        fora_sla_resolucao = 0
        
        tempos_resposta: List[float] = []
        tempos_resolucao: List[float] = []
        
        lista_em_risco: List[SlaChamadoStatus] = []
        lista_vencidos: List[SlaChamadoStatus] = []
        lista_pausados: List[SlaChamadoStatus] = []
        
        for chamado in chamados:
            # Config da prioridade
            prioridade_chamado = chamado.prioridade.lower() if chamado.prioridade else "media"
            config = configs.get(prioridade_chamado) or configs.get("media")
            
            if not config:
                continue
            
            # ✅ CORREÇÃO: Busca pausas REAIS do banco
            pausas = self.repo.get_pausas_para_calculo(chamado.id)
            
            # Status
            status_norm = normalizar_status(chamado.status)
            is_finalizado = is_status_finalizado(chamado.status)
            is_pausado = is_status_pausado(chamado.status)
            
            if is_finalizado:
                total_concluidos += 1
            else:
                total_ativos += 1
            
            # === SLA de Resposta ===
            if chamado.data_primeira_resposta:
                tempo_resposta = self.calculator.calcular_horas_uteis(
                    chamado.data_abertura,
                    chamado.data_primeira_resposta
                )
                tempos_resposta.append(tempo_resposta)
                
                if tempo_resposta <= config.tempo_resposta_horas:
                    dentro_sla_resposta += 1
                else:
                    fora_sla_resposta += 1
            
            # === SLA de Resolução ===
            if chamado.data_conclusao:
                # ✅ CORREÇÃO: Usa pausas reais no cálculo
                tempo_decorrido, tempo_pausado = self.calculator.calcular_horas_uteis_com_pausas(
                    chamado.data_abertura,
                    chamado.data_conclusao,
                    pausas
                )
                tempos_resolucao.append(tempo_decorrido)
                
                if tempo_decorrido <= config.tempo_resolucao_horas:
                    dentro_sla_resolucao += 1
                else:
                    fora_sla_resolucao += 1
            
            # === Chamados ativos ===
            elif not is_finalizado:
                # ✅ CORREÇÃO: Usa pausas reais no cálculo
                status_sla = self.calculator.calcular_status_sla(
                    chamado.data_abertura,
                    config.tempo_resolucao_horas,
                    pausas
                )
                
                chamado_status = SlaChamadoStatus(
                    chamado_id=chamado.id,
                    codigo=chamado.codigo or str(chamado.id),
                    protocolo=chamado.protocolo,
                    prioridade=chamado.prioridade or "media",
                    status=chamado.status,
                    status_normalizado=status_norm,
                    solicitante=chamado.solicitante,
                    unidade=chamado.unidade,
                    problema=chamado.problema,
                    data_abertura=chamado.data_abertura,
                    tempo_limite_horas=config.tempo_resolucao_horas,
                    tempo_decorrido_horas=status_sla["tempo_decorrido_horas"],
                    tempo_pausado_horas=status_sla["tempo_pausado_horas"],
                    tempo_restante_horas=status_sla["tempo_restante_horas"],
                    percentual_consumido=status_sla["percentual_consumido"],
                    em_risco=status_sla["em_risco"],
                    vencido=status_sla["vencido"],
                    pausado=is_pausado,
                    prazo_limite=status_sla["prazo_limite"]
                )
                
                # Classifica
                if is_pausado:
                    lista_pausados.append(chamado_status)
                elif status_sla["vencido"]:
                    lista_vencidos.append(chamado_status)
                elif status_sla["em_risco"]:
                    lista_em_risco.append(chamado_status)
        
        # Médias
        tempo_medio_resposta = (
            sum(tempos_resposta) / len(tempos_resposta)
            if tempos_resposta else 0
        )
        tempo_medio_resolucao = (
            sum(tempos_resolucao) / len(tempos_resolucao)
            if tempos_resolucao else 0
        )
        
        # Percentuais
        total_com_resposta = dentro_sla_resposta + fora_sla_resposta
        total_resolvidos = dentro_sla_resolucao + fora_sla_resolucao
        
        percentual_sla_resposta = (
            (dentro_sla_resposta / total_com_resposta * 100)
            if total_com_resposta > 0 else 100
        )
        percentual_sla_resolucao = (
            (dentro_sla_resolucao / total_resolvidos * 100)
            if total_resolvidos > 0 else 100
        )
        
        # Próximo recálculo
        ultimo_calculo = self.repo.get_ultimo_calculo()
        proximo_recalculo = None
        if ultimo_calculo and ultimo_calculo.last_calculated_at:
            proximo_recalculo = ultimo_calculo.last_calculated_at + timedelta(
                minutes=settings.SLA_RECALC_INTERVAL_MINUTES
            )
        
        # Ordena por urgência
        lista_em_risco.sort(key=lambda x: x.percentual_consumido, reverse=True)
        lista_vencidos.sort(key=lambda x: x.percentual_consumido, reverse=True)
        
        return SlaDashboard(
            periodo_inicio=data_inicio,
            periodo_fim=data_fim,
            total_chamados=total,
            total_chamados_ativos=total_ativos,
            total_chamados_concluidos=total_concluidos,
            dentro_sla_resposta=dentro_sla_resposta,
            fora_sla_resposta=fora_sla_resposta,
            percentual_sla_resposta=round(percentual_sla_resposta, 2),
            tempo_medio_resposta_horas=round(tempo_medio_resposta, 2),
            dentro_sla_resolucao=dentro_sla_resolucao,
            fora_sla_resolucao=fora_sla_resolucao,
            percentual_sla_resolucao=round(percentual_sla_resolucao, 2),
            tempo_medio_resolucao_horas=round(tempo_medio_resolucao, 2),
            chamados_em_risco=len(lista_em_risco),
            chamados_vencidos=len(lista_vencidos),
            chamados_pausados=len(lista_pausados),
            lista_em_risco=lista_em_risco,
            lista_vencidos=lista_vencidos,
            lista_pausados=lista_pausados,
            ultima_atualizacao=datetime.now(),
            proximo_recalculo=proximo_recalculo
        )
    
    def get_dashboard_resumo(self) -> SlaDashboardResumo:
        """Versão resumida para widgets"""
        dashboard = self.get_dashboard()
        return SlaDashboardResumo(
            percentual_sla_resposta=dashboard.percentual_sla_resposta,
            percentual_sla_resolucao=dashboard.percentual_sla_resolucao,
            chamados_em_risco=dashboard.chamados_em_risco,
            chamados_vencidos=dashboard.chamados_vencidos,
            chamados_pausados=dashboard.chamados_pausados,
            tempo_medio_resposta_horas=dashboard.tempo_medio_resposta_horas,
            tempo_medio_resolucao_horas=dashboard.tempo_medio_resolucao_horas,
            ultima_atualizacao=dashboard.ultima_atualizacao
        )
    
    # ==================== Recálculo ====================
    
    def recalcular_todos_chamados(self) -> RecalculoResponse:
        """
        Recalcula SLA de todos os chamados ativos abertos nos últimos 30 dias.

        O sistema considera apenas chamados abertos há no máximo 30 dias para
        otimizar performance e focar em chamados relevantes.
        """
        start_time = time.time()

        try:
            chamados = self.repo.get_chamados_ativos(dias_atras=settings.SLA_CALCULO_DIAS_ATRAS)
            configs = self._get_configs_cached()
            
            processados = 0
            atualizados = 0
            em_risco = 0
            vencidos = 0
            pausados = 0
            last_id = None
            
            for chamado in chamados:
                processados += 1
                last_id = chamado.id
                
                # Config
                prioridade = chamado.prioridade.lower() if chamado.prioridade else "media"
                config = configs.get(prioridade) or configs.get("media")
                
                if not config:
                    continue
                
                # Se pausado, apenas conta
                if is_status_pausado(chamado.status):
                    pausados += 1
                    continue
                
                # ✅ CORREÇÃO: Busca pausas reais
                pausas = self.repo.get_pausas_para_calculo(chamado.id)
                
                # Calcula
                status_sla = self.calculator.calcular_status_sla(
                    chamado.data_abertura,
                    config.tempo_resolucao_horas,
                    pausas
                )
                
                # Atualiza
                self.repo.update_chamado_sla(
                    chamado.id,
                    em_risco=status_sla["em_risco"],
                    vencido=status_sla["vencido"],
                    tempo_decorrido=status_sla["tempo_decorrido_horas"],
                    tempo_pausado=status_sla["tempo_pausado_horas"],
                    percentual=status_sla["percentual_consumido"]
                )
                
                atualizados += 1
                
                if status_sla["vencido"]:
                    vencidos += 1
                elif status_sla["em_risco"]:
                    em_risco += 1
            
            execution_time = (time.time() - start_time) * 1000
            
            # Log
            self.repo.log_calculation(
                calc_type="recalculo_automatico",
                chamados_count=processados,
                em_risco=em_risco,
                vencidos=vencidos,
                pausados=pausados,
                execution_time=execution_time,
                success=True,
                last_chamado_id=last_id
            )
            
            logger.info(
                f"[SLA] Recálculo OK: {atualizados} atualizados, "
                f"{em_risco} em risco, {vencidos} vencidos, "
                f"{pausados} pausados ({execution_time:.2f}ms)"
            )
            
            return RecalculoResponse(
                sucesso=True,
                chamados_processados=processados,
                chamados_atualizados=atualizados,
                chamados_em_risco=em_risco,
                chamados_vencidos=vencidos,
                chamados_pausados=pausados,
                tempo_execucao_ms=round(execution_time, 2),
                timestamp=datetime.now()
            )
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            self.repo.log_calculation(
                calc_type="recalculo_automatico",
                chamados_count=0,
                execution_time=execution_time,
                success=False,
                error_message=error_msg
            )
            
            logger.error(f"[SLA] Erro no recálculo: {error_msg}")
            
            return RecalculoResponse(
                sucesso=False,
                chamados_processados=0,
                chamados_atualizados=0,
                chamados_em_risco=0,
                chamados_vencidos=0,
                chamados_pausados=0,
                tempo_execucao_ms=round(execution_time, 2),
                timestamp=datetime.now(),
                erro=error_msg
            )
    
    # ==================== Chamado Individual ====================
    
    def get_sla_chamado(self, chamado_id: int) -> Optional[SlaChamadoStatus]:
        """Retorna status SLA de um chamado"""
        chamado = self.repo.get_chamado_by_id(chamado_id)
        if not chamado:
            return None
        
        configs = self._get_configs_cached()
        prioridade = chamado.prioridade.lower() if chamado.prioridade else "media"
        config = configs.get(prioridade) or configs.get("media")
        
        if not config:
            raise ConfiguracaoNaoEncontradaError(prioridade)
        
        # ✅ CORREÇÃO: Busca pausas reais
        pausas = self.repo.get_pausas_para_calculo(chamado_id)
        
        status_norm = normalizar_status(chamado.status)
        is_pausado = is_status_pausado(chamado.status)
        
        status_sla = self.calculator.calcular_status_sla(
            chamado.data_abertura,
            config.tempo_resolucao_horas,
            pausas
        )
        
        return SlaChamadoStatus(
            chamado_id=chamado.id,
            codigo=chamado.codigo or str(chamado.id),
            protocolo=chamado.protocolo,
            prioridade=chamado.prioridade or "media",
            status=chamado.status,
            status_normalizado=status_norm,
            solicitante=chamado.solicitante,
            unidade=chamado.unidade,
            problema=chamado.problema,
            data_abertura=chamado.data_abertura,
            tempo_limite_horas=config.tempo_resolucao_horas,
            tempo_decorrido_horas=status_sla["tempo_decorrido_horas"],
            tempo_pausado_horas=status_sla["tempo_pausado_horas"],
            tempo_restante_horas=status_sla["tempo_restante_horas"],
            percentual_consumido=status_sla["percentual_consumido"],
            em_risco=status_sla["em_risco"],
            vencido=status_sla["vencido"],
            pausado=is_pausado,
            prazo_limite=status_sla["prazo_limite"]
        )
    
    # ==================== Cache Status ====================
    
    def get_cache_status(self) -> Dict:
        """Retorna status do cache"""
        return sla_cache.get_status()
