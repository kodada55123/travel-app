import { config } from 'dotenv';
config();

export const ENV = {
  PORT: parseInt(process.env.PORT || '8080', 10),
  DATABASE_URL: process.env.DATABASE_URL || '',
  REDIS_URL: process.env.REDIS_URL || '',
  DUFFEL_API_KEY: process.env.DUFFEL_API_KEY || '',
  SERPAPI_KEY: process.env.SERPAPI_KEY || '',
  FIREBASE: {
    projectId: process.env.FIREBASE_PROJECT_ID || '',
    clientEmail: process.env.FIREBASE_CLIENT_EMAIL || '',
    privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n') || ''
  }
};
