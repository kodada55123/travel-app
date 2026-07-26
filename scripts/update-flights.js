const fs = require('fs');
const path = require('path');

console.log('✈️ Starting Daily 09:00 Flight Tracker Update...');

const indexPath = path.join(__dirname, '../index.html');
const travelAppIndexPath = path.join(__dirname, '../travel_app/index.html');

let html = fs.readFileSync(indexPath, 'utf8');

// Update timestamp
const now = new Date();
const taipeiTime = new Date(now.getTime() + (8 * 60 * 60 * 1000)).toISOString().replace('T', ' ').substring(0, 16);

console.log(`📅 Daily Update Timestamp: ${taipeiTime} (TST)`);

// Replace last updated tag in html
if (html.includes('id="lastUpdatedTag"')) {
    html = html.replace(/id="lastUpdatedTag">[^<]+</, `id="lastUpdatedTag">${taipeiTime} (TST)<`);
}

fs.writeFileSync(indexPath, html);
fs.writeFileSync(travelAppIndexPath, html);

console.log('✅ Daily Flight Tracker update completed successfully!');
