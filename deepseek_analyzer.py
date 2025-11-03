import logging
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import json
import os

logger = logging.getLogger(__name__)

class DeepSeekAnalyzer:
    """DeepSeek API分析器"""
    
    def __init__(self, config):
        self.config = config  # 保存配置对象
        self.api_key = config.deepseek.api_key
        self.base_url = config.deepseek.base_url
        self.model = config.deepseek.model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.positions_file = "positions.json"
        logger.info("DeepSeek分析器初始化完成")
    
    def _load_positions(self, inst_id: str) -> List[Dict]:
        """加载持仓信息"""
        try:
            if os.path.exists(self.positions_file):
                with open(self.positions_file, 'r', encoding='utf-8') as f:
                    all_positions = json.load(f)
                    # 筛选指定产品的持仓
                    return [p for p in all_positions if p.get('inst_id') == inst_id]
            return []
        except Exception as e:
            logger.error(f"加载持仓信息失败: {e}")
            return []
    
    def _calculate_position_pnl(self, position: Dict, current_price: float) -> Dict:
        """计算持仓盈亏"""
        entry_price = position['entry_price']
        size = position['size']
        leverage = position['leverage']
        direction = position['direction']
        
        if direction == 'long':
            pnl_percent = ((current_price - entry_price) / entry_price) * 100 * leverage
            pnl_amount = (current_price - entry_price) * size
        else:  # short
            pnl_percent = ((entry_price - current_price) / entry_price) * 100 * leverage
            pnl_amount = (entry_price - current_price) * size
        
        return {
            'pnl_percent': round(pnl_percent, 2),
            'pnl_amount': round(pnl_amount, 4)
        }
    
    def analyze_market_data(self, market_data: Dict, inst_id: str) -> Dict:
        """
        分析市场数据并返回交易建议
        """
        prompt = self._build_analysis_prompt(market_data, inst_id)
        
        try:
            logger.info("调用DeepSeek API进行分析...")
            response = self._call_deepseek_api(prompt)
            analysis_result = self._parse_analysis_response(response)
            logger.info(f"DeepSeek分析完成，建议: {analysis_result.get('recommendation', 'UNKNOWN')}")
            return analysis_result
        except Exception as e:
            logger.error(f"DeepSeek分析失败: {e}")
            return {
                "analysis": "分析失败",
                "recommendation": "HOLD",
                "confidence": 0.0,
                "reasoning": f"分析过程中出现错误: {e}",
                "support_levels": [],
                "resistance_levels": [],
                "position_action": "HOLD",
                "stop_adjustment": None,
                "urgent_action": False
            }
    
    def _build_analysis_prompt(self, market_data: Dict, inst_id: str) -> str:
        """构建分析提示词"""
        ticker = market_data['ticker']['data'][0]
        orderbook = market_data['orderbook']['data'][0]
        klines = market_data['candlesticks']['data']
        trades = market_data['trades']['data']
        
        current_price = float(ticker['last'])
        tech_indicators = self._calculate_technical_indicators(klines)
        
        # 加载持仓信息
        positions = self._load_positions(inst_id)
        position_info = self._format_position_info(positions, current_price)
        has_position = len(positions) > 0
        
        # 获取策略参数
        strategy = self.config.strategy
        timeframe_desc = {
            "5m": "5分钟级别的快速交易",
            "15m": "15分钟级别的平衡交易",
            "1H": "1小时级别的趋势交易"
        }.get(strategy['timeframe'], "中期交易")
        
        # 根据持仓状态定义可选操作
        if has_position:
            available_actions = f"""
**可选操作**（持仓状态）：
1. 【卖出 SELL】：平仓离场
2. 【调整止盈止损 ADJUST_STOPS】：优化止盈止损点位（建议止盈{strategy['profit_target']}%，止损{strategy['stop_loss']}%）
3. 【继续持仓 HOLD】：保持当前仓位不变
"""
        else:
            available_actions = f"""
**可选操作**（空仓状态）：
1. 【买多 BUY_LONG】：开多仓，预期价格上涨（RSI < {strategy['rsi_oversold']}时考虑）
2. 【买空 BUY_SHORT】：开空仓，预期价格下跌（RSI > {strategy['rsi_overbought']}时考虑）
3. 【观望 WATCH】：暂不操作，仅在市场极度不明朗时使用
"""
        
        prompt = f"""
你是一个专业的加密货币{timeframe_desc}分析师。

策略类型: {strategy['name']}
K线周期: {strategy['timeframe']}
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 当前市场价格: {current_price} USDT
**重要**: 这是实时最新价格，请基于 {current_price} USDT 进行所有分析和计算。

## 我的持仓状态:
{position_info}

{available_actions}

## 实时行情:
- 当前价格: {current_price} USDT
- 24h 最高: {ticker['high24h']} | 最低: {ticker['low24h']}
- 买一: {ticker['bidPx']} ({ticker['bidSz']}) | 卖一: {ticker['askPx']} ({ticker['askSz']})
- 24h成交量: {ticker['volCcy24h']} USDT

## 市场深度(前5档):
买盘: {self._format_orderbook_levels(orderbook['bids'][:5])}
卖盘: {self._format_orderbook_levels(orderbook['asks'][:5])}

## 技术指标({strategy['timeframe']}):
{tech_indicators}

## 成交分析:
{self._analyze_trades(trades)}

请基于{strategy['name']}策略给出交易建议，JSON格式返回:
{{
  "recommendation": "BUY_LONG/BUY_SHORT/WATCH (空仓时) 或 SELL/ADJUST_STOPS/HOLD (持仓时)",
  "confidence": 0-100,
  "analysis": "市场分析(50字内)",
  "reasoning": "详细理由(100字内)",
  "support_levels": [支撑位1, 支撑位2],
  "resistance_levels": [阻力位1, 阻力位2],
  "stop_adjustment": {{
    "should_adjust": true/false,
    "new_take_profit": 价格或null,
    "new_stop_loss": 价格或null,
    "adjustment_percent": 调整幅度百分比,
    "reason": "调整理由"
  }},
  "urgent_action": true/false,
  "urgent_reason": "紧急原因"
}}

**重要规则**:
1. 所有价格计算必须基于当前价格 {current_price} USDT
2. 空仓时: BUY_LONG(做多)/BUY_SHORT(做空)/WATCH(观望)
3. 持仓时: SELL(平仓)/ADJUST_STOPS(调整止盈止损)/HOLD(继续持仓)
4. 调整止盈止损时，必须计算 adjustment_percent（相对当前价格的调整幅度%）
5. 短线交易要果断，不要总是观望

请用JSON格式返回，包含以下字段:
{{
  "recommendation": "BUY_LONG/BUY_SHORT/WATCH/SELL/ADJUST_STOPS/HOLD",
  "confidence": 0-100,
  "analysis": "短期市场分析",
  "reasoning": "详细理由",
  "support_levels": [支撑位],
  "resistance_levels": [阻力位],
  "take_profit": 止盈价或null,
  "stop_loss": 止损价或null,
  "adjustment_percent": 调整幅度%或null,
  "urgent_action": true/false,
  "urgent_reason": "如需紧急操作的原因"
}}
"""
        
        return prompt
    
    def _format_position_info(self, positions: List[Dict], current_price: float) -> str:
        """格式化持仓信息"""
        if not positions:
            return "无持仓"
        
        info_lines = []
        for i, pos in enumerate(positions):
            pnl = self._calculate_position_pnl(pos, current_price)
            direction_text = "做多(LONG)" if pos['direction'] == 'long' else "做空(SHORT)"
            
            # 检查是否触发止盈止损
            triggered = ""
            if pos['direction'] == 'long':
                if current_price >= pos['take_profit']:
                    triggered = "⚠️ 已触发止盈"
                elif current_price <= pos['stop_loss']:
                    triggered = "⚠️ 已触发止损"
            else:  # short
                if current_price <= pos['take_profit']:
                    triggered = "⚠️ 已触发止盈"
                elif current_price >= pos['stop_loss']:
                    triggered = "⚠️ 已触发止损"
            
            info_lines.append(f"""
持仓 #{i+1}:
- 方向: {direction_text}
- 数量: {pos['size']} | 杠杆: {pos['leverage']}x
- 开仓价: {pos['entry_price']} | 开仓时间: {pos['open_time']}
- 当前止盈: {pos['take_profit']} | 当前止损: {pos['stop_loss']}
- 当前盈亏: {pnl['pnl_amount']:.4f} USDT ({pnl['pnl_percent']:.2f}%)
{f'- 状态: {triggered}' if triggered else '- 状态: ✅ 正常'}
            """.strip())
        
        return "\n\n".join(info_lines)
    
    def _format_orderbook_levels(self, levels: List) -> str:
        """格式化订单簿层级"""
        formatted = []
        for i, level in enumerate(levels):
            formatted.append(f"  档位{i+1}: 价格 {level[0]} | 数量 {level[1]}")
        return "\n".join(formatted)
    
    def _calculate_technical_indicators(self, klines: List) -> str:
        """计算技术指标"""
        if not klines:
            return "无K线数据"
        
        try:
            df = pd.DataFrame(klines, columns=['ts', 'o', 'h', 'l', 'c', 'vol', 'volCcy', 'volCcyQuote', 'confirm'])
            
            for col in ['o', 'h', 'l', 'c', 'vol', 'volCcy']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df = df.dropna()
            
            if len(df) < 20:
                return "数据不足计算技术指标"
            
            df['sma_10'] = df['c'].rolling(window=10).mean()
            df['sma_20'] = df['c'].rolling(window=20).mean()
            df = self._calculate_rsi(df, window=14)
            
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            indicators = f"""
            - 当前价格: {latest['c']:.2f}
            - 10周期SMA: {latest['sma_10']:.2f} {'↑' if latest['sma_10'] > prev['sma_10'] else '↓'}
            - 20周期SMA: {latest['sma_20']:.2f} {'↑' if latest['sma_20'] > prev['sma_20'] else '↓'}
            - RSI(14): {latest.get('rsi', 'N/A'):.2f}
            - 价格趋势: {'上涨' if latest['c'] > prev['c'] else '下跌'}
            """
            
            return indicators
        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return f"技术指标计算错误: {e}"
    
    def _calculate_rsi(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """计算RSI指标"""
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        return df
    
    def _analyze_trades(self, trades: List) -> str:
        """分析成交数据"""
        if not trades:
            return "无成交数据"
        
        try:
            buy_volume = sum(float(trade.get('sz', 0)) for trade in trades[:50] if trade.get('side') == 'buy')
            sell_volume = sum(float(trade.get('sz', 0)) for trade in trades[:50] if trade.get('side') == 'sell')
            
            return f"买入量: {buy_volume:.2f} | 卖出量: {sell_volume:.2f}"
        except Exception as e:
            return f"成交分析错误: {e}"
    
    def _call_deepseek_api(self, prompt: str) -> Dict:
        """调用DeepSeek API"""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的加密货币交易分析师，专注于技术分析和市场趋势判断。请用JSON格式返回分析结果。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 2048
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            # 记录详细的错误信息
            if response.status_code != 200:
                logger.error(f"API请求失败 - 状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error("API请求超时")
            raise Exception("API请求超时，请检查网络连接")
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求异常: {e}")
            raise
    
    def _parse_analysis_response(self, response: Dict) -> Dict:
        """解析DeepSeek API响应"""
        try:
            content = response['choices'][0]['message']['content']
            
            # 尝试从响应中提取JSON
            if '{' in content and '}' in content:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                json_str = content[json_start:json_end]
                result = json.loads(json_str)
                
                # 验证必要字段
                required_fields = ['recommendation', 'confidence', 'analysis', 'reasoning']
                for field in required_fields:
                    if field not in result:
                        result[field] = "未知"
                
                # 确保新字段存在
                if 'position_action' not in result:
                    result['position_action'] = 'HOLD'
                if 'stop_adjustment' not in result:
                    result['stop_adjustment'] = {
                        'should_adjust': False,
                        'new_take_profit': None,
                        'new_stop_loss': None,
                        'reason': ''
                    }
                if 'urgent_action' not in result:
                    result['urgent_action'] = False
                if 'urgent_reason' not in result:
                    result['urgent_reason'] = ''
                
                return result
            else:
                return {
                    "analysis": content,
                    "recommendation": "HOLD",
                    "confidence": 50.0,
                    "reasoning": content,
                    "support_levels": [],
                    "resistance_levels": [],
                    "position_action": "HOLD",
                    "stop_adjustment": {
                        'should_adjust': False,
                        'new_take_profit': None,
                        'new_stop_loss': None,
                        'reason': ''
                    },
                    "urgent_action": False,
                    "urgent_reason": ""
                }
        except Exception as e:
            logger.error(f"解析DeepSeek响应失败: {e}")
            return {
                "analysis": "解析失败",
                "recommendation": "HOLD",
                "confidence": 0.0,
                "reasoning": f"解析失败: {e}",
                "support_levels": [],
                "resistance_levels": [],
                "position_action": "HOLD",
                "stop_adjustment": {
                    'should_adjust': False,
                    'new_take_profit': None,
                    'new_stop_loss': None,
                    'reason': ''
                },
                "urgent_action": False,
                "urgent_reason": ""
            }
