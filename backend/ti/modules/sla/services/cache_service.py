"""
Serviço de cache para métricas de SLA.

Gerencia:
- Cache de métricas calculadas
- Expiração automática
- Recalculamento quando expirado
"""

import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ti.models import MetricsCacheDB

class CacheService:
    def __init__(self, db: Session):
        self.db = db
    
    def salvar(self, chave: str, valor: dict, ttl_minutos: int = 30) -> None:
        """
        Salva um valor em cache.
        
        Args:
            chave: Chave única do cache
            valor: Valor a cachear (será serializado para JSON)
            ttl_minutos: Tempo de vida do cache em minutos
        """
        cache = self.db.query(MetricsCacheDB).filter(
            MetricsCacheDB.cache_key == chave
        ).first()
        
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutos)
        cache_value = json.dumps(valor)
        
        if cache:
            cache.cache_value = cache_value
            cache.calculated_at = datetime.utcnow()
            cache.expires_at = expires_at
        else:
            cache = MetricsCacheDB(
                cache_key=chave,
                cache_value=cache_value,
                calculated_at=datetime.utcnow(),
                expires_at=expires_at
            )
            self.db.add(cache)
        
        self.db.commit()
    
    def obter(self, chave: str) -> dict | None:
        """
        Obtém um valor do cache se ainda estiver válido.
        
        Args:
            chave: Chave do cache
        
        Returns:
            Valor do cache ou None se não existir ou tiver expirado
        """
        cache = self.db.query(MetricsCacheDB).filter(
            MetricsCacheDB.cache_key == chave
        ).first()
        
        if not cache:
            return None
        
        # Verifica expiração
        if cache.expires_at and cache.expires_at < datetime.utcnow():
            return None  # Cache expirado
        
        # Retorna valor
        try:
            return json.loads(cache.cache_value)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def limpar(self, chave: str = None) -> None:
        """
        Limpa o cache (específico ou tudo).
        
        Args:
            chave: Chave específica ou None para limpar tudo
        """
        if chave:
            self.db.query(MetricsCacheDB).filter(
                MetricsCacheDB.cache_key == chave
            ).delete()
        else:
            self.db.query(MetricsCacheDB).delete()
        
        self.db.commit()
    
    def limpar_expirados(self) -> int:
        """
        Remove entradas de cache que expiraram.
        
        Returns:
            Número de registros removidos
        """
        agora = datetime.utcnow()
        resultado = self.db.query(MetricsCacheDB).filter(
            MetricsCacheDB.expires_at < agora
        ).delete()
        self.db.commit()
        return resultado
