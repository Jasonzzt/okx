import os
from dataclasses import dataclass
from typing import Optional
from strategy_config import get_strategy_params

@dataclass
class DeepSeekConfig:
    api_key: str
    base_url: str = "https://api.siliconflow.cn/v1"  # 硅基流动API https://cloud.siliconflow.cn/
    model: str = "deepseek-ai/DeepSeek-R1"

@dataclass
class EmailConfig:
    smtp_server: str
    smtp_port: int
    sender_email: str
    sender_password: str
    receiver_email: str

@dataclass
class TradingConfig:
    inst_id: str = "ETC-USDT-SWAP"
    analysis_interval: int = 30  # seconds
    confidence_threshold: float = 80.0  # 信心阈值，超过此值发送邮件提醒
    kline_bar: str = "5m"
    kline_limit: int = 100
    orderbook_size: int = 20
    trades_limit: int = 50
    strategy_name: str = "balanced"  # 策略名称
    adjustment_threshold: float = 2.0  # 调整阈值

@dataclass
class DatabaseConfig:
    db_path: str = "trading_analysis.db"

class Config:
    def __init__(self):
        # 获取策略配置
        strategy_name = os.getenv("TRADING_STRATEGY", "balanced")
        strategy_params = get_strategy_params(strategy_name)
        
        # DeepSeek配置
        self.deepseek = DeepSeekConfig(
            api_key=os.getenv("DEEPSEEK_API_KEY", "your_deepseek_api_key_here"),
            base_url=os.getenv("BASE_URL", "https://api.siliconflow.cn/v1"),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-ai/DeepSeek-V3.1-Terminus")
        )
        
        # 邮件配置
        self.email = EmailConfig(
            smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            sender_email=os.getenv("SENDER_EMAIL", "your_email@gmail.com"),
            sender_password=os.getenv("SENDER_PASSWORD", "your_app_password"),
            receiver_email=os.getenv("RECEIVER_EMAIL", "receiver@gmail.com"),
        )
        
        # 交易配置 - 优先使用策略参数，允许手动覆盖
        self.trading = TradingConfig(
            inst_id=os.getenv("INST_ID", "ETH-USDT-SWAP"),
            analysis_interval=int(os.getenv("ANALYSIS_INTERVAL", str(strategy_params['analysis_interval']))),
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", str(strategy_params['confidence_threshold']))),
            kline_bar=os.getenv("K_LINE_PERIOD", strategy_params['timeframe']),
            strategy_name=strategy_name,
            adjustment_threshold=strategy_params['adjustment_threshold']
        )
        
        # 数据库配置
        self.database = DatabaseConfig()
        
        # 保存策略参数供其他模块使用
        self.strategy = strategy_params

# 全局配置实例
config = Config()
