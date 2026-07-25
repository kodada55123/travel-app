import { FastifyInstance } from 'fastify';
import userRoutes from './users';
import destinationRoutes from './destinations';
import flightRoutes from './flights';

export default async function (fastify: FastifyInstance) {
  fastify.register(userRoutes);
  fastify.register(destinationRoutes);
  fastify.register(flightRoutes);
}
