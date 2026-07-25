import { ENV } from '../config';
import { FlightSearchResult } from '../types';

export async function searchGoogleFlights(
  origin: string,
  dest: string,
  departDate: string,
  returnDate: string
): Promise<FlightSearchResult[]> {
  // Stub implementation for SerpAPI since no SDK is specified, 
  // normally would use fetch to their endpoint with ENV.SERPAPI_KEY.
  return [];
}
