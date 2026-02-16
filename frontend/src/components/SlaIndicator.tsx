/**
 * Componente SlaIndicator
 * Exibe status e percentual de SLA consumido
 * 
 * Características:
 * - Exibe ícone e texto de status (Dentro/Risco/Vencido)
 * - Mostra percentual consumido
 * - Cores: Verde (dentro), Amarelo (risco), Vermelho (vencido)
 */

import React from 'react';
import { AlertCircle, CheckCircle2, Clock } from 'lucide-react';

interface SlaIndicatorProps {
  percentualConsumido: number;
  emRisco: boolean;
  vencido: boolean;
  showPercentage?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const SlaIndicator: React.FC<SlaIndicatorProps> = ({
  percentualConsumido,
  emRisco,
  vencido,
  showPercentage = true,
  size = 'md'
}) => {
  const getStatus = () => {
    if (vencido) return { status: 'Vencido', color: 'text-red-600', bgColor: 'bg-red-50', icon: AlertCircle };
    if (emRisco) return { status: 'Em Risco', color: 'text-yellow-600', bgColor: 'bg-yellow-50', icon: Clock };
    return { status: 'Dentro', color: 'text-green-600', bgColor: 'bg-green-50', icon: CheckCircle2 };
  };

  const { status, color, bgColor, icon: Icon } = getStatus();

  const sizeClasses = {
    sm: 'w-4 h-4 text-xs gap-1',
    md: 'w-5 h-5 text-sm gap-2',
    lg: 'w-6 h-6 text-base gap-2'
  };

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${bgColor}`}>
      <Icon className={`${sizeClasses[size].split(' ')[0]} ${sizeClasses[size].split(' ')[1]} ${color}`} />
      <div className="flex flex-col">
        <span className={`font-medium ${color} ${sizeClasses[size].split(' ')[2]}`}>
          {status}
        </span>
        {showPercentage && (
          <span className={`text-gray-600 ${size === 'sm' ? 'text-xs' : 'text-sm'}`}>
            {percentualConsumido.toFixed(1)}% consumido
          </span>
        )}
      </div>
    </div>
  );
};

export default SlaIndicator;
