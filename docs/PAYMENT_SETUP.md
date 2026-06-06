# 支付功能配置文档

## 概述

本文档说明如何配置星伴守护的支付功能，包括微信支付和支付宝支付。

## 当前状态

- ✅ 支付接口框架已完成
- ✅ 模拟支付功能可用
- ⏳ 真实支付API需要商户配置

## 配置步骤

### 1. 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# 微信支付配置
WECHAT_APP_ID=your_wechat_app_id
WECHAT_MCH_ID=your_wechat_mch_id
WECHAT_API_KEY=your_wechat_api_key
WECHAT_CERT_PATH=/path/to/your/apiclient_cert.p12

# 支付宝配置
ALIPAY_APP_ID=your_alipay_app_id
ALIPAY_PRIVATE_KEY=your_alipay_private_key
ALIPAY_PUBLIC_KEY=your_alipay_public_key
ALIPAY_GATEWAY=https://openapi.alipay.com/gateway.do
```

### 2. 微信支付配置

#### 2.1 申请商户号

1. 访问 [微信支付商户平台](https://pay.weixin.qq.com/)
2. 注册企业/个体工商户账户
3. 完成身份认证和账户验证
4. 获取以下信息：
   - 商户号（MCH_ID）
   - API密钥
   - 商户证书

#### 2.2 配置应用

1. 登录微信公众平台/开放平台
2. 创建小程序/公众号应用
3. 获取 AppID
4. 在商户平台配置支付授权目录

#### 2.3 配置支付回调

在微信支付商户平台配置：
- 支付通知URL: `https://your-domain.com/api/payment/wechat/callback`
- 退款通知URL: `https://your-domain.com/api/payment/wechat/refund-callback`

### 3. 支付宝配置

#### 3.1 申请商户号

1. 访问 [支付宝开放平台](https://open.alipay.com/)
2. 注册企业账户
3. 完成实名认证
4. 创建应用并获取 AppID

#### 3.2 配置密钥

1. 使用支付宝开放平台开发助手生成密钥
2. 上传应用公钥
3. 获取支付宝公钥
4. 配置接口加签方式（推荐使用RSA2）

#### 3.3 配置支付回调

在支付宝开放平台配置：
- 异步通知URL: `https://your-domain.com/api/payment/alipay/callback`
- 同步跳转URL: `https://your-domain.com/payment/success`

## 支付接口说明

### 创建订单（微信）

**接口:** `POST /api/payment/wechat/create`

**请求参数:**
```json
{
  "amount": 29.9,
  "type": "membership",
  "product_id": "monthly"
}
```

**响应:**
```json
{
  "success": true,
  "order_id": "XG12345678901234",
  "payment_type": "wechat",
  "qrcode_data": "weixin://wxpay/bizpayurl?pr=xxx",
  "timestamp": 1234567890,
  "nonce_str": "xxx",
  "prepay_id": "xxx",
  "sign": "xxx"
}
```

### 创建订单（支付宝）

**接口:** `POST /api/payment/alipay/create`

**请求参数:**
```json
{
  "amount": 29.9,
  "type": "membership",
  "product_id": "monthly"
}
```

**响应:**
```json
{
  "success": true,
  "order_id": "XG12345678901234",
  "payment_type": "alipay",
  "qrcode_data": "alipay://platformapi/startapp?saId=10000007&qrcode=xxx",
  "trade_no": "202312312345678901234567"
}
```

### 查询订单状态

**接口:** `GET /api/payment/query/<order_id>`

**响应:**
```json
{
  "order_id": "XG12345678901234",
  "amount": 29.9,
  "payment_type": "wechat",
  "status": "paid",
  "created_at": "2024-01-01 00:00:00",
  "paid_at": "2024-01-01 00:05:00"
}
```

## 测试方法

### 使用模拟支付

在开发环境中，系统提供模拟支付功能：

```bash
# 模拟支付回调
curl -X POST http://localhost:5000/api/payment/callback/mock \
  -H "Content-Type: application/json" \
  -d '{"order_id": "XG12345678901234"}'
```

### 测试订单流程

1. 登录应用
2. 进入会员中心
3. 选择套餐并点击支付
4. 获取支付二维码
5. 使用模拟支付完成支付
6. 检查会员状态是否更新

## 会员套餐

系统预置了以下会员套餐：

| 套餐 | 价格 | 时长 | 功能 |
|------|------|------|------|
| 月度会员 | ¥29.9 | 30天 | AI无限畅聊、安全升级、优先客服 |
| 季度会员 | ¥79.9 | 90天 | 以上+额外权益 |
| 年度会员 | ¥299.0 | 365天 | 以上+额外权益+专属服务 |

## 安全注意事项

1. **密钥保护**
   - 不要将API密钥提交到版本控制
   - 使用环境变量管理密钥
   - 定期更换密钥

2. **支付安全**
   - 验证支付回调签名
   - 检查订单金额和状态
   - 防止重复支付

3. **数据安全**
   - 加密存储敏感数据
   - 定期备份订单数据
   - 记录支付操作日志

4. **合规要求**
   - 遵守当地支付相关法律法规
   - 提供用户协议和隐私政策
   - 保存交易记录备查

## 常见问题

### Q: 支付后会员没有开通？
A: 检查支付回调是否正常接收，订单状态是否更新为 'paid'

### Q: 如何处理退款？
A: 系统目前不支持自动退款，需要手动处理。未来版本会添加退款接口

### Q: 可以测试真实支付吗？
A: 可以使用微信支付沙箱环境或支付宝沙箱环境进行测试

### Q: 支持其他支付方式吗？
A: 当前仅支持微信支付和支付宝。可以扩展支持其他支付方式

## 技术支持

如遇到问题，请查看：
- 后端日志: 检查 `/api/payment` 相关的错误日志
- 支付平台文档: 微信支付和支付宝官方文档
- 系统文档: 本文档和 README.md

## 更新日志

- v1.0.0 - 初始版本，支持微信支付和支付宝基础功能
