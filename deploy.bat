@echo off
REM 🦞 ClawChats 快速部署脚本 (Windows)

echo 🦞 ClawChats 快速部署
echo ======================
echo.

REM 检查 Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Docker，请先安装 Docker Desktop
    echo    访问：https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Docker Compose
    pause
    exit /b 1
)

echo ✅ Docker 已安装
echo ✅ Docker Compose 已安装
echo.

REM 启动服务
echo 🚀 启动服务...
docker-compose up -d

echo.
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo.
echo 📊 服务状态:
docker-compose ps

echo.
echo ✅ 部署完成！
echo.
echo 🌐 访问地址:
echo    管理后台：http://localhost:8081
echo    用户聊天：http://localhost:8080
echo.
echo 🔐 默认管理员账号:
echo    用户名：admin
echo    密码：Admin@123
echo.
echo ⚠️  首次登录后请立即修改密码！
echo.
echo 📖 详细文档：DEPLOY.md
echo.
pause
