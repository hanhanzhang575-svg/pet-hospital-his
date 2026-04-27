# FastAPI 服务启动诊断报告

**生成时间**: 2024年  
**项目**: 白之助宠物医院信息管理系统 (Shironosuke Pet Hospital IS)  
**目标**: 修复本地 FastAPI 服务无法访问的问题

---

## 🔍 诊断概览

根据初步诊断，**项目存在 SQLite3 DLL 加载错误**，导致：
- ❌ SQLAlchemy 无法导入（依赖 sqlite3）
- ❌ 数据库初始化失败
- ❌ FastAPI 应用无法启动
- ❌ http://127.0.0.1:8000/docs 无法访问

**根本原因**: 虚拟环境中的 Miniconda Python 3.9.12 与系统 Python 3.13.4 之间存在库不兼容

---

## 🚀 快速修复（5分钟方案）

### 方案 A：使用系统 Python（推荐 - 最快）

**优点**: 无需重建虚拟环境，立即可用  
**缺点**: 依赖系统全局环境

**步骤**:

```batch
cd C:\Users\zhangmohan\Desktop\信息系统

REM 1. 安装依赖到系统 Python
python -m pip install fastapi uvicorn sqlalchemy python-jose passlib apscheduler networkx chromadb httpx python-multipart

REM 2. 验证导入
python -c "import backend.main; print('SUCCESS')"

REM 3. 启动服务器
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

REM 4. 访问
REM 打开浏览器访问 http://127.0.0.1:8000/docs
```

**完整一行命令**:
```batch
python -m pip install fastapi uvicorn sqlalchemy python-jose passlib apscheduler networkx chromadb httpx python-multipart && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

---

### 方案 B：重建虚拟环境（完整 - 10分钟）

**优点**: 干净的隔离环境，不影响系统  
**缺点**: 需要一些时间

**步骤**:

```batch
cd C:\Users\zhangmohan\Desktop\信息系统

REM 1. 删除旧 venv
rmdir .venv /s /q

REM 2. 创建新 venv
python -m venv .venv

REM 3. 激活 venv
.venv\Scripts\activate.bat

REM 4. 升级 pip
python -m pip install --upgrade pip

REM 5. 安装依赖
pip install -r backend\requirements.txt

REM 6. 验证
python -c "import sqlite3; print('SQLite3:', sqlite3.version)"
python -c "import backend.main; print('Backend OK')"

REM 7. 启动服务
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

---

### 方案 C：使用提供的批处理脚本（全自动）

```batch
REM 直接运行现成脚本（无需逐步输入）
C:\Users\zhangmohan\Desktop\信息系统\start_server.bat
```

---

## 📋 环境信息

| 项目 | 值 |
|------|-----|
| **系统 Python** | C:\Users\zhangmohan\AppData\Local\Programs\Python\Python313\python.exe |
| **系统 Python 版本** | 3.13.4 |
| **项目根目录** | C:\Users\zhangmohan\Desktop\信息系统 |
| **虚拟环境位置** | .\.venv |
| **虚拟环境 Python 版本** | 3.9.12 (Miniconda) |
| **FastAPI 版本需求** | >=0.115,<0.117 |
| **Uvicorn 版本需求** | >=0.34,<0.36 |
| **SQLAlchemy 版本需求** | >=2.0,<2.1 |

---

## ✅ 验证清单

成功启动后，您应该看到：

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

然后可以访问以下 URL：

| URL | 说明 |
|-----|------|
| http://127.0.0.1:8000/docs | **Swagger UI (推荐)** |
| http://127.0.0.1:8000/redoc | ReDoc 文档 |
| http://127.0.0.1:8000/openapi.json | OpenAPI schema |
| http://127.0.0.1:8000/api/v1 | API 根路径（探活） |

---

## 🔧 依赖列表

**核心依赖** (`backend/requirements.txt`):

```
fastapi>=0.115,<0.117          # Web 框架
uvicorn>=0.34,<0.36            # ASGI 服务器
SQLAlchemy>=2.0,<2.1           # ORM
python-jose[cryptography]>=3.3,<4    # JWT 认证
passlib[bcrypt]>=1.7,<2        # 密码哈希
python-multipart>=0.0.9,<1     # 表单处理
apscheduler>=3.10,<4           # 后台定时任务
networkx>=3.4,<4               # 图算法（笼舍分配）
chromadb>=1.0,<2               # 向量数据库（RAG）
httpx>=0.28,<1                 # 异步 HTTP 客户端
```

---

## 🐛 常见问题

### Q: 安装依赖时很慢或超时？
**A**: 尝试使用清华大学 PyPI 镜像：
```batch
python -m pip install -r backend\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: 端口 8000 被占用？
**A**: 检查占用该端口的进程：
```powershell
Get-NetTCPConnection -LocalPort 8000 | Format-Table
```
或改用其他端口：
```batch
python -m uvicorn backend.main:app --port 8001
```

### Q: SQLite DLL 仍然加载失败？
**A**: 确保不混用不同 Python 版本的虚拟环境：
```batch
REM 检查当前激活的 Python 路径
python -c "import sys; print(sys.executable)"

REM 如果输出不是 .venv 中的路径，请先激活虚拟环境或使用系统 Python
```

### Q: 导入 backend.main 仍然失败？
**A**: 检查项目结构并确保在项目根目录：
```batch
dir backend\*.py
REM 应该显示: main.py, database.py, auth.py, scheduler.py 等
```

---

## 📝 提供的脚本文件

已在项目根目录创建以下辅助脚本：

| 文件 | 用途 |
|------|------|
| `start_server.bat` | **推荐使用** - 一键启动服务器 |
| `start_server.py` | Python 版本启动脚本 |
| `quick_start.py` | 快速诊断+启动 |
| `diagnose_and_fix.py` | 详细诊断脚本 |
| `fix_venv_ascii.py` | 虚拟环境重建脚本 |
| `run_fix_sqlite.bat` | SQLite 修复脚本 |

**推荐使用顺序**:
1. 首先尝试 `start_server.bat`
2. 如果失败，运行 `diagnose_and_fix.py` 了解具体问题
3. 根据诊断结果选择方案 A、B 或 C

---

## 🎯 成功标志

✅ **服务启动成功的表现**:
- 终端显示 `Uvicorn running on http://127.0.0.1:8000`
- 浏览器可以打开 http://127.0.0.1:8000/docs
- 能看到 Swagger 文档界面（蓝色的 API 文档页面）
- 可以展开 `/api/v1` 路由查看所有可用端点

---

## 📞 如果仍然无法解决

1. **查看完整错误日志**：
   ```batch
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 2>&1 | tee error_log.txt
   ```

2. **运行诊断脚本获取详细信息**：
   ```batch
   python diagnose_and_fix.py > diagnostic_output.txt 2>&1
   ```

3. **检查 Python 和 pip 版本**：
   ```batch
   python --version
   pip --version
   pip list | findstr /I "fastapi uvicorn sqlalchemy"
   ```

4. **验证项目文件完整性**：
   ```batch
   dir backend\main.py
   dir backend\database.py
   dir backend\requirements.txt
   ```

---

## 📚 项目背景

**项目名称**: 白之助宠物医院信息管理系统  
**技术栈**:
- 后端: FastAPI + SQLAlchemy + SQLite（WAL 模式）
- 前端: Vue 3 + Vite + Element Plus
- AI 模块: NetworkX + ChromaDB + DeepSeek API

**核心功能**:
- 宠物档案和主人管理
- 门诊挂号和预约系统
- 住院管理和笼舍分配
- 处方和药品库存管理
- 医生工作台和 AI 辅助诊断
- 后台定时任务和监控

---

**生成日期**: 2024  
**诊断工具版本**: 1.0
