import { Pool } from 'pg';
import { ENV } from '../config';

export const pool = new Pool({
  connectionString: ENV.DATABASE_URL
});

export const query = (text: string, params?: any[]) => {
  return pool.query(text, params);
};
