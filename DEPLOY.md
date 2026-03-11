# 🦞 ClawChats 快速部署指南

> 本指南适用于零基础用户，按照步骤操作即可完成部署

---

## 📋 系统要求

### 最低配置
- **CPU:** 2 核心
- **内存:** 2GB
- **磁盘:** 10GB
- **操作系统:** Windows 10 / macOS 10.15+ / Linux

### 必需软件
- **Docker Desktop** (Windows/macOS) 或 **Docker + Docker Compose** (Linux)

---

## 🚀 快速开始（3 步部署）

### 步骤 1: 安装 Docker

#### Windows/macOS 用户
1. 访问 https://www.docker.com/products/docker-desktop/
2. 下载并安装 Docker Desktop
3. 启动 Docker Desktop
4. 等待右下角图标变为绿色（表示 Docker 已启动）

#### Linux 用户
```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

---

### 步骤 2: 下载项目

#### 方式 A: Git 克隆（推荐）
```bash
git clone https://github.com/q4speed/claw-chats.git
cd claw-chats
```

#### 方式 B: 手动下载
1. 访问 https://github.com/q4speed/claw-chats
2. 点击 "Code" → "Download ZIP"
3. 解压到任意目录
4. 打开终端/命令提示符，进入解压后的目录

---

### 步骤 3: 启动服务

```bash
# 一键启动所有服务
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

**启动成功后，你会看到类似输出：**
```
✔ Container clawchats-db           Started
✔ Container clawchats-message-server Started
✔ Container clawchats-admin-server   Started
✔ Container clawchats-admin-web      Started
✔ Container clawchats-web-client     Started
```

---

## 🌐 访问系统

### 管理后台（管理员使用）
- **URL:** http://localhost:8081
- **默认账号:** 
  - 用户名：`admin`
  - 密码：`Admin@123`

⚠️ **首次登录后请立即修改密码！**

### 用户聊天界面（普通用户使用）
- **URL:** http://localhost:8080
- **账号:** 由管理员创建并分配

---

## 📱 使用流程

### 管理员操作流程

1. **登录管理后台**
   - 访问 http://localhost:8081
   - 使用默认账号登录

2. **创建用户**
   - 点击"创建用户"
   - 填写用户名（6-20 位，字母数字下划线）
   - 填写密码（8-16 位，包含大写 + 小写 + 数字 + 特殊符号）
   - 点击"创建用户"
   - **记录生成的用户名和密码**

3. **交付账号**
   - 将用户名和密码通过线下方式（微信、邮件、口头等）交付给用户
   - 提醒用户首次登录后修改密码

4. **管理用户**
   - 点击"用户列表"查看所有用户
   - 可以禁用/启用用户
   - 可以删除用户

### 普通用户使用流程

1. **登录聊天界面**
   - 访问 http://localhost:8080
   - 输入管理员分配的用户名和密码
   - 点击"登录"

2. **开始聊天**
   - 搜索其他用户
   - 发起私聊
   - 加入群组聊天

---

## 🔧 常用命令

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f admin-server
docker-compose logs -f message-server
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart admin-server
```

### 停止服务
```bash
# 停止所有服务（保留数据）
docker-compose down

# 停止并删除数据（慎用！）
docker-compose down -v
```

### 更新代码
```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

---

## 🐛 常见问题

### 1. 端口被占用

**错误信息:** `Bind for 0.0.0.0:8080 failed: port is already allocated`

**解决方法:**
```bash
# 查看占用端口的进程
# Windows:
netstat -ano | findstr :8080

# macOS/Linux:
lsof -i :8080

# 停止占用端口的进程，或修改 docker-compose.yml 中的端口映射
```

### 2. Docker 无法启动

**Windows/macOS:**
- 确保 Docker Desktop 已启动（右下角图标为绿色）
- 重启 Docker Desktop

**Linux:**
```bash
# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker
```

### 3. 数据库初始化失败

**症状:** 登录后提示"用户不存在"

**解决方法:**
```bash
# 删除数据库容器和数据
docker-compose down -v

# 重新启动（会重新初始化数据库）
docker-compose up -d
```

### 4. 无法访问管理后台

**检查步骤:**
1. 确认容器运行正常：`docker-compose ps`
2. 查看日志：`docker-compose logs admin-web`
3. 检查防火墙是否开放 8081 端口
4. 尝试访问：http://127.0.0.1:8081

---

## 🔐 安全建议

### 生产环境部署

1. **修改默认密码**
   - 首次登录后立即修改 admin 密码

2. **修改密钥**
   - 编辑 `docker-compose.yml`
   - 修改 `SECRET_KEY` 为随机字符串
   ```yaml
   - SECRET_KEY=your-random-secret-key-here
   ```

3. **使用 HTTPS**
   - 配置反向代理（Nginx/Caddy）
   - 申请 SSL 证书（Let's Encrypt 免费）

4. **限制访问**
   - 配置防火墙
   - 仅允许信任 IP 访问管理后台

5. **定期备份**
   ```bash
   # 备份数据库
   docker exec clawchats-db pg_dump -U postgres clawchats > backup-$(date +%Y%m%d).sql
   ```

---

## 📊 服务端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| Admin Web | 8081 | 管理后台（管理员专用） |
| Web Client | 8080 | 用户聊天界面 |
| Admin Server | 8766 | 管理 API |
| Message Server | 8765 | WebSocket 消息服务 |
| PostgreSQL | 5432 | 数据库（不建议暴露） |

---

## 💡 下一步

- [ ] 修改管理员密码
- [ ] 创建第一批用户账号
- [ ] 测试聊天功能
- [ ] 配置 HTTPS（生产环境）
- [ ] 设置定期备份

---

## 📞 获取帮助

- **GitHub Issues:** https://github.com/q4speed/claw-chats/issues
- **文档:** https://github.com/q4speed/claw-chats/tree/main/docs

---

*Last updated: 2026-03-11*
