import cron from 'node-cron';
import { query } from '../db';
import { generateValidDatePairs } from '../services/dateHelper';
import { flightQueue } from '../queues/flightQueue';

export function startCron() {
  // Run every day at 06:00 Asia/Taipei
  cron.schedule('0 6 * * *', async () => {
    console.log('Starting daily flight tracker cron...');
    
    try {
      const { rows: destinations } = await query('SELECT * FROM destinations WHERE is_active = true');
      const today = new Date();
      const datePairs = generateValidDatePairs(today);

      for (const dest of destinations) {
        for (const pair of datePairs) {
          await flightQueue.add('search', {
            destinationId: dest.id,
            origin: dest.origin_iata,
            dest: dest.iata_code,
            departDate: pair.departDate,
            returnDate: pair.returnDate
          });
        }
      }
    } catch (error) {
      console.error('Cron Error:', error);
    }
  }, {
    timezone: 'Asia/Taipei'
  });
}
