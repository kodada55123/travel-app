const fs = require('fs');
const path = require('path');

console.log('✈️ Preparing verified flight tracker for deployment...');

const indexPath = path.join(__dirname, '../index.html');
const travelAppIndexPath = path.join(__dirname, '../travel_app/index.html');

const html = fs.readFileSync(travelAppIndexPath, 'utf8');

fs.writeFileSync(indexPath, html);

console.log('✅ Verified flight tracker prepared successfully!');
