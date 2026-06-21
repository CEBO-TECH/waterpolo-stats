/**
 * Platform abstraction — differences between web and native (Capacitor).
 *
 * On web: uses localStorage, no haptics, no status bar control.
 * On native: uses Capacitor plugins for native feel.
 */

let _isNative: boolean | null = null;

export function isNativePlatform(): boolean {
  if (_isNative !== null) return _isNative;
  if (typeof window === 'undefined') return false;
  try {
    // Capacitor sets window.Capacitor when running in native container
    _isNative = !!(window as any).Capacitor?.isNativePlatform?.();
  } catch {
    _isNative = false;
  }
  return _isNative;
}

/**
 * Haptic feedback — vibrates on native, no-op on web.
 * Used when recording events for tactile confirmation.
 */
export async function hapticImpact(): Promise<void> {
  // No-op — @capacitor/haptics removed (its 8.0.x build is incompatible with the
  // resolved capacitor core and breaks the iOS build). Tactile feedback dropped.
}

/**
 * Status bar styling.
 *
 * The @capacitor/status-bar plugin (8.0.2) is incompatible with capacitor-swift-pm
 * 8.0.2 (it calls removed APIs: PluginConfig.getString / UIColor(fromHex:)), which
 * breaks the iOS build. We removed the plugin and set the status bar natively via
 * Info.plist instead (UIStatusBarStyle = light content). This is now a no-op.
 */
export async function setDarkStatusBar(): Promise<void> {
  // No-op — handled by Info.plist (UIStatusBarStyleLightContent).
}
