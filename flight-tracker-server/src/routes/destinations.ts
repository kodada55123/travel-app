import { FastifyInstance } from 'fastify';
import { query } from '../db';

export default async function (fastify: FastifyInstance) {
  fastify.get('/api/destinations/:userId', async (request, reply) => {
    const { userId } = request.params as any;
    const { rows } = await query('SELECT * FROM destinations WHERE user_id = $1', [userId]);
    return rows;
  });

  fastify.post('/api/destinations', async (request, reply) => {
    const { userId, cityName, iataCode, originIata } = request.body as any;
    const { rows } = await query(
      'INSERT INTO destinations (user_id, city_name, iata_code, origin_iata) VALUES ($1, $2, $3, $4) RETURNING *',
      [userId, cityName, iataCode, originIata]
    );
    return rows[0];
  });

  fastify.delete('/api/destinations/:id', async (request, reply) => {
    const { id } = request.params as any;
    await query('DELETE FROM destinations WHERE id = $1', [id]);
    return { success: true };
  });

  fastify.put('/api/destinations/:id/toggle', async (request, reply) => {
    const { id } = request.params as any;
    const { rows } = await query('UPDATE destinations SET is_active = NOT is_active WHERE id = $1 RETURNING *', [id]);
    return rows[0];
  });
}
