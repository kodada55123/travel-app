import { Duffel } from '@duffel/api';
import { ENV } from '../config';
import { FlightSearchResult } from '../types';

const duffel = new Duffel({ token: ENV.DUFFEL_API_KEY });

const LCC_AIRLINES = new Set([
  'VJ', 'QH', 'MM', 'IT', '7C', 'TW', 'FD', 'SL', '5J', 'Z2', 'AK', 'D7', 'TR', '3K', 'UO', 'HX', 'K6'
]);

export async function searchDirectFlights(
  origin: string,
  destination: string,
  departDate: string,
  returnDate: string
): Promise<FlightSearchResult[]> {
  try {
    const offerRequest = await duffel.offerRequests.create({
      slices: [
        { origin, destination, departure_date: departDate },
        { origin: destination, destination: origin, departure_date: returnDate }
      ],
      passengers: [{ type: 'adult' }],
      cabin_class: 'economy',
      max_connections: 0
    });

    return offerRequest.data.offers.map(offer => {
      const slice1 = offer.slices[0];
      const slice2 = offer.slices[1];
      const airlineCode = offer.owner.iata_code || '';
      
      return {
        departure_date: departDate,
        return_date: returnDate,
        airline_name: offer.owner.name,
        airline_code: airlineCode,
        is_lcc: isLccAirline(airlineCode),
        price: parseFloat(offer.total_amount),
        currency: offer.total_currency,
        outbound_flight_no: slice1?.segments[0]?.operating_carrier_flight_number || '',
        return_flight_no: slice2?.segments[0]?.operating_carrier_flight_number || '',
        trip_days: Math.floor((new Date(returnDate).getTime() - new Date(departDate).getTime()) / (1000 * 3600 * 24)) + 1,
        is_direct: true,
        raw_data: offer
      };
    });
  } catch (error) {
    console.error('Duffel API error:', error);
    return [];
  }
}

export function isLccAirline(code: string): boolean {
  return LCC_AIRLINES.has(code.toUpperCase());
}
