import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { COLORS } from '../src/constants/theme';
import { usePushNotifications } from '../src/hooks/usePushNotifications';
import { SafeAreaProvider } from 'react-native-safe-area-context';

export default function RootLayout() {
  usePushNotifications();

  return (
    <SafeAreaProvider style={{ backgroundColor: COLORS.background }}>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: COLORS.background },
          headerTintColor: COLORS.primary,
          contentStyle: { backgroundColor: COLORS.background },
        }}>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="destination/[id]" options={{ presentation: 'modal' }} />
      </Stack>
    </SafeAreaProvider>
  );
}
