export const apiClient = {
  baseUrl: 'https://api.flighttracker.example.com',
  async getDestinations() {
    // Mock implementation
    return Promise.resolve([
      { id: '1', iata: 'NRT', price: 4500, dateRange: 'Oct 12 - Oct 19', airline: 'Peach', isLCC: true, lccStatus: 'on_sale', trend: 'down' },
      { id: '2', iata: 'KIX', price: 5200, dateRange: 'Nov 01 - Nov 05', airline: 'Jetstar', isLCC: true, lccStatus: 'on_sale', trend: 'up' },
    ]);
  },
  async getFlightReport() {
    return Promise.resolve({
      totalTracked: 12,
      cheapestDeal: 4500,
    });
  },
};
