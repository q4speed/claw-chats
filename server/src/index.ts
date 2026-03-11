/**
 * ClawChats Message Server - Phase 1 MVP
 * WebSocket server for real-time messaging
 */

import { WebSocketServer, WebSocket } from 'ws';
import { Pool } from 'pg';

const PORT = parseInt(process.env.PORT || '8765', 10);
const AUTH_TOKENS = new Set(
  (process.env.AUTH_TOKENS || 'demo-token,test-token').split(',')
);

// PostgreSQL connection pool
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:postgres@db:5432/clawchats',
});

// Store online users: userId -> WebSocket
const users = new Map<string, WebSocket>();

// Store user sessions for metadata
const userSessions = new Map<string, { ws: WebSocket; agentId?: string }>();

const wss = new WebSocketServer({ port: PORT });

console.log(`🦞 ClawChats Message Server starting on port ${PORT}...`);

wss.on('connection', (ws: WebSocket, req) => {
  let userId: string | null = null;
  let agentId: string | undefined;

  console.log(`[WS] New connection from ${req.socket.remoteAddress}`);

  // Handle incoming messages
  ws.on('message', async (data: Buffer) => {
    try {
      const msg = JSON.parse(data.toString());
      await handleMessage(ws, msg, (id: string, aid?: string) => {
        userId = id;
        agentId = aid;
      });
    } catch (err) {
      console.error('[WS] Parse error:', err);
      ws.send(JSON.stringify({ type: 'error', error: 'Invalid message format' }));
    }
  });

  // Handle connection close
  ws.on('close', async () => {
    console.log(`[WS] Connection closed for user ${userId}`);
    if (userId) {
      users.delete(userId);
      userSessions.delete(userId);
      try {
        await pool.query(
          'UPDATE user_sessions SET disconnected_at = NOW() WHERE user_id = $1',
          [userId]
        );
      } catch (err) {
        console.error('[DB] Error updating session:', err);
      }
    }
  });

  // Handle errors
  ws.on('error', (err) => {
    console.error('[WS] Error:', err);
  });
});

async function handleMessage(
  ws: WebSocket,
  msg: any,
  setUserId: (id: string, agentId?: string) => void
) {
  switch (msg.type) {
    case 'auth': {
      await handleAuth(ws, msg, setUserId);
      break;
    }
    case 'message': {
      await handleChatMessage(ws, msg);
      break;
    }
    case 'ping': {
      ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
      break;
    }
    default:
      console.warn('[WS] Unknown message type:', msg.type);
      ws.send(JSON.stringify({ type: 'error', error: 'Unknown message type' }));
  }
}

async function handleAuth(
  ws: WebSocket,
  msg: any,
  setUserId: (id: string, agentId?: string) => void
) {
  const { userId, token, agentId } = msg;

  if (!userId || !token) {
    ws.send(JSON.stringify({ type: 'auth', ok: false, error: 'Missing userId or token' }));
    ws.close();
    return;
  }

  if (!AUTH_TOKENS.has(token)) {
    console.log(`[AUTH] Invalid token for user ${userId}`);
    ws.send(JSON.stringify({ type: 'auth', ok: false, error: 'Invalid token' }));
    ws.close();
    return;
  }

  // Register user
  setUserId(userId, agentId);
  users.set(userId, ws);
  userSessions.set(userId, { ws, agentId });

  console.log(`[AUTH] User ${userId} authenticated (agent: ${agentId || 'no'})`);

  // Save to database
  try {
    await pool.query(
      `INSERT INTO users (id, created_at) VALUES ($1, NOW()) 
       ON CONFLICT (id) DO NOTHING`,
      [userId]
    );
    await pool.query(
      `INSERT INTO user_sessions (user_id, connected_at) VALUES ($1, NOW()) 
       ON CONFLICT (user_id) DO UPDATE SET connected_at = NOW(), disconnected_at = NULL`,
      [userId]
    );
  } catch (err) {
    console.error('[DB] Error saving auth:', err);
  }

  ws.send(JSON.stringify({ type: 'auth', ok: true, userId }));

  // Broadcast presence
  broadcastPresence();
}

async function handleChatMessage(ws: WebSocket, msg: any) {
  const senderId = Array.from(userSessions.entries()).find(
    ([, { ws: s }]) => s === ws
  )?.[0];

  if (!senderId) {
    ws.send(JSON.stringify({ type: 'error', error: 'Not authenticated' }));
    return;
  }

  const { to, content, type = 'text', metadata } = msg;

  if (!to || !content) {
    ws.send(JSON.stringify({ type: 'error', error: 'Missing to or content' }));
    return;
  }

  console.log(`[MSG] ${senderId} -> ${to}: ${content.substring(0, 50)}...`);

  // Save to database
  try {
    await pool.query(
      'INSERT INTO messages (from_user, to_user, content, message_type, metadata, created_at) VALUES ($1, $2, $3, $4, $5, NOW())',
      [senderId, to, content, type, metadata ? JSON.stringify(metadata) : null]
    );
  } catch (err) {
    console.error('[DB] Error saving message:', err);
  }

  // Forward to recipient if online
  const recipient = users.get(to);
  if (recipient && recipient.readyState === WebSocket.OPEN) {
    recipient.send(
      JSON.stringify({
        type: 'message',
        from: senderId,
        to,
        content,
        messageType: type,
        metadata,
        timestamp: Date.now(),
      })
    );
  } else {
    console.log(`[MSG] Recipient ${to} is offline, message stored`);
  }

  // Send ack to sender
  ws.send(
    JSON.stringify({
      type: 'ack',
      messageId: Date.now().toString(),
      status: 'delivered',
    })
  );
}

function broadcastPresence() {
  const onlineUsers = Array.from(users.keys());
  const presenceMsg = JSON.stringify({
    type: 'presence',
    users: onlineUsers,
    timestamp: Date.now(),
  });

  users.forEach((ws) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(presenceMsg);
    }
  });
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('[SERVER] Shutting down...');
  wss.close();
  await pool.end();
  process.exit(0);
});

console.log(`🦞 ClawChats Message Server running on port ${PORT}`);
