"""Cache para feriados e configurações"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

from .config import settings

logger = logging.getLogger("sla.cache")


class SlaCache:
    """Cache simples para dados de SLA"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_cache()
        return cls._instance
    
    def _init_cache(self):
        """Inicializa estruturas do cache"""
        self._feriados: Optional[List] = None
        self._feriados_timestamp: Optional[datetime] = None
        self._configs: Optional[Dict] = None
        self._configs_timestamp: Optional[datetime] = None
        self._ttl = timedelta(minutes=settings.CACHE_TTL_MINUTES)
    
    def _is_valid(self, timestamp: Optional[datetime]) -> bool:
        """Verifica se o cache ainda é válido"""
        if timestamp is None:
            return False
        return datetime.now() - timestamp < self._ttl
    
    # ========== Feriados ==========
    
    def get_feriados(self) -> Optional[List]:
        """Retorna feriados do cache se válido"""
        if self._is_valid(self._feriados_timestamp):
            return self._feriados
        return None
    
    def set_feriados(self, feriados: List) -> None:
        """Armazena feriados no cache"""
        self._feriados = feriados
        self._feriados_timestamp = datetime.now()
        logger.debug(f"Cache de feriados atualizado: {len(feriados)} registros")
    
    def invalidate_feriados(self) -> None:
        """Invalida cache de feriados"""
        self._feriados = None
        self._feriados_timestamp = None
        logger.debug("Cache de feriados invalidado")
    
    # ========== Configs ==========
    
    def get_configs(self) -> Optional[Dict]:
        """Retorna configs do cache se válido"""
        if self._is_valid(self._configs_timestamp):
            return self._configs
        return None
    
    def set_configs(self, configs: Dict) -> None:
        """Armazena configs no cache"""
        self._configs = configs
        self._configs_timestamp = datetime.now()
        logger.debug(f"Cache de configs atualizado: {len(configs)} registros")
    
    def invalidate_configs(self) -> None:
        """Invalida cache de configs"""
        self._configs = None
        self._configs_timestamp = None
        logger.debug("Cache de configs invalidado")
    
    # ========== Geral ==========
    
    def invalidate_all(self) -> None:
        """Invalida todo o cache"""
        self.invalidate_feriados()
        self.invalidate_configs()
        logger.info("Cache completamente invalidado")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do cache"""
        return {
            "feriados": {
                "cached": self._feriados is not None,
                "count": len(self._feriados) if self._feriados else 0,
                "valid": self._is_valid(self._feriados_timestamp),
                "updated_at": self._feriados_timestamp.isoformat() if self._feriados_timestamp else None
            },
            "configs": {
                "cached": self._configs is not None,
                "count": len(self._configs) if self._configs else 0,
                "valid": self._is_valid(self._configs_timestamp),
                "updated_at": self._configs_timestamp.isoformat() if self._configs_timestamp else None
            },
            "ttl_minutes": settings.CACHE_TTL_MINUTES
        }


# Instância global do cache
sla_cache = SlaCache()
