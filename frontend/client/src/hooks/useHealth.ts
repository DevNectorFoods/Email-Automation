import { useState, useEffect } from 'react';
import { healthAPI } from '@/lib/api';

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  version?: string;
  uptime?: number;
}

// Hook for health check
export const useHealth = () => {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await healthAPI.check();
      setHealthStatus(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check health status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return {
    healthStatus,
    loading,
    error,
    refetch: checkHealth,
  };
}; 