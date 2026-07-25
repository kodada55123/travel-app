import * as admin from 'firebase-admin';
import { ENV } from '../config';

if (ENV.FIREBASE.projectId && ENV.FIREBASE.clientEmail && ENV.FIREBASE.privateKey) {
  admin.initializeApp({
    credential: admin.credential.cert({
      projectId: ENV.FIREBASE.projectId,
      clientEmail: ENV.FIREBASE.clientEmail,
      privateKey: ENV.FIREBASE.privateKey,
    })
  });
}

export async function sendPushNotification(token: string, title: string, body: string) {
  if (!admin.apps.length) return;
  
  try {
    await admin.messaging().send({
      token,
      notification: { title, body },
      android: {
        notification: { channelId: 'flight_alerts' }
      },
      apns: {
        payload: { aps: { sound: 'default' } }
      }
    });
  } catch (error) {
    console.error('FCM Error:', error);
  }
}

export async function sendBatchNotifications(payloads: { token: string; title: string; body: string }[]) {
  if (!admin.apps.length || payloads.length === 0) return;

  const messages = payloads.map(p => ({
    token: p.token,
    notification: { title: p.title, body: p.body }
  }));

  try {
    await admin.messaging().sendEach(messages);
  } catch (error) {
    console.error('Batch FCM Error:', error);
  }
}
