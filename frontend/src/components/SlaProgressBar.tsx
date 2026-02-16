/**
 * Componente SlaProgressBar
 * Exibe barra de progresso do SLA consumido
 * 
 * Características:
 * - Barra com cores (verde, amarelo, vermelho)
 * - Animação de preenchimento
 * - Label com percentual
 * - Suporte a diferentes tamanhos
 */

import React from 'react';
import { motion } from 'framer-motion';

interface SlaProgressBarProps {
  percentualConsumido: number;
  emRisco: boolean;
  vencido: boolean;
  height?: 'sm' | 'md' | 'lg';
  animated?: boolean;
  showLabel?: boolean;
}

export const SlaProgressBar: React.FC<SlaProgressBarProps> = ({
  percentualConsumido,
  emRisco,
  vencido,
  height = 'md',
  animated = true,
  showLabel = true
}) => {
  // Clampear o percentual entre 0 e 100
  const percent = Math.min(Math.max(percentualConsumido, 0), 100);

  // Determinar cor baseado no status
  const getColor = () => {
    if (vencido) return 'bg-red-600';
    if (emRisco) return 'bg-yellow-500';
    return 'bg-green-600';
  };

  const heightClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4'
  };

  const bgColor = getColor();

  return (
    <div className="w-full">
      <div className={`w-full ${heightClasses[height]} bg-gray-200 rounded-full overflow-hidden`}>
        <motion.div
          className={`${bgColor} h-full rounded-full`}
          initial={{ width: '0%' }}
          animate={{ width: `${percent}%` }}
          transition={animated ? { duration: 0.5, ease: 'easeOut' } : { duration: 0 }}
        />
      </div>
      {showLabel && (
        <div className="flex justify-between items-center mt-2">
          <span className="text-sm text-gray-600">
            {vencido ? '⚠️ Vencido' : emRisco ? '⚠️ Em Risco' : '✓ Dentro do SLA'}
          </span>
          <span className="text-sm font-medium text-gray-700">
            {percent.toFixed(1)}%
          </span>
        </div>
      )}
    </div>
  );
};

export default SlaProgressBar;
