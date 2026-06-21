import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'tech.cebo.waterpolo',
  appName: 'Cap Track',
  webDir: 'out',
  server: {
    // In production: uses bundled web assets from 'out/'
    // In dev: uncomment to point to local dev server
    // url: 'http://192.168.1.X:3001',
  },
  // Plugins @capacitor/status-bar, splash-screen and haptics removed — their 8.0.x
  // iOS builds are incompatible with the resolved capacitor core (break the build).
  // Status bar styled via Info.plist; splash via LaunchScreen.storyboard.
  plugins: {},
  ios: {
    contentInset: 'automatic',
  },
  android: {
    backgroundColor: '#0b0f14',
  },
};

export default config;
