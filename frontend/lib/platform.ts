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
  if (!isNativePlatform()) return;
  try {
    const { Haptics, ImpactStyle } = await import('@capacitor/haptics');
    await Haptics.impact({ style: ImpactStyle.Medium });
  } catch {
    // Plugin not available
  }
}

/**
 * Set dark status bar — matches app theme on native.
 */
export async function setDarkStatusBar(): Promise<void> {
  if (!isNativePlatform()) return;
  try {
    const { StatusBar, Style } = await import('@capacitor/status-bar');
    await StatusBar.setStyle({ style: Style.Dark });
    await StatusBar.setBackgroundColor({ color: '#0b0f14' });
  } catch {
    // Plugin not available
  }
}
