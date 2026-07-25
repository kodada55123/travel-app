import Fastify from 'fastify';
import cors from '@fastify/cors';
import { ENV } from './config';
import routes from './routes';
import { startCron } from './cron/dailyTracker';
import './queues/flightWorker';

const fastify = Fastify({ logger: true });

async function start() {
  try {
    await fastify.register(cors);
    await fastify.register(routes);

    startCron();

    await fastify.listen({ port: ENV.PORT, host: '0.0.0.0' });
    console.log(`Server listening on port ${ENV.PORT}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
}

start();
