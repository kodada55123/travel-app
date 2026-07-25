import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { COLORS } from '../../src/constants/theme';
import { useFlightData } from '../../src/hooks/useFlightData';
import DestinationCard from '../../src/components/DestinationCard';
import { LinearGradient } from 'expo-linear-gradient';

export default function DashboardScreen() {
  const { destinations, report, loading } = useFlightData();
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1000);
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>✈️ Flight Tracker</Text>
        <Text style={styles.date}>{new Date().toLocaleDateString()}</Text>
      </View>

      <FlatList
        data={destinations}
        keyExtractor={item => item.id}
        renderItem={({ item }) => <DestinationCard item={item} />}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl refreshing={refreshing || loading} onRefresh={onRefresh} tintColor={COLORS.primary} />
        }
        ListHeaderComponent={() => (
          <LinearGradient colors={['#4A90D9', '#2E5A88']} style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>Summary</Text>
            <View style={styles.summaryRow}>
              <View>
                <Text style={styles.summaryLabel}>Tracked</Text>
                <Text style={styles.summaryValue}>{report?.totalTracked || 0}</Text>
              </View>
              <View>
                <Text style={styles.summaryLabel}>Cheapest Deal</Text>
                <Text style={styles.summaryValue}>NT$ {report?.cheapestDeal?.toLocaleString() || 0}</Text>
              </View>
            </View>
          </LinearGradient>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { padding: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerTitle: { fontSize: 24, fontWeight: 'bold', color: COLORS.primary },
  date: { color: COLORS.secondary, fontSize: 14 },
  listContent: { padding: 16 },
  summaryCard: { padding: 20, borderRadius: 16, marginBottom: 24 },
  summaryTitle: { color: COLORS.primary, fontSize: 18, fontWeight: 'bold', marginBottom: 16 },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-between' },
  summaryLabel: { color: 'rgba(255,255,255,0.7)', fontSize: 14, marginBottom: 4 },
  summaryValue: { color: COLORS.primary, fontSize: 24, fontWeight: 'bold' },
});
