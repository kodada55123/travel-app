export function generateValidDatePairs(fromDate: Date): { departDate: string; returnDate: string; tripDays: number }[] {
  const pairs: { departDate: string; returnDate: string; tripDays: number }[] = [];
  const start = new Date(fromDate);
  start.setHours(0, 0, 0, 0);

  const end = new Date(start);
  end.setFullYear(end.getFullYear() + 1);

  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    for (const days of [5, 6]) {
      const returnDate = new Date(d);
      returnDate.setDate(returnDate.getDate() + days - 1);
      
      if (returnDate > end) continue;

      if (spansWeekend(d, returnDate)) {
        pairs.push({
          departDate: d.toISOString().split('T')[0],
          returnDate: returnDate.toISOString().split('T')[0],
          tripDays: days
        });
      }
    }
  }
  return pairs;
}

export function spansWeekend(start: Date, end: Date): boolean {
  let hasSaturday = false;
  let hasSunday = false;
  
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    if (d.getDay() === 6) hasSaturday = true;
    if (d.getDay() === 0) hasSunday = true;
  }
  
  return hasSaturday && hasSunday;
}
