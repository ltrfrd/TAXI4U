// Background location tracking — stub for future implementation.
//
// When implemented, this module will use expo-location's background mode
// (requires expo-location background permission + app.json background modes)
// to continue GPS tracking after the app moves to the background.
//
// Expo docs: https://docs.expo.dev/versions/latest/sdk/location/#background-location-methods

export async function startBackgroundTracking() {
  throw new Error('Background location tracking is not yet implemented.');
}

export async function stopBackgroundTracking() {
  // no-op until implemented
}
