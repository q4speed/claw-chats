/**
 * ClawChats OpenClaw Channel Plugin
 * 
 * Connects OpenClaw to ClawChats message server for real-time communication
 * 
 * Configuration:
 * {
 *   "channels": {
 *     "clawchats": {
 *       "enabled": true,
 *       "serverUrl": "ws://localhost:8765/ws",
 *       "userId": "openclaw-main",
 *       "token": "demo-token"
 *     }
 *   }
 * }
 */

import WebSocket from 'ws';

// ============== Types ==============

interface ChannelConfig {
  enabled: boolean;
  serverUrl: string;
  userId: string;
  token: string;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

interface RuntimeAPI {
  handleInbound?: (msg: {
    channelId: string;
    peerId: string;
    text: string;
    timestamp: number;
    metadata?: any;
  }) => void;
}

interface WSMessage {
  type: string;
  [key: string]: any;
}

// ============== State ==============

let ws: WebSocket | null = null;
let config: ChannelConfig | null = null;
let runtime: RuntimeAPI | null = null;
let connected = false;
let reconnectTimer: NodeJS.Timeout | null = null;

// ============== Connection Management ==============

/**
 * Initialize and start the channel monitor
 */
export async function monitorClawChats(cfg: ChannelConfig, rt?: RuntimeAPI) {
  config = cfg;
  runtime = rt;
  
  console.log('[ClawChats] Initializing...', {
    serverUrl: cfg.serverUrl,
    userId: cfg.userId
  });
  
  connect();
}

/**
 * Connect to ClawChats server
 */
function connect() {
  if (!config) {
    console.error('[ClawChats] No configuration');
    return;
  }
  
  try {
    console.log('[ClawChats] Connecting to', config.serverUrl);
    ws = new WebSocket(config.serverUrl);
    
    ws.on('open', onOpen);
    ws.on('message', onMessage);
    ws.on('close', onClose);
    ws.on('error', onError);
    
  } catch (err) {
    console.error('[ClawChats] Connection error:', err);
    scheduleReconnect();
  }
}

function onOpen() {
  console.log('[ClawChats] Connected');
  
  // Authenticate
  ws?.send(JSON.stringify({
    type: 'auth',
    userId: config?.userId,
    token: config?.token
  }));
}

function onMessage(data: Buffer) {
  try {
    const msg: WSMessage = JSON.parse(data.toString());
    handleMessage(msg);
  } catch (err) {
    console.error('[ClawChats] Parse error:', err);
  }
}

function onClose() {
  console.log('[ClawChats] Disconnected');
  connected = false;
  
  if (config?.autoReconnect !== false) {
    scheduleReconnect();
  }
}

function onError(err: Error) {
  console.error('[ClawChats] Error:', err.message);
  connected = false;
}

function handleMessage(msg: WSMessage) {
  switch (msg.type) {
    case 'auth':
      handleAuth(msg);
      break;
    
    case 'message':
      handleChatMessage(msg);
      break;
    
    case 'presence':
      handlePresence(msg);
      break;
    
    case 'pong':
      // Keepalive response
      break;
    
    default:
      console.log('[ClawChats] Unknown message type:', msg.type);
  }
}

function handleAuth(msg: WSMessage) {
  if (msg.ok) {
    connected = true;
    console.log('[ClawChats] Authenticated as', msg.userId);
    
    // Clear reconnect timer
    if (reconnectTimer) {
      clearInterval(reconnectTimer);
      reconnectTimer = null;
    }
  } else {
    console.error('[ClawChats] Auth failed:', msg.error);
  }
}

function handleChatMessage(msg: WSMessage) {
  console.log('[ClawChats] Message from', msg.from, ':', msg.content);
  
  if (runtime?.handleInbound) {
    runtime.handleInbound({
      channelId: 'clawchats',
      peerId: msg.from,
      text: msg.content,
      timestamp: msg.timestamp || Date.now(),
      metadata: msg.metadata
    });
  }
}

function handlePresence(msg: WSMessage) {
  console.log('[ClawChats] Online users:', msg.users);
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  
  const interval = config?.reconnectInterval || 30000;
  
  console.log(`[ClawChats] Will reconnect in ${interval / 1000}s...`);
  
  reconnectTimer = setInterval(() => {
    if (!connected && config) {
      console.log('[ClawChats] Reconnecting...');
      connect();
    }
  }, interval);
}

// ============== Outbound Messages ==============

/**
 * Send a text message
 */
export async function sendText(
  cfg: ChannelConfig,
  to: string,
  text: string,
  accountId?: string
): Promise<{ ok: boolean; error?: string }> {
  
  if (!ws || !connected) {
    const error = 'Not connected';
    console.error('[ClawChats]', error);
    return { ok: false, error };
  }
  
  try {
    const message: WSMessage = {
      type: 'message',
      to,
      content: text
    };
    
    if (accountId) {
      message.metadata = { accountId };
    }
    
    ws.send(JSON.stringify(message));
    console.log('[ClawChats] Sent message to', to);
    
    return { ok: true };
    
  } catch (err) {
    const error = err instanceof Error ? err.message : String(err);
    console.error('[ClawChats] Send error:', error);
    return { ok: false, error };
  }
}

/**
 * Send a task message (for OpenClaw collaboration)
 */
export async function sendTask(
  cfg: ChannelConfig,
  to: string,
  task: {
    taskId: string;
    action: 'create' | 'update' | 'complete';
    title: string;
    description: string;
    priority?: 'low' | 'normal' | 'high';
    deadline?: number;
  }
): Promise<{ ok: boolean; error?: string }> {
  
  if (!ws || !connected) {
    const error = 'Not connected';
    console.error('[ClawChats]', error);
    return { ok: false, error };
  }
  
  try {
    ws.send(JSON.stringify({
      type: 'task',
      to,
      payload: task
    }));
    console.log('[ClawChats] Sent task to', to);
    
    return { ok: true };
    
  } catch (err) {
    const error = err instanceof Error ? err.message : String(err);
    console.error('[ClawChats] Send task error:', error);
    return { ok: false, error };
  }
}

// ============== Utility Functions ==============

/**
 * Check connection status
 */
export function isConnected(): boolean {
  return connected && ws?.readyState === WebSocket.OPEN;
}

/**
 * Get current user ID
 */
export function getUserId(): string | null {
  return config?.userId || null;
}

/**
 * Disconnect from server
 */
export function disconnect() {
  if (reconnectTimer) {
    clearInterval(reconnectTimer);
    reconnectTimer = null;
  }
  
  if (ws) {
    ws.close();
    ws = null;
  }
  
  connected = false;
  console.log('[ClawChats] Disconnected');
}

/**
 * Reconnect to server
 */
export function reconnect() {
  disconnect();
  connect();
}

// ============== OpenClaw Channel Interface ==============

/**
 * OpenClaw channel export
 */
export const channel = {
  name: 'clawchats',
  version: '0.3.0',
  
  async init(cfg: ChannelConfig, rt?: RuntimeAPI) {
    await monitorClawChats(cfg, rt);
  },
  
  async sendText(
    cfg: ChannelConfig,
    to: string,
    text: string,
    accountId?: string
  ) {
    return sendText(cfg, to, text, accountId);
  },
  
  async sendTask(cfg: ChannelConfig, to: string, task: any) {
    return sendTask(cfg, to, task);
  },
  
  disconnect() {
    disconnect();
  },
  
  isConnected() {
    return isConnected();
  }
};

export default channel;
