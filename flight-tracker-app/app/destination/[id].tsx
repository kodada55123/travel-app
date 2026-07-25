import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../../src/constants/theme';
import { CITIES } from '../../src/constants/cities';

export default function DestinationDetailScreen() {
  const { id } = useLocalSearchParams();
  const city = CITIES.find(c => c.iata === id) || CITIES[0];

  return (
    <View style={styles.container}>
      <ScrollView bounces={false}>
        <LinearGradient colors={['#1a2138', COLORS.background]} style={styles.hero}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color={COLORS.primary} />
          </TouchableOpacity>
          <Text style={styles.heroFlag}>{city.flag}</Text>
          <Text style={styles.heroTitle}>{city.name} ({city.iata})</Text>
          <Text style={styles.heroSubtitle}>{city.nameEn}, {city.country}</Text>
          
          <View style={styles.heroPriceContainer}>
            <Text style={styles.heroPriceLabel}>Current Best Price</Text>
            <Text style={styles.heroPrice}>NT$ 4,500</Text>
          </View>
        </LinearGradient>

        <View style={styles.content}>
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>LCC STATUS</Text>
            <View style={styles.lccCard}>
              <View style={styles.lccHeader}>
                <Text style={styles.lccName}>Peach Aviation</Text>
                <View style={[styles.badge, { backgroundColor: COLORS.accentSecondary }]}>
                  <Text style={styles.badgeText}>On Sale</Text>
                </View>
              </View>
              <Text style={styles.lccDetails}>Winter schedule available up to Mar 2027.</Text>
            </View>
            <View style={styles.lccCard}>
              <View style={styles.lccHeader}>
                <Text style={styles.lccName}>Tigerair Taiwan</Text>
                <View style={[styles.badge, { backgroundColor: COLORS.warning }]}>
                  <Text style={styles.badgeText}>Not Yet</Text>
                </View>
              </View>
              <Text style={styles.lccDetails}>Expected to open Summer schedule next week.</Text>
            </View>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>PRICE TREND (Mock Heatmap)</Text>
            <View style={styles.heatmapCard}>
              {['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'].map((month, i) => (
                <View key={month} style={styles.monthRow}>
                  <Text style={styles.monthText}>{month}</Text>
                  <View style={styles.daysRow}>
                    {Array.from({ length: 5 }).map((_, j) => (
                      <View key={j} style={[styles.heatCell, { backgroundColor: i === 1 && j === 2 ? COLORS.success : i === 2 ? COLORS.danger : COLORS.warning }]} />
                    ))}
                  </View>
                </View>
              ))}
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  hero: { paddingTop: 60, paddingBottom: 32, paddingHorizontal: 20, alignItems: 'center' },
  backButton: { position: 'absolute', top: 50, left: 20, width: 40, height: 40, justifyContent: 'center', alignItems: 'center', borderRadius: 20, backgroundColor: 'rgba(255,255,255,0.1)' },
  heroFlag: { fontSize: 64, marginBottom: 16, marginTop: 20 },
  heroTitle: { fontSize: 32, fontWeight: 'bold', color: COLORS.primary },
  heroSubtitle: { fontSize: 16, color: COLORS.secondary, marginTop: 4 },
  heroPriceContainer: { marginTop: 24, alignItems: 'center', padding: 16, backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 16, width: '100%' },
  heroPriceLabel: { color: COLORS.secondary, fontSize: 14, marginBottom: 4 },
  heroPrice: { color: COLORS.primary, fontSize: 36, fontWeight: '900' },
  content: { padding: 20 },
  section: { marginBottom: 32 },
  sectionTitle: { color: COLORS.secondary, fontSize: 14, fontWeight: 'bold', marginBottom: 16, letterSpacing: 1 },
  lccCard: { backgroundColor: COLORS.card, padding: 16, borderRadius: 12, marginBottom: 12, borderWidth: 1, borderColor: COLORS.cardBorder },
  lccHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  lccName: { color: COLORS.primary, fontSize: 16, fontWeight: 'bold' },
  badge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4 },
  badgeText: { color: COLORS.primary, fontSize: 12, fontWeight: 'bold' },
  lccDetails: { color: COLORS.secondary, fontSize: 14 },
  heatmapCard: { backgroundColor: COLORS.card, padding: 16, borderRadius: 12, borderWidth: 1, borderColor: COLORS.cardBorder },
  monthRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  monthText: { color: COLORS.primary, width: 40, fontSize: 14 },
  daysRow: { flexDirection: 'row', flex: 1, justifyContent: 'space-between' },
  heatCell: { width: '18%', height: 24, borderRadius: 4 },
});
