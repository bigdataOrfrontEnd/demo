# 模块 01: 认证 (Auth)

> **API 前缀**: `/api/auth`  
> **源码**: `src/web/api/auth.py`  
> **认证要求**: 否（这是设置认证的入口）

## 模块概述

认证模块提供简单的单用户 JWT 认证系统。首次启动时无密码，所有 API 可公开访问；通过 `/api/auth/setup` 首次设置用户名密码后，所有受保护路由需要 Bearer Token。

## 认证流程

```
首次启动 → 无密码 → 所有 API 公开
         → 调用 POST /api/auth/setup 设置密码
         → 获得 JWT Token (30天有效期)
         → 后续请求携带 Authorization: Bearer <token>
         → Token 过期需重新登录
```

## 数据存储

认证信息存储在 `app_settings` 表中：

| Key | 用途 |
|-----|------|
| `auth_username` | 用户名 |
| `auth_password_hash` | SHA256 密码哈希 |
| `jwt_secret` | JWT 签名密钥 (首次自动生成 64位随机hex) |

## Docker 部署

通过环境变量可在启动时自动初始化账号：

- `AUTH_USERNAME` — 用户名
- `AUTH_PASSWORD` — 密码
- `JWT_SECRET` — 自定义 JWT 密钥（可选）

## API 端点

### GET /api/auth/status

获取认证状态（是否已设置密码）。

**响应示例**：
```json
{
  "initialized": false
}
```

### POST /api/auth/setup

首次设置用户名和密码。仅当系统未初始化时可用。

**请求体**：
```json
{
  "username": "admin",
  "password": "123456"
}
```
- 用户名至少 2 位
- 密码至少 6 位

**响应**：
```json
{
  "token": "eyJhbGciOi...",
  "expires_at": "2026-06-20T12:00:00+00:00"
}
```

### POST /api/auth/login

登录并获取 Token。需要系统已初始化。

**请求体**：
```json
{
  "username": "admin",
  "password": "123456"
}
```

**响应**：同 setup，返回 token 和过期时间。

### POST /api/auth/change-password

修改密码（需已登录）。

**请求体**：
```json
{
  "username": "admin",
  "password": "newpassword"
}
```

**响应**：
```json
{
  "message": "密码已更新"
}
```

### GET /api/auth/me

获取当前登录用户信息。

**响应**：
```json
{
  "user": "user"
}
```

## 关键实现细节

### JWT 配置
- 算法：HS256
- 有效期：30 天
- Secret：优先环境变量 `JWT_SECRET`，否则从数据库读取，首次自动生成

### 密码存储
使用 SHA256 哈希，存储哈希值而非明文：
```python
hashlib.sha256(password.encode()).hexdigest()
```

### 中间件保护
所有受保护的路由通过依赖注入 `get_current_user` 进行验证：
```python
protected = [Depends(get_current_user)]
app.include_router(stocks.router, ..., dependencies=protected)
```

如果系统未初始化（无密码），`get_current_user` 返回 `None`，允许通过。
如果已初始化但无 Token 或 Token 过期，返回 401。

### auth/me API 的特殊性
`/api/auth/me` 在未设置密码时返回 `{"user": "guest"}`，前端据此判断是否需要显示初始化页面。
