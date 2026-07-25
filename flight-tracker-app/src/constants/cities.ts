export interface City {
  id: string;
  name: string;
  nameEn: string;
  iata: string;
  country: string;
  flag: string;
  region: string;
}

export const CITIES: City[] = [
  { id: '1', name: '東京', nameEn: 'Tokyo', iata: 'NRT', country: 'Japan', flag: '🇯🇵', region: 'East Asia' },
  { id: '2', name: '大阪', nameEn: 'Osaka', iata: 'KIX', country: 'Japan', flag: '🇯🇵', region: 'East Asia' },
  { id: '3', name: '首爾', nameEn: 'Seoul', iata: 'ICN', country: 'South Korea', flag: '🇰🇷', region: 'East Asia' },
  { id: '4', name: '曼谷', nameEn: 'Bangkok', iata: 'BKK', country: 'Thailand', flag: '🇹🇭', region: 'Southeast Asia' },
  { id: '5', name: '新加坡', nameEn: 'Singapore', iata: 'SIN', country: 'Singapore', flag: '🇸🇬', region: 'Southeast Asia' },
  { id: '6', name: '峴港', nameEn: 'Danang', iata: 'DAD', country: 'Vietnam', flag: '🇻🇳', region: 'Southeast Asia' },
  { id: '7', name: '宿霧', nameEn: 'Cebu', iata: 'CEB', country: 'Philippines', flag: '🇵🇭', region: 'Southeast Asia' },
  { id: '8', name: '香港', nameEn: 'Hong Kong', iata: 'HKG', country: 'Hong Kong', flag: '🇭🇰', region: 'East Asia' },
  { id: '9', name: '吉隆坡', nameEn: 'Kuala Lumpur', iata: 'KUL', country: 'Malaysia', flag: '🇲🇾', region: 'Southeast Asia' },
  { id: '10', name: '沖繩', nameEn: 'Okinawa', iata: 'OKA', country: 'Japan', flag: '🇯🇵', region: 'East Asia' },
  { id: '11', name: '福岡', nameEn: 'Fukuoka', iata: 'FUK', country: 'Japan', flag: '🇯🇵', region: 'East Asia' },
  { id: '12', name: '馬尼拉', nameEn: 'Manila', iata: 'MNL', country: 'Philippines', flag: '🇵🇭', region: 'Southeast Asia' },
  { id: '13', name: '胡志明市', nameEn: 'Ho Chi Minh City', iata: 'SGN', country: 'Vietnam', flag: '🇻🇳', region: 'Southeast Asia' },
  { id: '14', name: '金邊', nameEn: 'Phnom Penh', iata: 'PNH', country: 'Cambodia', flag: '🇰🇭', region: 'Southeast Asia' },
];
