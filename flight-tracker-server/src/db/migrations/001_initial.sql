CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  fcm_token TEXT,
  apns_token TEXT,
  timezone VARCHAR(50) DEFAULT 'UTC',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS destinations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  city_name VARCHAR(255) NOT NULL,
  iata_code VARCHAR(10) NOT NULL,
  origin_iata VARCHAR(10) NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS flight_prices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  destination_id UUID REFERENCES destinations(id) ON DELETE CASCADE,
  departure_date DATE NOT NULL,
  return_date DATE NOT NULL,
  airline_name VARCHAR(255) NOT NULL,
  airline_code VARCHAR(10) NOT NULL,
  is_lcc BOOLEAN DEFAULT FALSE,
  price DECIMAL(10,2) NOT NULL,
  currency VARCHAR(3) NOT NULL,
  outbound_flight_no VARCHAR(20),
  return_flight_no VARCHAR(20),
  trip_days INTEGER NOT NULL,
  is_direct BOOLEAN DEFAULT TRUE,
  raw_data JSONB,
  fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS price_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  destination_id UUID REFERENCES destinations(id) ON DELETE CASCADE,
  alert_type VARCHAR(50) NOT NULL,
  message TEXT NOT NULL,
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lcc_availability (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  origin_iata VARCHAR(10) NOT NULL,
  dest_iata VARCHAR(10) NOT NULL,
  airline_code VARCHAR(10) NOT NULL,
  airline_name VARCHAR(255) NOT NULL,
  check_date DATE NOT NULL,
  months_ahead INTEGER NOT NULL,
  has_flights BOOLEAN NOT NULL,
  checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_destinations_user_id ON destinations(user_id);
CREATE INDEX idx_flight_prices_destination_id ON flight_prices(destination_id);
CREATE INDEX idx_price_alerts_user_id ON price_alerts(user_id);
CREATE INDEX idx_lcc_availability_route ON lcc_availability(origin_iata, dest_iata);
