import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_bot import TradingAnalysisBot
from strategy_config import print_strategy_info

def setup_logging():
    """配置日志"""
    # 创建logs目录（如果不存在）
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # 生成带日期的日志文件名
    log_date = datetime.now().strftime('%Y%m%d')
    dated_log_file = os.path.join(logs_dir, f'trading_bot_{log_date}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('trading_bot.log', encoding='utf-8'),  # 通用日志文件
            logging.FileHandler(dated_log_file, encoding='utf-8'),     # 按日期的日志文件
            logging.StreamHandler()
        ]
    )

def main():
    """主函数"""
    print("🚀 智能交易分析系统启动中...")
    
    # 设置日志
    setup_logging()
    
    # 打印策略信息
    strategy = os.getenv('TRADING_STRATEGY', 'balanced')
    print_strategy_info(strategy)
    
    # 检查必要的环境变量
    required_env_vars = ['DEEPSEEK_API_KEY', 'SENDER_EMAIL', 'SENDER_PASSWORD', 'RECEIVER_EMAIL']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 缺少必要的环境变量: {', '.join(missing_vars)}")
        print("请创建 .env 文件并设置以下变量:")
        for var in missing_vars:
            print(f"  {var}=your_value_here")
        return
    
    try:
        # 创建交易机器人实例
        bot = TradingAnalysisBot()
        
        # 运行单次测试
        print("运行单次分析测试...")
        test_result = bot.run_analysis_cycle()
        
        if test_result:
            print("✅ 测试成功! 开始连续监控...")
            # 开始连续分析
            bot.start_continuous_analysis()
        else:
            print("❌ 测试失败，请检查配置和网络连接。")
            
    except KeyboardInterrupt:
        print("\n👋 用户终止程序")
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        logging.exception("程序运行异常")

if __name__ == "__main__":
    main()
