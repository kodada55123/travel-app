import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, TextInput, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { COLORS } from '../../src/constants/theme';
import { CITIES } from '../../src/constants/cities';
import { Ionicons } from '@expo/vector-icons';

export default function AddDestinationScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [tracked, setTracked] = useState<Record<string, boolean>>({ NRT: true, KIX: true });

  const filteredCities = CITIES.filter(c => 
    c.name.includes(searchQuery) || c.nameEn.toLowerCase().includes(searchQuery.toLowerCase()) || c.iata.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const toggleTrack = (iata: string) => {
    setTracked(prev => ({ ...prev, [iata]: !prev[iata] }));
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Add Destination</Text>
      </View>
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color={COLORS.secondary} style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search city or IATA..."
          placeholderTextColor={COLORS.secondary}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>
      <FlatList
        data={filteredCities}
        keyExtractor={item => item.iata}
        numColumns={2}
        contentContainerStyle={styles.grid}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card} onPress={() => toggleTrack(item.iata)}>
            <Text style={styles.flag}>{item.flag}</Text>
            <Text style={styles.cityName}>{item.name}</Text>
            <Text style={styles.cityEn}>{item.nameEn}</Text>
            <Text style={styles.iata}>{item.iata}</Text>
            {tracked[item.iata] && (
              <View style={styles.trackedBadge}>
                <Ionicons name="checkmark-circle" size={24} color={COLORS.success} />
              </View>
            )}
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
  searchContainer: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.card, margin: 16, borderRadius: 12, paddingHorizontal: 12, borderWidth: 1, borderColor: COLORS.cardBorder },
  searchIcon: { marginRight: 8 },
  searchInput: { flex: 1, color: COLORS.primary, paddingVertical: 12, fontSize: 16 },
  grid: { padding: 8 },
  card: { flex: 1, backgroundColor: COLORS.card, margin: 8, padding: 16, borderRadius: 16, alignItems: 'center', borderWidth: 1, borderColor: COLORS.cardBorder, position: 'relative' },
  flag: { fontSize: 32, marginBottom: 8 },
  cityName: { color: COLORS.primary, fontSize: 16, fontWeight: 'bold' },
  cityEn: { color: COLORS.secondary, fontSize: 12, marginTop: 4 },
  iata: { color: COLORS.accent, fontSize: 14, fontWeight: 'bold', marginTop: 8 },
  trackedBadge: { position: 'absolute', top: 8, right: 8 },
});
