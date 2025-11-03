# 🎯 策略快速切换指南

## 一、当前配置（平衡策略）

你现在使用的是 **平衡策略 (balanced)** ⭐

```
📈 K线周期: 15分钟
⏰ 分析间隔: 3分钟 (180秒)
🎯 信心阈值: 75%
💰 止盈/止损: 3% / 1.5%
📧 邮件阈值: 调整>2%
```

这是**推荐配置**，适合大多数交易者！

---

## 二、如何切换策略？

### 方法：编辑 `.env` 文件

找到这一行：
```env
TRADING_STRATEGY=balanced
```

改成你想要的策略：

#### 选项1: 激进短线（更快）
```env
TRADING_STRATEGY=aggressive
```
- ⚡ 5分钟K线，1分钟分析
- 🎯 适合全天盯盘
- 📊 日均5-10次交易

#### 选项2: 平衡策略（推荐）⭐
```env
TRADING_STRATEGY=balanced
```
- ⚖️ 15分钟K线，3分钟分析
- 💼 适合工作间隙查看
- 📊 日均3-5次交易

#### 选项3: 保守长线（更稳）
```env
TRADING_STRATEGY=conservative
```
- 🛡️ 1小时K线，10分钟分析
- 😌 适合偶尔查看
- 📊 日均1-2次交易

---

## 三、切换后重启

修改 `.env` 后，重启程序：

```bash
# 停止当前运行（Ctrl+C）
# 然后重新运行
python main.py
```

启动时会显示当前策略信息！

---

## 四、三种策略对比

| 特性 | 激进 🚀 | 平衡 ⚖️ | 保守 🛡️ |
|-----|--------|--------|--------|
| K线 | 5分钟 | 15分钟 | 1小时 |
| 分析 | 1分钟 | 3分钟 | 10分钟 |
| 信心 | 70% | 75% | 80% |
| 止盈 | 1.5% | 3% | 5% |
| 止损 | 1% | 1.5% | 2.5% |
| 邮件 | >1.2% | >2% | >3% |
| 频率 | 高 | 中 | 低 |
| 盯盘 | 全天 | 每小时 | 偶尔 |

---

## 五、我该选哪个？

### 🤔 快速决策

**你能盯盘多久？**
- 全天 → `aggressive`（激进）
- 每小时 → `balanced`（平衡）⭐
- 每天1-2次 → `conservative`（保守）

**你是什么水平？**
- 新手 → `conservative`（保守）
- 有经验 → `balanced`（平衡）⭐
- 老手 → 任意

**你的风格？**
- 追求刺激 → `aggressive`（激进）
- 平衡稳健 → `balanced`（平衡）⭐
- 求稳为主 → `conservative`（保守）

---

## 六、当前 .env 配置

你的 `.env` 文件应该是：

```env
# 交易配置
INST_ID=ETH-USDT-SWAP

# 策略选择: aggressive / balanced / conservative
TRADING_STRATEGY=balanced

# 以下参数会自动设置，通常不需要改
# ANALYSIS_INTERVAL=180
# CONFIDENCE_THRESHOLD=75.0
# K_LINE_PERIOD=15m
```

---

## 七、高级：手动微调

如果你想用某个策略，但调整部分参数：

```env
# 使用平衡策略
TRADING_STRATEGY=balanced

# 但我想更频繁分析（覆盖默认180秒）
ANALYSIS_INTERVAL=120

# 我想降低信心阈值（覆盖默认75%）
CONFIDENCE_THRESHOLD=70.0
```

这样会使用平衡策略的其他参数，但自定义这两项。

---

## 八、验证当前配置

运行这个命令查看当前配置：

```bash
python -c "from config import config; from strategy_config import print_strategy_info; print_strategy_info(config.trading.strategy_name)"
```

---

## 📚 更多信息

- 📖 完整对比：查看 `STRATEGY_GUIDE.md`
- 💼 持仓管理：查看 `POSITIONS_GUIDE.md`
- 📧 邮件规则：所有策略都在买多/买空/卖出/大幅调整时发邮件

---

## ⭐ 推荐配置

**新手**：`conservative`（保守长线）
**进阶**：`balanced`（平衡策略）⭐ 
**高手**：`aggressive`（激进短线）

大多数人应该用 **balanced**！

当前你就是用的这个，已经是推荐配置了！👍
