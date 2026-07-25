export interface User {
  id: string;
  email: string;
  fcm_token?: string;
  apns_token?: string;
  timezone: string;
  created_at: Date;
}

export interface Destination {
  id: string;
  user_id: string;
  city_name: string;
  iata_code: string;
  origin_iata: string;
  is_active: boolean;
  created_at: Date;
}

export interface FlightSearchResult {
  departure_date: string;
  return_date: string;
  airline_name: string;
  airline_code: string;
  is_lcc: boolean;
  price: number;
  currency: string;
  outbound_flight_no: string;
  return_flight_no: string;
  trip_days: number;
  is_direct: boolean;
  raw_data?: any;
}
