import { Queue } from 'bullmq';
import { ENV } from '../config';
import IORedis from 'ioredis';

const connection = new IORedis(ENV.REDIS_URL, { maxRetriesPerRequest: null });

export const flightQueue = new Queue('flight-search', {
  connection,
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 1000,
    },
  },
});
