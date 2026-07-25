import { Worker } from 'bullmq';
import IORedis from 'ioredis';
import { ENV } from '../config';
import { searchDirectFlights } from '../services/duffelService';
import { searchGoogleFlights } from '../services/serpApiService';
import { detectLccAvailability } from '../services/lccDetector';
import { query } from '../db';

const connection = new IORedis(ENV.REDIS_URL, { maxRetriesPerRequest: null });

export const worker = new Worker('flight-search', async job => {
  const { destinationId, origin, dest, departDate, returnDate } = job.data;
  
  // Rate limited searches
  const duffelResults = await searchDirectFlights(origin, dest, departDate, returnDate);
  const serpResults = await searchGoogleFlights(origin, dest, departDate, returnDate);

  const allResults = [...duffelResults, ...serpResults];
  
  for (const res of allResults) {
    await query(
      `INSERT INTO flight_prices 
       (destination_id, departure_date, return_date, airline_name, airline_code, is_lcc, price, currency, outbound_flight_no, return_flight_no, trip_days, is_direct, raw_data)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)`,
      [
        destinationId, res.departure_date, res.return_date, res.airline_name, 
        res.airline_code, res.is_lcc, res.price, res.currency, 
        res.outbound_flight_no, res.return_flight_no, res.trip_days, res.is_direct, res.raw_data
      ]
    );
  }

  await detectLccAvailability(origin, dest, departDate);
  
}, { connection });

worker.on('failed', (job, err) => {
  console.error(`Job ${job?.id} failed with error ${err.message}`);
});
