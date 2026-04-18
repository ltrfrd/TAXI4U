import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { TouchableOpacity, Text } from 'react-native';
import { AuthProvider, useAuth } from '../context/AuthContext';
import DriverLoginScreen from '../screens/DriverLoginScreen';
import DriverProfileScreen from '../screens/DriverProfileScreen';
import DriverRidesScreen from '../screens/DriverRidesScreen';
import HomeScreen from '../screens/HomeScreen';
import MapScreen from '../screens/MapScreen';
import ResultScreen from '../screens/ResultScreen';

const Stack = createStackNavigator();

const HEADER = {
  headerStyle: { backgroundColor: '#1a1a2e' },
  headerTintColor: '#f5c518',
  headerTitleStyle: { fontWeight: 'bold', fontSize: 20 },
};

function RootNavigator() {
  const { token, loading } = useAuth();

  if (loading) return null;

  return (
    <Stack.Navigator screenOptions={HEADER}>
      {token ? (
        <>
          <Stack.Screen
            name="Home"
            component={HomeScreen}
            options={({ navigation }) => ({
              title: 'TAXI4U',
              headerRight: () => (
                <TouchableOpacity
                  onPress={() => navigation.navigate('DriverProfile')}
                  style={{ marginRight: 16 }}
                >
                  <Text style={{ color: '#f5c518', fontSize: 22 }}>{'👤'}</Text>
                </TouchableOpacity>
              ),
            })}
          />
          <Stack.Screen name="Result" component={ResultScreen} options={{ title: 'Fare Result' }} />
          <Stack.Screen name="Map" component={MapScreen} options={{ title: 'Live Zone Map' }} />
          <Stack.Screen
            name="DriverProfile"
            component={DriverProfileScreen}
            options={{ title: 'My Profile' }}
          />
          <Stack.Screen
            name="DriverRides"
            component={DriverRidesScreen}
            options={{ title: 'My Rides' }}
          />
        </>
      ) : (
        <Stack.Screen
          name="DriverLogin"
          component={DriverLoginScreen}
          options={{ title: 'TAXI4U — Driver', headerLeft: () => null }}
        />
      )}
    </Stack.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <AuthProvider>
      <NavigationContainer>
        <RootNavigator />
      </NavigationContainer>
    </AuthProvider>
  );
}
