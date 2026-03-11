"""
ClawChats Message Server - Phase 1 MVP
WebSocket server for real-time messaging using FastAPI
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Set, Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncpg

# Configuration
PORT = int(os.getenv("PORT", "8765"))
AUTH_TOKENS = set(os.getenv("AUTH_TOKENS", "demo-token,test-token,admin-token").split(","))
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/clawchats"
)

# FastAPI app
app = FastAPI(title="ClawChats Message Server", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, dict] = {}
        self.group_subscriptions: Dict[str, Set[str]] = {}  # group_id -> set of user_ids
        self.db_pool: Optional[asyncpg.Pool] = None

    async def connect(self, websocket: WebSocket, user_id: str, agent_id: Optional[str] = None):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_sessions[user_id] = {"ws": websocket, "agent_id": agent_id}
        
        # Save to database
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO users (id, created_at) 
                    VALUES ($1, NOW()) ON CONFLICT (id) DO NOTHING
                    """,
                    user_id
                )
                await conn.execute(
                    """
                    INSERT INTO user_sessions (user_id, connected_at) 
                    VALUES ($1, NOW()) 
                    ON CONFLICT (user_id) DO UPDATE 
                    SET connected_at = NOW(), disconnected_at = NULL
                    """,
                    user_id
                )
        
        print(f"[WS] User {user_id} connected")
        await self.broadcast_presence()

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        # Remove from all group subscriptions
        for group_id in self.group_subscriptions:
            self.group_subscriptions[group_id].discard(user_id)
        print(f"[WS] User {user_id} disconnected")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            ws = self.active_connections[user_id]
            await ws.send_json(message)

    async def broadcast(self, message: dict):
        for ws in self.active_connections.values():
            await ws.send_json(message)

    async def broadcast_presence(self):
        users = list(self.active_connections.keys())
        await self.broadcast({
            "type": "presence",
            "users": users,
            "timestamp": int(datetime.now().timestamp() * 1000)
        })

    async def broadcast_to_group(self, group_id: str, message: dict, exclude_user: Optional[str] = None):
        """Broadcast message to all users in a group"""
        if group_id not in self.group_subscriptions:
            return
        for user_id in self.group_subscriptions[group_id]:
            if user_id != exclude_user and user_id in self.active_connections:
                await self.send_personal_message(message, user_id)

    async def subscribe_to_group(self, user_id: str, group_id: str):
        """Subscribe a user to a group"""
        if group_id not in self.group_subscriptions:
            self.group_subscriptions[group_id] = set()
        self.group_subscriptions[group_id].add(user_id)
        print(f"[WS] User {user_id} subscribed to group {group_id}")

    async def unsubscribe_from_group(self, user_id: str, group_id: str):
        """Unsubscribe a user from a group"""
        if group_id in self.group_subscriptions:
            self.group_subscriptions[group_id].discard(user_id)
            print(f"[WS] User {user_id} unsubscribed from group {group_id}")

    async def init_db(self):
        """Initialize database connection pool"""
        try:
            self.db_pool = await asyncpg.create_pool(DATABASE_URL)
            print("[DB] Connection pool created")
        except Exception as e:
            print(f"[DB] Connection failed: {e}")
            self.db_pool = None

    async def save_message(self, from_user: str, to_user: str, content: str, 
                          msg_type: str = "text", metadata: Optional[dict] = None):
        if not self.db_pool:
            return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO messages (from_user, to_user, content, message_type, metadata, created_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    """,
                    from_user, to_user, content, msg_type, 
                    json.dumps(metadata) if metadata else None
                )
        except Exception as e:
            print(f"[DB] Error saving message: {e}")

    async def save_group_message(self, group_id: str, from_user: str, content: str, 
                                msg_type: str = "text", metadata: Optional[dict] = None):
        if not self.db_pool:
            return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO group_messages (group_id, from_user, content, message_type, metadata, created_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    """,
                    group_id, from_user, content, msg_type, 
                    json.dumps(metadata) if metadata else None
                )
        except Exception as e:
            print(f"[DB] Error saving group message: {e}")

    async def get_group_members(self, group_id: str) -> List[str]:
        """Get list of user IDs in a group"""
        if not self.db_pool:
            return []
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT user_id FROM group_members WHERE group_id = $1",
                    group_id
                )
                return [row["user_id"] for row in rows]
        except Exception as e:
            print(f"[DB] Error getting group members: {e}")
            return []

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    await manager.init_db()
    print(f"🦞 ClawChats Message Server starting on port {PORT}...")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    user_id: Optional[str] = None
    
    await manager.connect(websocket, "temp")  # Temporary connection
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                await handle_message(websocket, msg, manager)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "error": "Invalid JSON"})
    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(user_id)
            await manager.broadcast_presence()

async def handle_message(websocket: WebSocket, msg: dict, manager: ConnectionManager):
    msg_type = msg.get("type")
    
    if msg_type == "auth":
        await handle_auth(websocket, msg, manager)
    elif msg_type == "message":
        await handle_chat_message(websocket, msg, manager)
    elif msg_type == "group_message":
        await handle_group_message(websocket, msg, manager)
    elif msg_type == "group_subscribe":
        await handle_group_subscribe(websocket, msg, manager)
    elif msg_type == "group_unsubscribe":
        await handle_group_unsubscribe(websocket, msg, manager)
    elif msg_type == "ping":
        await websocket.send_json({"type": "pong", "timestamp": int(datetime.now().timestamp() * 1000)})
    else:
        await websocket.send_json({"type": "error", "error": "Unknown message type"})

async def handle_auth(websocket: WebSocket, msg: dict, manager: ConnectionManager):
    user_id = msg.get("userId")
    token = msg.get("token")
    agent_id = msg.get("agentId")

    if not user_id or not token:
        await websocket.send_json({"type": "auth", "ok": False, "error": "Missing userId or token"})
        await websocket.close()
        return

    if token not in AUTH_TOKENS:
        print(f"[AUTH] Invalid token for user {user_id}")
        await websocket.send_json({"type": "auth", "ok": False, "error": "Invalid token"})
        await websocket.close()
        return

    # Remove temp connection and add real one
    manager.disconnect("temp")
    await manager.connect(websocket, user_id, agent_id)
    
    print(f"[AUTH] User {user_id} authenticated (agent: {agent_id or 'no'})")
    await websocket.send_json({"type": "auth", "ok": True, "userId": user_id})

async def handle_chat_message(websocket: WebSocket, msg: dict, manager: ConnectionManager):
    # Find sender
    sender_id = None
    for uid, session in manager.user_sessions.items():
        if session["ws"] == websocket:
            sender_id = uid
            break

    if not sender_id:
        await websocket.send_json({"type": "error", "error": "Not authenticated"})
        return

    to_user = msg.get("to")
    content = msg.get("content")
    msg_type = msg.get("type", "text")
    metadata = msg.get("metadata")

    if not to_user or not content:
        await websocket.send_json({"type": "error", "error": "Missing to or content"})
        return

    print(f"[MSG] {sender_id} -> {to_user}: {content[:50]}...")

    # Save to database
    await manager.save_message(sender_id, to_user, content, msg_type, metadata)

    # Forward to recipient if online
    if to_user in manager.active_connections:
        await manager.send_personal_message({
            "type": "message",
            "from": sender_id,
            "to": to_user,
            "content": content,
            "messageType": msg_type,
            "metadata": metadata,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }, to_user)
    else:
        print(f"[MSG] Recipient {to_user} is offline, message stored")

    # Send ack
    await websocket.send_json({
        "type": "ack",
        "messageId": str(int(datetime.now().timestamp() * 1000)),
        "status": "delivered"
    })

@app.get("/health")
async def health_check():
    return {"status": "healthy", "connections": len(manager.active_connections)}

@app.get("/stats")
async def get_stats():
    return {
        "online_users": len(manager.active_connections),
        "users": list(manager.active_connections.keys()),
        "group_subscriptions": {k: len(v) for k, v in manager.group_subscriptions.items()}
    }


# ============== Group Message Handlers ==============

async def handle_group_subscribe(websocket: WebSocket, msg: dict, manager: ConnectionManager):
    """Subscribe to a group"""
    sender_id = None
    for uid, session in manager.user_sessions.items():
        if session["ws"] == websocket:
            sender_id = uid
            break
    
    if not sender_id:
        await websocket.send_json({"type": "error", "error": "Not authenticated"})
        return
    
    group_id = msg.get("group_id")
    if not group_id:
        await websocket.send_json({"type": "error", "error": "Missing group_id"})
        return
    
    await manager.subscribe_to_group(sender_id, group_id)
    await websocket.send_json({
        "type": "group_subscribed",
        "group_id": group_id,
        "status": "ok"
    })


async def handle_group_unsubscribe(websocket: WebSocket, msg: dict, manager: ConnectionManager):
    """Unsubscribe from a group"""
    sender_id = None
    for uid, session in manager.user_sessions.items():
        if session["ws"] == websocket:
            sender_id = uid
            break
    
    if not sender_id:
        await websocket.send_json({"type": "error", "error": "Not authenticated"})
        return
    
    group_id = msg.get("group_id")
    if not group_id:
        await websocket.send_json({"type": "error", "error": "Missing group_id"})
        return
    
    await manager.unsubscribe_from_group(sender_id, group_id)
    await websocket.send_json({
        "type": "group_unsubscribed",
        "group_id": group_id,
        "status": "ok"
    })


async def handle_group_message(websocket: WebSocket, msg: dict, manager: ConnectionManager):
    """Handle group message"""
    sender_id = None
    for uid, session in manager.user_sessions.items():
        if session["ws"] == websocket:
            sender_id = uid
            break
    
    if not sender_id:
        await websocket.send_json({"type": "error", "error": "Not authenticated"})
        return
    
    group_id = msg.get("group_id")
    content = msg.get("content")
    msg_type = msg.get("type", "text")
    
    if not group_id or not content:
        await websocket.send_json({"type": "error", "error": "Missing group_id or content"})
        return
    
    print(f"[GROUP MSG] {sender_id} -> group {group_id}: {content[:50]}...")
    
    # Save to database
    await manager.save_group_message(group_id, sender_id, content, msg_type)
    
    # Broadcast to all group members
    broadcast_msg = {
        "type": "group_message",
        "group_id": group_id,
        "from": sender_id,
        "content": content,
        "messageType": msg_type,
        "timestamp": int(datetime.now().timestamp() * 1000)
    }
    
    await manager.broadcast_to_group(group_id, broadcast_msg, exclude_user=sender_id)
    
    # Send ack to sender
    await websocket.send_json({
        "type": "ack",
        "messageId": str(int(datetime.now().timestamp() * 1000)),
        "status": "delivered"
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
