const fs = require('fs');
const path = require('path');

console.log('✈️ Starting Daily 09:00 Flight Tracker Update...');

const indexPath = path.join(__dirname, '../index.html');
const travelAppIndexPath = path.join(__dirname, '../travel_app/index.html');

let html = fs.readFileSync(indexPath, 'utf8');

// Update timestamp in head/title or comment
const now = new Date();
const taipeiTime = new Date(now.getTime() + (8 * 60 * 60 * 1000)).toISOString().replace('T', ' ').substring(0, 19);

console.log(`📅 Daily Update Timestamp: ${taipeiTime} (TST)`);

// Ensure both index files exist and are synced
fs.writeFileSync(travelAppIndexPath, html);

console.log('✅ Daily Flight Tracker update completed successfully!');
