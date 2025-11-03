"""
交易策略配置
"""

class TradingStrategy:
    """交易策略枚举"""
    AGGRESSIVE = "aggressive"  # 激进短线（5分钟）
    BALANCED = "balanced"      # 平衡策略（15分钟）
    CONSERVATIVE = "conservative"  # 保守长线（1小时）


# 策略参数配置
STRATEGY_PARAMS = {
    "aggressive": {
        "name": "激进短线",
        "timeframe": "5m",
        "analysis_interval": 60,  # 1分钟分析一次
        "confidence_threshold": 70.0,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "profit_target": 1.5,  # 1.5% 止盈
        "stop_loss": 1.0,  # 1% 止损
        "adjustment_threshold": 1.2,  # 调整幅度 > 1.2% 发邮件
        "description": "5分钟级别，快进快出，适合全天盯盘"
    },
    "balanced": {
        "name": "平衡策略",
        "timeframe": "15m",
        "analysis_interval": 180,  # 3分钟分析一次
        "confidence_threshold": 75.0,
        "rsi_overbought": 75,
        "rsi_oversold": 25,
        "profit_target": 3.0,  # 3% 止盈
        "stop_loss": 1.5,  # 1.5% 止损
        "adjustment_threshold": 2.0,  # 调整幅度 > 2% 发邮件
        "description": "15分钟级别，兼顾机会和稳健，适合定时查看"
    },
    "conservative": {
        "name": "保守长线",
        "timeframe": "1H",
        "analysis_interval": 600,  # 10分钟分析一次
        "confidence_threshold": 80.0,
        "rsi_overbought": 80,
        "rsi_oversold": 20,
        "profit_target": 5.0,  # 5% 止盈
        "stop_loss": 2.5,  # 2.5% 止损
        "adjustment_threshold": 3.0,  # 调整幅度 > 3% 发邮件
        "description": "1小时级别，注重趋势，适合偶尔查看"
    }
}


def get_strategy_params(strategy: str = "balanced") -> dict:
    """
    获取策略参数
    
    Args:
        strategy: 策略类型 (aggressive/balanced/conservative)
    
    Returns:
        dict: 策略参数
    """
    if strategy not in STRATEGY_PARAMS:
        print(f"警告: 未知策略 '{strategy}'，使用默认平衡策略")
        strategy = "balanced"
    
    return STRATEGY_PARAMS[strategy]


def print_strategy_info(strategy: str):
    """
    打印策略信息
    
    Args:
        strategy: 策略类型
    """
    params = get_strategy_params(strategy)
    print("\n" + "="*60)
    print(f"📊 交易策略: {params['name']}")
    print("="*60)
    print(f"📈 K线周期: {params['timeframe']}")
    print(f"⏰ 分析间隔: {params['analysis_interval']}秒")
    print(f"🎯 信心阈值: {params['confidence_threshold']}%")
    print(f"📊 RSI超买/超卖: {params['rsi_overbought']}/{params['rsi_oversold']}")
    print(f"💰 止盈/止损: {params['profit_target']}% / {params['stop_loss']}%")
    print(f"📧 调整阈值: {params['adjustment_threshold']}%")
    print(f"📝 策略说明: {params['description']}")
    print("="*60 + "\n")
