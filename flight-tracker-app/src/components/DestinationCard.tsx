import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS } from '../constants/theme';
import { Ionicons } from '@expo/vector-icons';
import { CITIES } from '../constants/cities';

export default function DestinationCard({ item }: { item: any }) {
  const city = CITIES.find(c => c.iata === item.iata);
  if (!city) return null;

  return (
    <LinearGradient colors={[COLORS.card, '#1a2138']} style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>{city.name} {city.flag}</Text>
        <Text style={styles.iata}>{city.iata}</Text>
      </View>
      <View style={styles.priceContainer}>
        <Text style={styles.price}>NT$ {item.price.toLocaleString()}</Text>
        <Ionicons name={item.trend === 'down' ? 'trending-down' : 'trending-up'} size={24} color={item.trend === 'down' ? COLORS.success : COLORS.danger} />
      </View>
      <View style={styles.details}>
        <Text style={styles.dateRange}>{item.dateRange}</Text>
        <Text style={styles.airline}>{item.airline}</Text>
      </View>
      {item.isLCC && (
        <View style={[styles.badge, { backgroundColor: item.lccStatus === 'on_sale' ? COLORS.accentSecondary : COLORS.warning }]}>
          <Text style={styles.badgeText}>{item.lccStatus === 'on_sale' ? 'LCC On Sale' : 'LCC Not Yet On Sale'}</Text>
        </View>
      )}
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.cardBorder,
  },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 20, fontWeight: 'bold', color: COLORS.primary },
  iata: { fontSize: 16, color: COLORS.secondary },
  priceContainer: { flexDirection: 'row', alignItems: 'center', marginTop: 12 },
  price: { fontSize: 32, fontWeight: '900', color: COLORS.primary, marginRight: 8 },
  details: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 },
  dateRange: { color: COLORS.secondary, fontSize: 14 },
  airline: { color: COLORS.secondary, fontSize: 14 },
  badge: { alignSelf: 'flex-start', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4, marginTop: 12 },
  badgeText: { color: COLORS.primary, fontSize: 12, fontWeight: 'bold' },
});
