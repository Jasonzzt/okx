# 🤖 AI智能加密货币交易分析系统

基于 DeepSeek AI 的加密货币交易分析系统，支持 OKX 交易所实时行情分析，提供智能交易建议和邮件提醒。

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

## ✨ 核心特性

### 📊 多策略支持
- **激进短线** (5分钟K线) - 适合全天盯盘
- **平衡策略** (15分钟K线) - 推荐配置 ⭐
- **保守长线** (1小时K线) - 适合偶尔查看

### 🤖 AI智能分析
- DeepSeek AI 深度分析市场数据
- 实时行情监控（Ticker、K线、订单簿、成交记录）
- 技术指标计算（RSI、SMA、成交量分析）
- 支撑位/阻力位识别

### 💼 持仓管理
- 多持仓跟踪（支持做多/做空）
- 实时盈亏计算
- 动态止盈止损调整
- 持仓状态智能识别

### 📧 邮件提醒
- 关键操作邮件通知
- 支持 QQ/Gmail/163 等邮箱
- HTML格式邮件，清晰易读
- 可配置提醒阈值

### 💾 数据存储
- SQLite 数据库存储分析历史
- 完整的市场数据记录
- 邮件发送记录追踪

---

## 🚀 快速开始

### 1️⃣ 系统要求

- Python 3.10+
- 网络连接（访问 OKX API 和 DeepSeek API）

### 2️⃣ 克隆项目

```bash
git clone https://github.com/yourusername/okx-trading-bot.git
cd okx-trading-bot
```

### 3️⃣ 安装依赖

使用 uv（推荐，更快）：
```bash
# 安装 uv（如果还没安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖（自动创建虚拟环境）
uv sync

# 或手动创建虚拟环境
uv venv
source .venv/bin/activate  # Linux/Mac
uv pip install -r requirements.txt
```

### 4️⃣ 配置环境变量

复制配置模板：
```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=你的DeepSeek_API密钥
DEEPSEEK_MODEL=deepseek-ai/DeepSeek-V3.1-Terminus
BASE_URL=https://api.siliconflow.cn/v1

# 邮件配置（QQ邮箱）
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465
SENDER_EMAIL=你的QQ邮箱@qq.com
SENDER_PASSWORD=你的QQ邮箱授权码
RECEIVER_EMAIL=接收邮件的邮箱@qq.com

# 交易配置
INST_ID=ETH-USDT-SWAP
TRADING_STRATEGY=balanced  # aggressive/balanced/conservative
```

#### 📝 获取配置项

**DeepSeek API Key**：
1. 访问 [SiliconFlow](https://cloud.siliconflow.cn/)
2. 注册并创建 API Key
3. 复制到 `DEEPSEEK_API_KEY`

**QQ邮箱授权码**：
1. 登录 [QQ邮箱](https://mail.qq.com)
2. 设置 → 账户 → 开启 IMAP/SMTP 服务
3. 生成授权码（16位）
4. 复制到 `SENDER_PASSWORD`

详细配置说明：
- 📖 [QQ邮箱配置指南](QQ_EMAIL_GUIDE.md)
- 📖 [策略选择指南](STRATEGY_GUIDE.md)

### 5️⃣ 测试邮件配置

```bash
uv run test_qq_email.py
```

成功后会收到测试邮件 ✅

### 6️⃣ 启动系统

```bash
uv run main.py
```


---

## 📖 使用指南

### 策略选择

系统提供三种交易策略：

| 策略 | K线周期 | 分析频率 | 适合人群 |
|-----|--------|---------|---------|
| **激进短线** | 5分钟 | 每1分钟 | 全天盯盘 |
| **平衡策略** ⭐ | 15分钟 | 每3分钟 | 工作间隙 |
| **保守长线** | 1小时 | 每10分钟 | 偶尔查看 |

切换策略：编辑 `.env` 中的 `TRADING_STRATEGY`

```env
TRADING_STRATEGY=balanced  # aggressive/balanced/conservative
```

详细对比：[策略选择指南](STRATEGY_GUIDE.md)

### 持仓管理

编辑 `positions.json` 记录你的持仓：

```json
[
  {
    "inst_id": "ETH-USDT-SWAP",
    "size": 1.0,
    "entry_price": 3750.00,
    "direction": "long",
    "leverage": 10,
    "take_profit": 3900.00,
    "stop_loss": 3680.00,
    "open_time": "2025-11-03T20:00:00"
  }
]
```

详细说明：[持仓管理指南](POSITIONS_GUIDE.md)

### 邮件提醒规则

系统会在以下情况发送邮件（需满足信心度阈值）：

- ✅ **买多** (BUY_LONG)
- ✅ **买空** (BUY_SHORT)
- ✅ **卖出** (SELL)
- ✅ **大幅调整止盈止损** (调整幅度超过策略阈值)
- ✅ **紧急操作** (urgent_action)

邮件示例：

```
🚨 交易提醒 - ETH-USDT-SWAP

建议操作：买多 (BUY_LONG)
当前价格：3735.50 USDT
信心水平：82%

分析摘要：
价格突破阻力位，RSI显示超卖反弹...

详细理由：
技术指标显示明确买入信号...
```

---

## 📂 项目结构

```
okx-trading-bot/
├── main.py                 # 主程序入口
├── config.py               # 配置管理
├── strategy_config.py      # 策略配置
├── trading_bot.py          # 交易分析机器人
├── deepseek_analyzer.py    # AI分析器
├── market_data.py          # 市场数据获取
├── email_notifier.py       # 邮件通知
├── db.py                   # 数据库操作
├── positions.json          # 持仓记录
├── .env                    # 环境配置
├── requirements.txt        # Python依赖
│
├── logs/                   # 日志文件
│   └── trading_bot_YYYYMMDD.log
│
├── tests/                  # 测试脚本
│   ├── test_qq_email.py
│   └── test_email_587.py
│
└── docs/                   # 文档
    ├── README.md
    ├── STRATEGY_GUIDE.md
    ├── POSITIONS_GUIDE.md
    ├── QQ_EMAIL_GUIDE.md
    └── QUICK_STRATEGY_SWITCH.md
```

---

## ⚙️ 配置说明

### 策略参数

| 策略 | 止盈目标 | 止损幅度 | 信心阈值 | 邮件阈值 |
|-----|---------|---------|---------|---------|
| 激进 | 1.5% | 1.0% | 70% | 1.2% |
| 平衡 | 3.0% | 1.5% | 75% | 2.0% |
| 保守 | 5.0% | 2.5% | 80% | 3.0% |

### 手动覆盖参数

在 `.env` 中可以手动覆盖策略默认参数：

```env
TRADING_STRATEGY=balanced

# 手动覆盖（可选）
ANALYSIS_INTERVAL=120        # 自定义分析间隔
CONFIDENCE_THRESHOLD=70.0    # 自定义信心阈值
K_LINE_PERIOD=10m            # 自定义K线周期
```

---

## 🔧 高级用法

### 后台运行

#### 使用 nohup
```bash
nohup uv run main.py > output.log 2>&1 &
```

#### 使用 screen
```bash
screen -S trading-bot
uv run main.py
# Ctrl+A+D 分离会话
```

#### 使用 tmux
```bash
tmux new -s trading-bot
uv run main.py
# Ctrl+B+D 分离会话
```

---

## 📊 监控和日志

### 日志文件

日志存储在 `logs/` 目录：

- `trading_bot.log` - 通用日志
- `trading_bot_YYYYMMDD.log` - 按日期归档

实时查看日志：

```bash
tail -f logs/trading_bot_$(date +%Y%m%d).log
```


## 🐛 故障排除

### 常见问题

#### 1. DeepSeek API 502 错误

**原因**：API服务暂时不可用

**解决**：
- 等待1-2分钟后自动重试
- 检查 API Key 是否有效
- 查看 API 配额是否用完

#### 2. 邮件发送超时

**原因**：网络问题或端口被阻

**解决**：
- QQ邮箱：使用端口465（SSL）
- Gmail：使用端口587（STARTTLS）或使用VPN
- 163邮箱：使用端口465（SSL）

测试邮件：
```bash
python3 test_qq_email.py
```

#### 3. 导入模块错误

**原因**：依赖未安装

**解决**：
```bash
pip install -r requirements.txt
```

#### 4. positions.json 格式错误

**原因**：JSON格式不正确

**解决**：
- 检查 JSON 语法（逗号、引号、括号）
- 使用 JSON 验证工具
- 参考 `POSITIONS_GUIDE.md`

#### 5. 数据库锁定

**原因**：多个进程同时访问

**解决**：
```bash
# 停止所有实例
pkill -f "uv run main.py"

# 重新启动
uv run main.py
```

---

## 🔒 安全建议

### API密钥安全

- ✅ 不要将 `.env` 文件提交到 Git
- ✅ 使用环境变量存储敏感信息
- ✅ 定期更换 API Key
- ✅ 限制 API Key 权限（只读）

### 资金安全

- ⚠️ **本系统仅提供分析建议，不执行交易**
- ⚠️ 所有交易决策需人工确认
- ⚠️ 不要盲目跟随AI建议
- ⚠️ 做好风险控制和资金管理

### 邮件安全

- ✅ 使用授权码而非密码
- ✅ 不要共享授权码
- ✅ 定期检查邮箱登录记录

---

## 📈 性能优化

### 减少API调用

- 调整 `ANALYSIS_INTERVAL` 增加分析间隔
- 使用保守策略减少分析频率

### 降低资源占用

- 限制K线数据量（`kline_limit`）
- 清理旧日志文件
- 定期清理数据库（保留最近数据）

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 报告问题

请在 GitHub Issues 中提供：
- 详细的错误描述
- 复现步骤
- 日志输出
- 系统环境信息

### 提交代码

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## ⚠️ 免责声明

**重要提示**：

1. **仅供学习研究使用**
   - 本系统仅用于技术学习和研究
   - 不构成任何投资建议

2. **AI分析局限性**
   - AI分析可能不准确
   - 市场瞬息万变
   - 历史表现不代表未来

3. **风险警告**
   - 加密货币交易风险极高
   - 可能导致本金全部损失
   - 请根据自身情况谨慎决策

4. **责任声明**
   - 使用本系统造成的任何损失
   - 开发者不承担任何责任
   - 用户需自行承担所有风险

**请在充分了解风险的前提下使用本系统！**


## 🙏 致谢

- [OKX](https://www.okx.com/) - 提供市场数据API
- [DeepSeek](https://www.deepseek.com/) - 提供AI分析能力
- [SiliconFlow](https://cloud.siliconflow.cn/) - 提供API服务
- 所有贡献者和使用者

---

## 📚 相关文档

- 📖 [策略选择指南](STRATEGY_GUIDE.md)
- 📖 [持仓管理指南](POSITIONS_GUIDE.md)
- 📖 [QQ邮箱配置](QQ_EMAIL_GUIDE.md)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star！⭐**

Made with ❤️ by AI Trading Community

</div>
