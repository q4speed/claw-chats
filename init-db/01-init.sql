-- ClawChats Database Schema
-- Phase 2: 用户注册 + 即时通讯 + 群组管理

-- 用户表
CREATE TABLE IF NOT EXISTS users (
  id VARCHAR(64) PRIMARY KEY,
  username VARCHAR(64) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  email VARCHAR(255),
  status VARCHAR(32) DEFAULT 'active',  -- active | disabled
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_status ON users(status);

-- 用户会话表（在线状态）
CREATE TABLE IF NOT EXISTS user_sessions (
  user_id VARCHAR(64) PRIMARY KEY REFERENCES users(id),
  connected_at TIMESTAMP NOT NULL,
  disconnected_at TIMESTAMP,
  last_seen_at TIMESTAMP
);

CREATE INDEX idx_sessions_connected ON user_sessions(connected_at);

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
  id BIGSERIAL PRIMARY KEY,
  from_user VARCHAR(64) REFERENCES users(id),
  to_user VARCHAR(64) REFERENCES users(id),
  content TEXT NOT NULL,
  message_type VARCHAR(32) DEFAULT 'text',  -- text | system | group
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_to_user ON messages(to_user);
CREATE INDEX idx_messages_from_user ON messages(from_user);
CREATE INDEX idx_messages_created ON messages(created_at);

-- 群组表
CREATE TABLE IF NOT EXISTS groups (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  owner_id VARCHAR(64) REFERENCES users(id),
  description TEXT,
  avatar_url VARCHAR(512),
  status VARCHAR(32) DEFAULT 'active',  -- active | disabled
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_groups_owner ON groups(owner_id);
CREATE INDEX idx_groups_name ON groups(name);

-- 群成员表
CREATE TABLE IF NOT EXISTS group_members (
  id SERIAL PRIMARY KEY,
  group_id VARCHAR(64) REFERENCES groups(id) ON DELETE CASCADE,
  user_id VARCHAR(64) REFERENCES users(id) ON DELETE CASCADE,
  role VARCHAR(32) DEFAULT 'member',  -- admin | member
  joined_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(group_id, user_id)
);

CREATE INDEX idx_group_members_group ON group_members(group_id);
CREATE INDEX idx_group_members_user ON group_members(user_id);

-- 群组消息表
CREATE TABLE IF NOT EXISTS group_messages (
  id BIGSERIAL PRIMARY KEY,
  group_id VARCHAR(64) REFERENCES groups(id) ON DELETE CASCADE,
  from_user VARCHAR(64) REFERENCES users(id),
  content TEXT NOT NULL,
  message_type VARCHAR(32) DEFAULT 'text',
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_group_messages_group ON group_messages(group_id);
CREATE INDEX idx_group_messages_created ON group_messages(created_at);

-- 插入测试用户（可选）
-- 密码都是 "123456" 的 bcrypt 哈希
INSERT INTO users (id, username, password_hash) VALUES 
  ('user-1', 'alice', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu'),
  ('user-2', 'bob', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu')
ON CONFLICT (id) DO NOTHING;
