import { FastifyInstance } from 'fastify';
import { query } from '../db';

export default async function (fastify: FastifyInstance) {
  fastify.post('/api/users/register', async (request, reply) => {
    const { email, timezone } = request.body as any;
    const { rows } = await query(
      'INSERT INTO users (email, timezone) VALUES ($1, $2) ON CONFLICT (email) DO UPDATE SET timezone = $2 RETURNING *',
      [email, timezone || 'UTC']
    );
    return rows[0];
  });

  fastify.post('/api/users/push-token', async (request, reply) => {
    const { userId, token, type } = request.body as any;
    const column = type === 'apns' ? 'apns_token' : 'fcm_token';
    await query(`UPDATE users SET ${column} = $1 WHERE id = $2`, [token, userId]);
    return { success: true };
  });

  fastify.get('/api/users/:id', async (request, reply) => {
    const { id } = request.params as any;
    const { rows } = await query('SELECT * FROM users WHERE id = $1', [id]);
    if (!rows.length) return reply.status(404).send({ error: 'Not found' });
    return rows[0];
  });
}
