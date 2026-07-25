import { FastifyInstance } from 'fastify';
import { query } from '../db';

export default async function (fastify: FastifyInstance) {
  fastify.get('/api/flights/report/:userId', async (request, reply) => {
    // Complex report query
    const { userId } = request.params as any;
    const { rows } = await query(
      `SELECT d.city_name, f.* 
       FROM destinations d
       JOIN flight_prices f ON d.id = f.destination_id
       WHERE d.user_id = $1
       ORDER BY f.price ASC LIMIT 100`,
      [userId]
    );
    return rows;
  });

  fastify.get('/api/flights/cheapest/:destinationId', async (request, reply) => {
    const { destinationId } = request.params as any;
    const { rows } = await query(
      `SELECT * FROM flight_prices WHERE destination_id = $1 ORDER BY price ASC LIMIT 10`,
      [destinationId]
    );
    return rows;
  });

  fastify.get('/api/flights/calendar/:destinationId', async (request, reply) => {
    const { destinationId } = request.params as any;
    const { rows } = await query(
      `SELECT departure_date, MIN(price) as min_price 
       FROM flight_prices 
       WHERE destination_id = $1 
       GROUP BY departure_date`,
      [destinationId]
    );
    return rows;
  });

  fastify.get('/api/flights/lcc-status/:destinationId', async (request, reply) => {
    const { destinationId } = request.params as any;
    const { rows: dests } = await query('SELECT * FROM destinations WHERE id = $1', [destinationId]);
    if (!dests.length) return reply.status(404).send();
    
    const { rows } = await query(
      `SELECT * FROM lcc_availability WHERE origin_iata = $1 AND dest_iata = $2`,
      [dests[0].origin_iata, dests[0].iata_code]
    );
    return rows;
  });
}
