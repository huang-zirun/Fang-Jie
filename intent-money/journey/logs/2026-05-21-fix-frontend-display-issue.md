# 2026-05-21 - 修复前端目标列表显示问题

## 问题描述
前端页面只显示标题"今天你想怎么赚钱？"和副标题，但没有显示 4 个目标选项卡片。

## 问题排查过程

### 1. 初步检查
- 前端组件 `IntentSelect.vue` 代码正确，使用 `v-for` 渲染 `intents` 数组
- API 调用逻辑：`getIntents()` 返回数据后赋值给 `intents.value`
- 响应处理：`res.data.intents || res.data`（兼容不同响应格式）

### 2. 后端 API 检查
- API 路由：`/api/v1/intents` 正确注册
- 数据库表已创建，但种子数据未插入
- 后端启动时没有自动运行 `seed_all()` 函数

### 3. 第一次修复：添加数据库初始化
修改 `backend/app/main.py`，添加 `lifespan` 事件处理器：
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_all()
    yield

app = FastAPI(title="Intent Money OS", version="0.1.0", lifespan=lifespan)
```

### 4. 发现新问题：API 返回 500 错误
- 后端返回 `Internal Server Error`
- 数据库表存在但无数据
- 种子数据仍未被插入

### 5. 端口配置问题
- 后端运行在 `http://127.0.0.1:8080`
- 前端 Vite 代理配置：`target: 'http://localhost:8000'`
- 端口和主机都不匹配，导致前端 API 请求全部失败

### 6. 第二次修复：修正 Vite 代理配置
修改 `frontend/vite.config.ts`：
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8080',  // 从 localhost:8000 改为 127.0.0.1:8080
      changeOrigin: true,
    },
  },
}
```

### 7. 第三次修复：端口统一调整为 9090
根据用户需求，将后端端口从 8080 改为 9090：
- `server.py`：后端启动端口 `8080` → `9090`
- `vite.config.ts`：代理目标 `8080` → `9090`

## 修复结果
✅ 前端正常显示 4 个目标选项：
- 🎯 引流拿客户（可用）
- 💰 成交赚钱（即将开放）
- 🔗 裂变招募分销（即将开放）
- 📈 IP 长期增长（即将开放）

## 关键教训
1. **数据库初始化时机**：种子数据必须在应用启动时自动插入，不能依赖手动执行
2. **代理配置一致性**：前端代理目标必须与实际后端运行地址完全一致
3. **端口管理**：统一使用单一端口号（9090），避免混淆

## 当前状态
- 后端：http://127.0.0.1:9090 ✅
- 前端：http://localhost:5173 ✅
- API 文档：http://127.0.0.1:9090/docs ✅
- 数据库：SQLite (intent_money.db) ✅
- 种子数据：已自动插入 ✅

## 修改文件
1. `backend/app/main.py` - 添加 lifespan 事件处理器
2. `frontend/vite.config.ts` - 修正代理配置
3. `server.py` - 后端端口配置
