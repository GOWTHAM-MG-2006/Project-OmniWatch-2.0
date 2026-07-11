/**
 * OmniWatch 2.0 — Mobile (Notifications)
 * Component: notifications
 * Layer: Mobile
 * Phase: 7
 * Purpose: Push notification registration and handling for incident alerts
 */
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import api from './api';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export async function registerForPushNotifications(): Promise<string | null> {
  try {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      console.log('Push notification permission not granted');
      return null;
    }

    const token = await Notifications.getExpoPushTokenAsync({
      projectId: 'omniwatch-mobile',
    });

    console.log('Push token:', token.data);

    if (Platform.OS === 'android') {
      Notifications.setNotificationChannelAsync('incidents', {
        name: 'Incident Alerts',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#FF231F7C',
      });
    }

    return token.data;
  } catch (error) {
    console.error('Failed to register for notifications:', error);
    return null;
  }
}

export async function scheduleIncidentNotification(incident: any): Promise<void> {
  try {
    await Notifications.scheduleNotificationAsync({
      content: {
        title: `🚨 ${incident.severity} Incident`,
        body: `${incident.root_cause?.entity || 'Unknown'} - ${incident.root_cause?.metric || ''}`,
        data: { incidentId: incident.incident_id },
        sound: true,
      },
      trigger: null,
    });
  } catch (error) {
    console.error('Failed to schedule notification:', error);
  }
}

export function addNotificationListener(
  handler: (notification: Notifications.Notification) => void
): Notifications.Subscription {
  return Notifications.addNotificationReceivedListener(handler);
}

export function addResponseListener(
  handler: (response: Notifications.NotificationResponse) => void
): Notifications.Subscription {
  return Notifications.addNotificationResponseReceivedListener(handler);
}
