import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)

class EmailNotifier:
    """邮件通知器"""
    
    def __init__(self, config):
        self.config = config.email
        logger.info("邮件通知器初始化完成")
    
    def send_trading_alert(self, analysis_data: Dict) -> bool:
        """
        发送交易提醒邮件
        
        Args:
            analysis_data: 分析数据字典
            
        Returns:
            bool: 发送是否成功
        """
        try:
            subject = self._build_subject(analysis_data)
            body = self._build_email_body(analysis_data)
            
            success = self._send_email(subject, body)
            
            if success:
                logger.info(f"交易提醒邮件发送成功: {analysis_data.get('recommendation')}")
            else:
                logger.error("交易提醒邮件发送失败")
            
            return success
            
        except Exception as e:
            logger.error(f"发送交易提醒邮件时出错: {e}")
            return False
    
    def _build_subject(self, analysis_data: Dict) -> str:
        """构建邮件主题"""
        recommendation = analysis_data.get('recommendation', 'UNKNOWN')
        confidence = analysis_data.get('confidence', 0)
        price = analysis_data.get('current_price', 0)
        inst_id = analysis_data.get('inst_id', 'UNKNOWN')
        
        if recommendation == "BUY":
            emoji = "🟢"
            action = "买入"
        elif recommendation == "SELL":
            emoji = "🔴" 
            action = "卖出"
        else:
            emoji = "🟡"
            action = "持有"
        
        return f"{emoji} {inst_id} 交易提醒: {action} | 信心度: {confidence}% | 价格: {price}"
    
    def _build_email_body(self, analysis_data: Dict) -> str:
        """构建邮件正文"""
        recommendation = analysis_data.get('recommendation', 'UNKNOWN')
        confidence = analysis_data.get('confidence', 0)
        price = analysis_data.get('current_price', 0)
        analysis_summary = analysis_data.get('analysis_summary', '')
        reasoning = analysis_data.get('reasoning', '')
        support_levels = analysis_data.get('support_levels', [])
        resistance_levels = analysis_data.get('resistance_levels', [])
        inst_id = analysis_data.get('inst_id', 'UNKNOWN')
        position_action = analysis_data.get('position_action', 'HOLD')
        stop_adjustment = analysis_data.get('stop_adjustment', {})
        urgent_action = analysis_data.get('urgent_action', False)
        urgent_reason = analysis_data.get('urgent_reason', '')
        
        # 构建紧急提醒部分
        urgent_html = ""
        if urgent_action:
            urgent_html = f"""
            <div style="background-color: #ff6b6b; color: white; padding: 20px; border-radius: 5px; margin: 15px 0; text-align: center;">
                <h2>🚨 紧急操作提醒 🚨</h2>
                <p style="font-size: 18px; font-weight: bold;">{urgent_reason}</p>
            </div>
            """
        
        # 构建持仓操作建议部分
        position_html = ""
        if position_action != 'HOLD':
            action_text = {
                'CLOSE_ALL': '🔴 建议全部平仓',
                'CLOSE_PARTIAL': '🟠 建议部分平仓',
                'ADD': '🟢 建议加仓'
            }.get(position_action, position_action)
            
            position_html = f"""
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #ffc107;">
                <h3>📈 持仓操作建议</h3>
                <p style="font-size: 16px; font-weight: bold;">{action_text}</p>
            </div>
            """
        
        # 构建止盈止损调整部分
        stop_html = ""
        if stop_adjustment.get('should_adjust', False):
            tp = stop_adjustment.get('new_take_profit')
            sl = stop_adjustment.get('new_stop_loss')
            reason = stop_adjustment.get('reason', '')
            
            stop_html = f"""
            <div style="background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #007bff;">
                <h3>⚙️ 止盈止损调整建议</h3>
                {f'<p><strong>新止盈价:</strong> {tp} USDT</p>' if tp else ''}
                {f'<p><strong>新止损价:</strong> {sl} USDT</p>' if sl else ''}
                <p><strong>调整理由:</strong> {reason}</p>
            </div>
            """
        
        # 构建HTML邮件内容
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
                .recommendation {{ font-size: 24px; font-weight: bold; margin: 10px 0; }}
                .buy {{ color: #28a745; }}
                .sell {{ color: #dc3545; }}
                .hold {{ color: #ffc107; }}
                .info-box {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .levels {{ display: flex; justify-content: space-between; }}
                .support, .resistance {{ width: 48%; padding: 10px; }}
                .support {{ background-color: #d4edda; }}
                .resistance {{ background-color: #f8d7da; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚀 加密货币交易提醒</h2>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            {urgent_html}
            
            <div class="recommendation {recommendation.lower()}">
                {'🟢 建议买入' if recommendation == 'BUY' else '🔴 建议卖出' if recommendation == 'SELL' else '🟡 建议持有'}
            </div>
            
            {position_html}
            
            {stop_html}
            
            <div class="info-box">
                <h3>📊 交易概览</h3>
                <p><strong>交易对:</strong> {inst_id}</p>
                <p><strong>当前价格:</strong> {price} USDT</p>
                <p><strong>信心水平:</strong> {confidence}%</p>
            </div>
            
            <div class="info-box">
                <h3>📈 市场分析</h3>
                <p><strong>分析总结:</strong> {analysis_summary}</p>
                <p><strong>详细理由:</strong> {reasoning}</p>
            </div>
            
            <div class="levels">
                <div class="support">
                    <h4>💪 支撑位</h4>
                    <ul>
                        {"".join(f"<li>{level}</li>" for level in support_levels[:5]) if support_levels else "<li>无数据</li>"}
                    </ul>
                </div>
                <div class="resistance">
                    <h4>🚧 阻力位</h4>
                    <ul>
                        {"".join(f"<li>{level}</li>" for level in resistance_levels[:5]) if resistance_levels else "<li>无数据</li>"}
                    </ul>
                </div>
            </div>
            
            <div style="margin-top: 20px; padding: 10px; background-color: #fff3cd; border-radius: 5px;">
                <p><strong>⚠️ 风险提示:</strong> 此分析仅为AI生成建议，不构成投资意见。加密货币交易风险极高，请谨慎决策。</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _send_email(self, subject: str, body: str) -> bool:
        """发送邮件"""
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.sender_email
            msg['To'] = self.config.receiver_email
            
            # 添加HTML内容
            html_part = MIMEText(body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 发送邮件
            logger.info(f"正在连接到 {self.config.smtp_server}:{self.config.smtp_port}")
            
            if self.config.smtp_port == 465:
                # 465端口使用SSL
                server = smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port, timeout=30)
                logger.info("使用SSL连接")
            else:
                # 587端口使用STARTTLS
                server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port, timeout=30)
                logger.info("使用STARTTLS连接")
                server.starttls()  # 启用TLS加密
            
            logger.info("正在登录...")
            server.login(self.config.sender_email, self.config.sender_password)
            
            logger.info("正在发送邮件...")
            server.send_message(msg)
            server.quit()
            
            logger.info("✅ 邮件发送成功")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"邮件认证失败: {e}")
            logger.error("请检查邮箱地址和应用专用密码是否正确")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP错误: {e}")
            return False
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False