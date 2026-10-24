import { TabList, TabSlot, TabTrigger, Tabs, type TabTriggerSlotProps } from 'expo-router/ui';
import { useEffect } from 'react';
import { Pressable, Text, type PressableProps } from 'react-native';

import { useApp } from '@/lib/state';
import { Brand } from '@/lib/theme';

/** On web the pages sit in a top bar, like the Streamlit app's navigation. */
export default function AppTabs() {
  const { colors } = useApp();
  useEffect(() => {
    // Browsers default SVG text to a serif font; match the rest of the UI.
    const s = document.createElement('style');
    s.textContent = 'svg text { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }';
    document.head.appendChild(s);
    return () => s.remove();
  }, []);
  return (
    <Tabs>
      <TabList style={{ flexDirection: 'row', gap: 6, paddingHorizontal: 16, paddingVertical: 8, backgroundColor: colors.bg,
        borderBottomWidth: 1, borderBottomColor: colors.border, justifyContent: 'center' }}>
        <TabTrigger name="index" href="/" asChild><TabButton>📈 Analyze</TabButton></TabTrigger>
        <TabTrigger name="compare" href="/compare" asChild><TabButton>⇆ Compare</TabButton></TabTrigger>
        <TabTrigger name="batch" href="/batch" asChild><TabButton>▤ Batch</TabButton></TabTrigger>
        <TabTrigger name="method" href="/method" asChild><TabButton>⚗ Method & results</TabButton></TabTrigger>
      </TabList>
      <TabSlot style={{ flex: 1 }} />
    </Tabs>
  );
}

function TabButton({ children, isFocused, ...props }: TabTriggerSlotProps) {
  const { colors } = useApp();
  return (
    <Pressable {...(props as PressableProps)} style={{ paddingHorizontal: 12, paddingVertical: 6, borderRadius: 6,
      backgroundColor: isFocused ? 'rgba(27,127,122,0.14)' : 'transparent' }}>
      <Text style={{ fontSize: 14, fontWeight: isFocused ? '700' : '500', color: isFocused ? Brand.teal : colors.text }}>{children}</Text>
    </Pressable>
  );
}
