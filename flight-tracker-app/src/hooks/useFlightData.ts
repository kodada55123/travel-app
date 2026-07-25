import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

export function useFlightData() {
  const [destinations, setDestinations] = useState<any[]>([]);
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const dests = await apiClient.getDestinations();
        const rep = await apiClient.getFlightReport();
        setDestinations(dests);
        setReport(rep);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  return { destinations, report, loading };
}
