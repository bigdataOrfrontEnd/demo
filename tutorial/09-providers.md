# 模块 09: AI 提供商管理 (Providers)

> **API 前缀**: `/api/providers`  
> **源码**: `src/web/api/providers.py`  
> **认证要求**: 是  
> **数据库表**: `ai_services`, `ai_models`

## 模块概述

AI 提供商模块管理用户配置的 AI 服务商和模型。一个服务商可以关联多个模型，可设置默认模型。

## 数据模型

### AIService 表 (ai_services)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR | 服务商名称 (如 "智谱") |
| base_url | VARCHAR | API 端点 URL |
| api_key | VARCHAR | API 密钥 |

### AIModel 表 (ai_models)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | VARCHAR | 显示名 (如 "GLM-4-Flash") |
| service_id | FK(ai_services) | 所属服务商 |
| model | VARCHAR | 实际模型标识 (如 "glm-4-flash") |
| is_default | BOOLEAN | 是否为系统默认 |

## API 端点

### 服务商管理

#### GET /api/providers/services

获取所有 AI 服务商列表（含关联模型）。

#### POST /api/providers/services

创建服务商。

**请求体**:
```json
{
  "name": "DeepSeek",
  "base_url": "https://api.deepseek.com/v1",
  "api_key": "sk-xxx"
}
```

#### PUT /api/providers/services/{service_id}

更新服务商信息。

#### DELETE /api/providers/services/{service_id}

删除服务商（级联删除关联模型）。

### 模型管理

#### GET /api/providers/models

获取所有 AI 模型列表。

#### POST /api/providers/models

创建模型。

**请求体**:
```json
{
  "name": "DeepSeek-Chat",
  "service_id": 1,
  "model": "deepseek-chat",
  "is_default": true
}
```
设置 `is_default=true` 会自动将其他模型设为非默认。

#### PUT /api/providers/models/{model_id}

更新模型信息。

#### DELETE /api/providers/models/{model_id}

删除模型。

#### POST /api/providers/models/{model_id}/test

测试模型连接。

**响应**:
```json
{
  "ok": true,
  "reply": "OK"
}
```
或失败时返回 400：
```json
{
  "detail": "测试失败: Connection timeout"
}
```

## 模型选择优先级

当 Agent 需要调用 AI 时，按以下优先级选择模型：

```
1. StockAgent 级别: 股票- Agent 绑定中指定的 ai_model_id
2. AgentConfig 级别: Agent 设置的默认 ai_model_id
3. 系统默认: ai_models 中 is_default=true 的模型
4. 回退: 取数据库中第一个模型
5. 环境变量: Settings.ai_model（最后兜底）
```

## 测试接口

`/api/providers/models/{model_id}/test` 会向模型发送简单对话测试：

```python
client.chat(
    system_prompt="You are a helpful assistant.",
    user_content="Say 'OK' in one word.",
    temperature=0,
)
```

## 使用场景

- 设置页面配置 AI 服务商和模型
- 可支持 OpenAI、DeepSeek、智谱等任意兼容 OpenAI API 的服务
- 测试按钮验证 API 密钥和连接是否正常
