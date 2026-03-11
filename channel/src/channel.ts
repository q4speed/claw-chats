/**
 * ClawChats OpenClaw Channel Plugin
 * Connects OpenClaw to ClawChats message server
 */

import WebSocket from 'ws';

interface ChannelConfig {
  serverUrl: string;
  userId: string;
  token: string;
}

interface RuntimeAPI {
  handleInbound?: (msg: {
    channelId: string;
    peerId: string;
    text: string;
    timestamp: number;
  }) => void;
}

let ws: WebSocket | null = null;
let config: ChannelConfig | null = null;
let runtime: RuntimeAPI | null = null;
let connected = false;

/**
 * Initialize and start the channel monitor
 */
export async function monitorClawChats(cfg: ChannelConfig, rt?: RuntimeAPI) {
  config = cfg;
  runtime = rt;

  connect();

  // Heartbeat - reconnect if disconnected
  setInterval(() => {
    if (!connected && config) {
      console.log('[ClawChats] Reconnecting...');
      connect();
    }
  }, 30000);
}

function connect() {
  if (!config) return;

  try {
    ws = new WebSocket(config.serverUrl);

    ws.on('open', () => {
      console.log('[ClawChats] Connected to', config.serverUrl);
      ws?.send(JSON.stringify({
        type: 'auth',
        userId: config.userId,
        token: config.token
      }));
    });

    ws.on('message', (data: Buffer) => {
      try {
        const msg = JSON.parse(data.toString());
        handleMessage(msg);
      } catch (err) {
        console.error('[ClawChats] Parse error:', err);
      }
    });

    ws.on('close', () => {
      console.log('[ClawChats] Disconnected');
      connected = false;
    });

    ws.on('error', (err) => {
      console.error('[ClawChats] Error:', err);
      connected = false;
    });
  } catch (err) {
    console.error('[ClawChats] Connection error:', err);
    connected = false;
  }
}

function handleMessage(msg: any) {
  switch (msg.type) {
    case 'auth':
      if (msg.ok) {
        connected = true;
        console.log('[ClawChats] Authenticated as', msg.userId);
      } else {
        console.error('[ClawChats] Auth failed:', msg.error);
      }
      break;

    case 'message':
      console.log('[ClawChats] Message from', msg.from, ':', msg.content);
      if (runtime?.handleInbound) {
        runtime.handleInbound({
          channelId: 'clawchats',
          peerId: msg.from,
          text: msg.content,
          timestamp: msg.timestamp || Date.now()
        });
      }
      break;

    case 'presence':
      console.log('[ClawChats] Online users:', msg.users);
      break;

    case 'pong':
      // Keepalive
      break;
  }
}

/**
 * Send a text message
 */
export async function sendText(cfg: ChannelConfig, to: string, text: string): Promise<{ ok: boolean }> {
  if (!ws || !connected) {
    console.error('[ClawChats] Not connected');
    return { ok: false, error: 'Not connected' };
  }

  try {
    ws.send(JSON.stringify({
      type: 'message',
      to,
      content: text
    }));
    console.log('[ClawChats] Sent message to', to);
    return { ok: true };
  } catch (err) {
    console.error('[ClawChats] Send error:', err);
    return { ok: false, error: String(err) };
  }
}

/**
 * Check connection status
 */
export function isConnected(): boolean {
  return connected && ws?.readyState === WebSocket.OPEN;
}

/**
 * Disconnect from server
 */
export function disconnect() {
  if (ws) {
    ws.close();
    ws = null;
  }
  connected = false;
}
