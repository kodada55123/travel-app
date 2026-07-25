import React, { useState } from 'react';
import { View, Text, StyleSheet, Switch, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { COLORS } from '../../src/constants/theme';
import { Ionicons } from '@expo/vector-icons';

export default function SettingsScreen() {
  const [dailyReport, setDailyReport] = useState(true);
  const [lccAlerts, setLccAlerts] = useState(true);

  const renderRow = (icon: any, title: string, rightContent: React.ReactNode) => (
    <View style={styles.row}>
      <View style={styles.rowLeft}>
        <Ionicons name={icon} size={24} color={COLORS.secondary} style={styles.rowIcon} />
        <Text style={styles.rowTitle}>{title}</Text>
      </View>
      {rightContent}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        <View style={styles.header}>
          <Text style={styles.title}>Settings</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>PREFERENCES</Text>
          <View style={styles.card}>
            {renderRow('location', 'Origin Airport', <Text style={styles.value}>TPE (Taoyuan)</Text>)}
            <View style={styles.divider} />
            {renderRow('cash', 'Currency', <Text style={styles.value}>TWD (NT$)</Text>)}
            <View style={styles.divider} />
            {renderRow('people', 'Passengers', <Text style={styles.value}>1 Adult</Text>)}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>NOTIFICATIONS</Text>
          <View style={styles.card}>
            {renderRow('document-text', 'Daily Report', <Switch value={dailyReport} onValueChange={setDailyReport} trackColor={{ true: COLORS.accent }} />)}
            <View style={styles.divider} />
            {renderRow('airplane', 'LCC Alerts', <Switch value={lccAlerts} onValueChange={setLccAlerts} trackColor={{ true: COLORS.accent }} />)}
            <View style={styles.divider} />
            {renderRow('pricetag', 'Price Drop Threshold', <Text style={styles.value}>- NT$1,000</Text>)}
          </View>
        </View>

        <TouchableOpacity style={styles.logoutButton}>
          <Text style={styles.logoutText}>Sign Out</Text>
        </TouchableOpacity>
        <Text style={styles.version}>Version 1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { padding: 16 },
  title: { fontSize: 28, fontWeight: 'bold', color: COLORS.primary },
  section: { marginBottom: 24, paddingHorizontal: 16 },
  sectionTitle: { color: COLORS.secondary, fontSize: 12, fontWeight: 'bold', marginBottom: 8, marginLeft: 8 },
  card: { backgroundColor: COLORS.card, borderRadius: 16, borderWidth: 1, borderColor: COLORS.cardBorder, overflow: 'hidden' },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16 },
  rowLeft: { flexDirection: 'row', alignItems: 'center' },
  rowIcon: { marginRight: 12 },
  rowTitle: { color: COLORS.primary, fontSize: 16 },
  value: { color: COLORS.accent, fontSize: 16, fontWeight: '500' },
  divider: { height: 1, backgroundColor: COLORS.cardBorder, marginLeft: 52 },
  logoutButton: { marginHorizontal: 16, backgroundColor: 'rgba(239, 68, 68, 0.1)', padding: 16, borderRadius: 12, alignItems: 'center', marginBottom: 24 },
  logoutText: { color: COLORS.danger, fontSize: 16, fontWeight: 'bold' },
  version: { textAlign: 'center', color: COLORS.secondary, fontSize: 12, marginBottom: 32 },
});
