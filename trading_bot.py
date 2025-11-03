import logging
import time
import json
from datetime import datetime
from typing import Dict, Optional, List, Any

from config import config
from market_data import OKXMarketData
from deepseek_analyzer import DeepSeekAnalyzer
from db import TradingAnalysisDB
from email_notifier import EmailNotifier

logger = logging.getLogger(__name__)

class TradingAnalysisBot:
    """交易分析机器人"""
    
    def __init__(self):
        self.config = config  # 保存配置对象
        self.inst_id = config.trading.inst_id
        self.confidence_threshold = config.trading.confidence_threshold
        
        # 初始化各个模块
        self.market_data = OKXMarketData(flag="0")
        self.analyzer = DeepSeekAnalyzer(config)
        self.database = TradingAnalysisDB(config.database.db_path)
        self.email_notifier = EmailNotifier(config)
        
        # 统计信息
        self.analysis_count = 0
        self.email_alerts_sent = 0
        self.last_analysis_time = None
        
        logger.info(f"交易分析机器人初始化完成，监控交易对: {self.inst_id}")
    
    def run_analysis_cycle(self) -> Optional[Dict]:
        """运行一次完整的分析周期"""
        logger.info(f"开始分析周期 #{self.analysis_count + 1} - {self.inst_id}")
        
        try:
            # 1. 获取市场数据
            market_data = self.market_data.get_all_market_data(self.inst_id, config)
            
            # 2. 调用DeepSeek进行分析
            analysis_result = self.analyzer.analyze_market_data(market_data, self.inst_id)
            
            # 3. 准备存储数据
            current_price = float(market_data['ticker']['data'][0]['last'])
            analysis_data = {
                'inst_id': self.inst_id,
                'current_price': current_price,
                'recommendation': analysis_result.get('recommendation', 'HOLD'),
                'confidence': float(analysis_result.get('confidence', 0)),
                'analysis_summary': analysis_result.get('analysis', ''),
                'reasoning': analysis_result.get('reasoning', ''),
                'support_levels': analysis_result.get('support_levels', []),
                'resistance_levels': analysis_result.get('resistance_levels', []),
                'position_action': analysis_result.get('position_action', 'HOLD'),
                'stop_adjustment': analysis_result.get('stop_adjustment', {}),
                'urgent_action': analysis_result.get('urgent_action', False),
                'urgent_reason': analysis_result.get('urgent_reason', ''),
                'market_data_json': json.dumps(market_data),
                'raw_response': json.dumps(analysis_result)
            }
            
            # 4. 保存到数据库
            record_id = self.database.save_analysis(analysis_data)
            analysis_data['record_id'] = record_id
            
            # 5. 检查是否需要发送邮件提醒
            should_send_email = self._should_send_email_alert(analysis_result)
            if should_send_email:
                self._send_email_alert(analysis_data)
                analysis_data['email_sent'] = True
            else:
                analysis_data['email_sent'] = False
            
            # 6. 输出结果
            self._print_analysis_result(analysis_data)
            
            # 更新统计
            self.analysis_count += 1
            self.last_analysis_time = datetime.now()
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"分析周期执行失败: {e}")
            return None
    
    def _should_send_email_alert(self, result: Dict[str, Any]) -> bool:
        """判断是否应该发送邮件提醒
        
        只在以下情况发送邮件:
        1. 买多 (BUY_LONG)
        2. 买空 (BUY_SHORT)
        3. 卖出 (SELL)
        4. 需要大幅调整止盈止损 (adjustment_percent > 策略阈值)
        5. 紧急操作 (urgent_action)
        
        同时需要 confidence 超过阈值
        """
        recommendation = result.get('recommendation', '').upper()
        confidence = result.get('confidence', 0)
        
        # 紧急操作，无论信心度如何都发送
        if result.get('urgent_action', False):
            logger.info("检测到紧急操作，发送邮件提醒")
            return True
        
        # 检查信心度是否超过阈值
        if confidence < self.confidence_threshold:
            logger.info(f"信心度 {confidence}% 低于阈值 {self.confidence_threshold}%，不发送邮件")
            return False
        
        # 买多、买空、卖出操作
        if recommendation in ['BUY_LONG', 'BUY_SHORT', 'SELL']:
            logger.info(f"检测到 {recommendation} 操作，发送邮件提醒")
            return True
        
        # 检查是否需要大幅调整止盈止损（根据策略阈值）
        if recommendation == 'ADJUST_STOPS':
            stop_adjustment = result.get('stop_adjustment', {})
            adjustment_percent = stop_adjustment.get('adjustment_percent')
            threshold = self.config.trading.adjustment_threshold
            
            if adjustment_percent:
                adj_value = abs(float(adjustment_percent))
                if adj_value > threshold:
                    logger.info(f"检测到大幅调整 {adj_value:.2f}% > {threshold}%，发送邮件提醒")
                    return True
                else:
                    logger.info(f"调整幅度 {adj_value:.2f}% 未超过阈值 {threshold}%，不发送邮件")
            else:
                logger.info("ADJUST_STOPS 但未提供 adjustment_percent，不发送邮件")
            
        return False
    
    def _get_positions(self) -> List[Dict]:
        """获取持仓列表"""
        try:
            return self.analyzer._load_positions(self.inst_id)
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return []
    
    def _check_has_position(self, positions: List[Dict], inst_id: str) -> bool:
        """检查是否有指定交易对的持仓"""
        return any(p['inst_id'] == inst_id for p in positions)
    
    def _is_significant_stop_adjustment(self, stop_adjustment: Dict, current_price: float) -> bool:
        """判断是否为大幅止盈止损调整"""
        if not stop_adjustment.get('should_adjust', False) or current_price == 0:
            return False
        
        # 获取当前持仓的止盈止损
        try:
            positions = self.analyzer._load_positions(self.inst_id)
            if not positions:
                return False
            
            # 使用第一个持仓作为参考
            pos = positions[0]
            old_tp = pos.get('take_profit', 0)
            old_sl = pos.get('stop_loss', 0)
            
            new_tp = stop_adjustment.get('new_take_profit')
            new_sl = stop_adjustment.get('new_stop_loss')
            
            # 如果调整幅度超过当前价格的2%，视为大幅调整
            threshold = current_price * 0.02
            
            if new_tp and old_tp:
                if abs(new_tp - old_tp) > threshold:
                    logger.info(f"止盈大幅调整: {old_tp} -> {new_tp} (变化 {abs(new_tp - old_tp):.2f})")
                    return True
            
            if new_sl and old_sl:
                if abs(new_sl - old_sl) > threshold:
                    logger.info(f"止损大幅调整: {old_sl} -> {new_sl} (变化 {abs(new_sl - old_sl):.2f})")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查止盈止损调整幅度失败: {e}")
            return False
    
    def _send_email_alert(self, analysis_data: Dict):
        """发送邮件提醒"""
        try:
            success = self.email_notifier.send_trading_alert(analysis_data)
            
            # 保存邮件提醒记录
            alert_data = {
                'inst_id': analysis_data['inst_id'],
                'recommendation': analysis_data['recommendation'],
                'confidence': analysis_data['confidence'],
                'current_price': analysis_data['current_price'],
                'message': f"{analysis_data['recommendation']} - {analysis_data['analysis_summary']}",
                'sent_successfully': success
            }
            
            self.database.save_email_alert(alert_data)
            
            if success:
                self.database.mark_email_sent(analysis_data['record_id'])
                self.email_alerts_sent += 1
                logger.info(f"高信心度交易提醒邮件已发送! 建议: {analysis_data['recommendation']}, 信心度: {analysis_data['confidence']}%")
            else:
                logger.error("邮件发送失败，但分析记录已保存")
                
        except Exception as e:
            logger.error(f"发送邮件提醒失败: {e}")
    
    def _print_analysis_result(self, analysis_data: Dict):
        """打印分析结果"""
        recommendation = analysis_data['recommendation']
        confidence = analysis_data['confidence']
        price = analysis_data['current_price']
        urgent_action = analysis_data.get('urgent_action', False)
        
        # 获取持仓信息
        positions = self._get_positions()
        has_position = self._check_has_position(positions, self.inst_id)
        
        # 将操作建议翻译成中文
        rec_map = {
            'BUY_LONG': '买多',
            'BUY_SHORT': '买空',
            'SELL': '卖出',
            'ADJUST_STOPS': '调整止盈止损',
            'HOLD': '继续持仓',
            'WATCH': '观望'
        }
        action_text = rec_map.get(recommendation, recommendation)
        
        # 根据建议设置颜色和图标
        if recommendation in ['BUY_LONG', 'BUY_SHORT']:
            color_start = "\033[92m"  # 绿色
            icon = "📈"
        elif recommendation == "SELL":
            color_start = "\033[91m"  # 红色
            icon = "📉"
        elif recommendation == "WATCH":
            color_start = "\033[96m"  # 青色
            icon = "👀"
        else:  # HOLD, ADJUST_STOPS
            color_start = "\033[93m"  # 黄色
            icon = "⏸️"
        
        color_end = "\033[0m"
        
        print("\n" + "="*70)
        print(f"📊 {self.inst_id} 分析结果")
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💰 当前价格: {price:.2f} USDT")
        
        # 显示持仓状态
        if has_position:
            position = next(p for p in positions if p['inst_id'] == self.inst_id)
            direction = "做多 📈" if position['direction'] == 'long' else "做空 📉"
            entry_price = position['entry_price']
            pnl_data = self.analyzer._calculate_position_pnl(position, price)
            print(f"📌 当前持仓: {direction} | 开仓价: {entry_price} | 盈亏: {pnl_data['pnl_percent']:.2f}%")
        else:
            print(f"📌 当前持仓: 空仓")
        
        print(f"{color_start}{icon} 建议: {action_text} ({recommendation}) | 信心度: {confidence:.1f}%{color_end}")
        
        # 如果是调整止盈止损，显示调整幅度
        if recommendation == 'ADJUST_STOPS':
            stop_adj = analysis_data.get('stop_adjustment', {})
            adjustment_percent = stop_adj.get('adjustment_percent')
            if adjustment_percent:
                print(f"⚙️  调整幅度: {adjustment_percent:.2f}%")
            if stop_adj.get('new_take_profit'):
                print(f"   新止盈: {stop_adj['new_take_profit']} USDT")
            if stop_adj.get('new_stop_loss'):
                print(f"   新止损: {stop_adj['new_stop_loss']} USDT")
            if stop_adj.get('reason'):
                print(f"   理由: {stop_adj['reason']}")
        
        # 显示邮件发送状态
        if analysis_data.get('email_sent', False):
            print(f"📧 邮件提醒已发送!")
        
        if urgent_action:
            print(f"🚨🚨 紧急操作提醒: {analysis_data.get('urgent_reason', '')}")
        elif confidence >= self.confidence_threshold and not analysis_data.get('email_sent', False):
            print(f"🚨 高信心度提醒! 建议立即关注")
        
        summary = analysis_data['analysis_summary']
        if len(summary) > 100:
            summary = summary[:100] + "..."
        print(f"📋 分析总结: {summary}")
        print("="*70 + "\n")
    
    def start_continuous_analysis(self):
        """开始连续分析"""
        interval = config.trading.analysis_interval
        
        logger.info(f"开始连续分析，间隔: {interval}秒，信心阈值: {self.confidence_threshold}%")
        print(f"\n🚀 开始监控 {self.inst_id}")
        print(f"📊 分析间隔: {interval}秒")
        print(f"🎯 信心阈值: {self.confidence_threshold}%")
        print(f"📧 邮件提醒: 已启用")
        print("="*50)
        
        try:
            while True:
                start_time = time.time()
                
                # 执行分析周期
                self.run_analysis_cycle()
                
                # 打印统计信息
                if self.analysis_count % 10 == 0:
                    self._print_statistics()
                
                # 计算等待时间
                elapsed = time.time() - start_time
                wait_time = max(1, interval - elapsed)
                
                logger.info(f"等待 {wait_time:.1f} 秒后进行下一次分析...")
                time.sleep(wait_time)
                
        except KeyboardInterrupt:
            logger.info("用户中断分析过程")
            self._print_final_statistics()
        except Exception as e:
            logger.error(f"连续分析过程出错: {e}")
            self._print_final_statistics()
            raise
    
    def _print_statistics(self):
        """打印统计信息"""
        print(f"\n📈 统计信息 (分析次数: {self.analysis_count}, 邮件提醒: {self.email_alerts_sent})")
    
    def _print_final_statistics(self):
        """打印最终统计信息"""
        print("\n" + "="*50)
        print("🏁 分析任务结束")
        print(f"📊 总分析次数: {self.analysis_count}")
        print(f"📧 邮件提醒发送: {self.email_alerts_sent}")
        print("="*50)
