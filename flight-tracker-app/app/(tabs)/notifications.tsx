import React from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { COLORS } from '../../src/constants/theme';
import { Ionicons } from '@expo/vector-icons';

const NOTIFICATIONS = [
  { id: '1', type: 'lcc_alert', title: 'Peach Aviation Sale!', message: 'TPE to NRT from NT$2,500 starts tomorrow.', date: 'Just now', read: false },
  { id: '2', type: 'price_drop', title: 'Price Drop: KIX', message: 'Osaka flights dropped below NT$5,000.', date: '2 hours ago', read: false },
  { id: '3', type: 'daily_report', title: 'Daily Tracker Report', message: 'Checked 12 destinations. Found 2 new deals.', date: 'Yesterday', read: true },
];

export default function NotificationsScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Notifications</Text>
      </View>
      <FlatList
        data={NOTIFICATIONS}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <TouchableOpacity style={[styles.card, !item.read && styles.cardUnread]}>
            <View style={styles.iconContainer}>
              <Ionicons 
                name={item.type === 'lcc_alert' ? 'airplane' : item.type === 'price_drop' ? 'pricetag' : 'document-text'} 
                size={24} 
                color={item.type === 'lcc_alert' ? COLORS.accentSecondary : COLORS.accent} 
              />
            </View>
            <View style={styles.content}>
              <Text style={styles.cardTitle}>{item.title}</Text>
              <Text style={styles.message}>{item.message}</Text>
              <Text style={styles.time}>{item.date}</Text>
            </View>
            {!item.read && <View style={styles.unreadDot} />}
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { padding: 16 },
  title: { fontSize: 28, fontWeight: 'bold', color: COLORS.primary },
  list: { padding: 16 },
  card: { flexDirection: 'row', backgroundColor: COLORS.card, padding: 16, borderRadius: 12, marginBottom: 12, borderWidth: 1, borderColor: COLORS.cardBorder, alignItems: 'center' },
  cardUnread: { borderColor: COLORS.accent, backgroundColor: '#1a2238' },
  iconContainer: { width: 48, height: 48, borderRadius: 24, backgroundColor: 'rgba(255,255,255,0.05)', justifyContent: 'center', alignItems: 'center', marginRight: 16 },
  content: { flex: 1 },
  cardTitle: { color: COLORS.primary, fontSize: 16, fontWeight: 'bold', marginBottom: 4 },
  message: { color: COLORS.secondary, fontSize: 14, marginBottom: 8 },
  time: { color: COLORS.secondary, fontSize: 12 },
  unreadDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: COLORS.accent, marginLeft: 8 },
});
