import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'tech.cebo.waterpolo',
  appName: 'WaterPolo Stats',
  webDir: 'out',
  server: {
    // In production: uses bundled web assets from 'out/'
    // In dev: uncomment to point to local dev server
    // url: 'http://192.168.1.X:3001',
  },
  plugins: {
    SplashScreen: {
      launchAutoHide: true,
      backgroundColor: '#0b0f14',
      androidScaleType: 'CENTER_CROP',
    },
    StatusBar: {
      style: 'DARK',
      backgroundColor: '#0b0f14',
    },
  },
  ios: {
    contentInset: 'automatic',
  },
  android: {
    backgroundColor: '#0b0f14',
  },
};

export default config;
