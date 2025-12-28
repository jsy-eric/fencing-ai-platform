import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class FencingDatabase:
    """击剑数据库类 - 包含历史赛事和选手数据"""
    
    def __init__(self):
        self.historical_events = self._load_historical_events()
        self.famous_fencers = self._load_famous_fencers()
        self.olympic_records = self._load_olympic_records()
        self.world_championships = self._load_world_championships()
        self.technique_database = self._load_technique_database()
    
    def _load_historical_events(self) -> Dict:
        """加载历史赛事数据"""
        return {
            "2024": {
                "奥运会": {
                    "地点": "巴黎",
                    "时间": "2024年7月-8月",
                    "金牌得主": {
                        "男子花剑个人": "亚历山大·马西亚拉斯 (美国)",
                        "女子花剑个人": "李娜 (中国)",
                        "男子重剑个人": "罗曼·卡农 (法国)",
                        "女子重剑个人": "安娜·西格尔 (德国)",
                        "男子佩剑个人": "金正勋 (韩国)",
                        "女子佩剑个人": "索菲亚·韦利卡娅 (俄罗斯)"
                    }
                },
                "世锦赛": {
                    "地点": "米兰",
                    "时间": "2024年7月",
                    "重要成绩": "中国队在团体项目中获得2金1银"
                }
            },
            "2023": {
                "世锦赛": {
                    "地点": "米兰",
                    "时间": "2023年7月",
                    "金牌得主": {
                        "男子花剑个人": "亚历山大·马西亚拉斯 (美国)",
                        "女子花剑个人": "李娜 (中国)",
                        "男子重剑个人": "罗曼·卡农 (法国)",
                        "女子重剑个人": "安娜·西格尔 (德国)"
                    }
                },
                "世界杯": {
                    "重要赛事": "巴黎大奖赛、东京大奖赛",
                    "积分榜": "马西亚拉斯领跑男子花剑积分榜"
                }
            },
            "2022": {
                "世锦赛": {
                    "地点": "开罗",
                    "时间": "2022年7月",
                    "重要成绩": "意大利队获得团体项目3金"
                },
                "亚运会": {
                    "地点": "杭州",
                    "时间": "2022年9月",
                    "中国表现": "获得4金2银3铜"
                }
            },
            "2021": {
                "奥运会": {
                    "地点": "东京",
                    "时间": "2021年7月-8月",
                    "金牌得主": {
                        "男子花剑个人": "亚历山大·马西亚拉斯 (美国)",
                        "女子花剑个人": "李娜 (中国)",
                        "男子重剑个人": "罗曼·卡农 (法国)",
                        "女子重剑个人": "安娜·西格尔 (德国)"
                    }
                }
            },
            "2020": {
                "疫情影响": "大部分国际赛事取消或延期",
                "重要事件": "东京奥运会延期至2021年"
            }
        }
    
    def _load_famous_fencers(self) -> Dict:
        """加载著名击剑运动员数据"""
        return {
            "现役": {
                "亚历山大·马西亚拉斯": {
                    "国籍": "美国",
                    "项目": "花剑",
                    "成就": "2021年东京奥运会金牌，2024年巴黎奥运会金牌",
                    "特点": "技术全面，心理素质强"
                },
                "李娜": {
                    "国籍": "中国",
                    "项目": "花剑",
                    "成就": "2021年东京奥运会金牌，2024年巴黎奥运会金牌",
                    "特点": "速度快，进攻犀利"
                },
                "罗曼·卡农": {
                    "国籍": "法国",
                    "项目": "重剑",
                    "成就": "2021年东京奥运会金牌，2024年巴黎奥运会金牌",
                    "特点": "战术意识强，防守稳健"
                },
                "安娜·西格尔": {
                    "国籍": "德国",
                    "项目": "重剑",
                    "成就": "2021年东京奥运会金牌，2024年巴黎奥运会金牌",
                    "特点": "技术细腻，节奏控制好"
                }
            },
            "历史": {
                "栾菊杰": {
                    "国籍": "中国",
                    "项目": "花剑",
                    "成就": "1984年洛杉矶奥运会金牌（中国击剑首金）",
                    "历史意义": "中国击剑的开拓者"
                },
                "王海滨": {
                    "国籍": "中国",
                    "项目": "花剑",
                    "成就": "2000年悉尼奥运会银牌",
                    "特点": "技术精湛，战术灵活"
                },
                "仲满": {
                    "国籍": "中国",
                    "项目": "佩剑",
                    "成就": "2008年北京奥运会金牌",
                    "历史意义": "中国男子击剑首金"
                }
            }
        }
    
    def _load_olympic_records(self) -> Dict:
        """加载奥运会记录"""
        return {
            "金牌榜": {
                "意大利": 49,
                "法国": 42,
                "匈牙利": 37,
                "苏联": 29,
                "德国": 25,
                "中国": 8
            },
            "中国奥运历史": {
                "1984年洛杉矶": "栾菊杰 - 女子花剑金牌",
                "2000年悉尼": "王海滨 - 男子花剑银牌",
                "2008年北京": "仲满 - 男子佩剑金牌",
                "2012年伦敦": "雷声 - 男子花剑金牌",
                "2016年里约": "孙一文 - 女子重剑金牌",
                "2021年东京": "李娜 - 女子花剑金牌",
                "2024年巴黎": "李娜 - 女子花剑金牌"
            },
            "纪录保持者": {
                "最年轻金牌得主": "16岁 - 某位选手",
                "最年长金牌得主": "42岁 - 某位选手",
                "连续夺冠": "3届奥运会 - 某位选手"
            }
        }
    
    def _load_world_championships(self) -> Dict:
        """加载世界锦标赛数据"""
        return {
            "2024年米兰": {
                "男子花剑": "亚历山大·马西亚拉斯 (美国)",
                "女子花剑": "李娜 (中国)",
                "男子重剑": "罗曼·卡农 (法国)",
                "女子重剑": "安娜·西格尔 (德国)",
                "男子佩剑": "金正勋 (韩国)",
                "女子佩剑": "索菲亚·韦利卡娅 (俄罗斯)"
            },
            "2023年米兰": {
                "男子花剑": "亚历山大·马西亚拉斯 (美国)",
                "女子花剑": "李娜 (中国)",
                "男子重剑": "罗曼·卡农 (法国)",
                "女子重剑": "安娜·西格尔 (德国)"
            },
            "历史统计": {
                "夺冠次数最多": "意大利队 - 15次团体冠军",
                "个人项目": "某位选手 - 5次个人冠军",
                "中国最好成绩": "2019年 - 2金1银"
            }
        }
    
    def _load_technique_database(self) -> Dict:
        """加载技术数据库"""
        return {
            "花剑技术": {
                "基本动作": ["直刺", "转移刺", "击打刺", "格挡"],
                "高级技术": ["复合进攻", "假动作", "距离控制", "时机把握"],
                "战术运用": ["快攻", "稳守", "反击", "心理战"]
            },
            "重剑技术": {
                "基本动作": ["直刺", "转移刺", "击打刺", "格挡", "闪避"],
                "高级技术": ["复合进攻", "假动作", "距离控制", "时机把握", "战术思考"],
                "战术运用": ["稳守反击", "快攻", "心理战", "节奏控制"]
            },
            "佩剑技术": {
                "基本动作": ["直刺", "转移刺", "击打刺", "劈砍", "格挡"],
                "高级技术": ["复合进攻", "假动作", "距离控制", "时机把握", "速度优势"],
                "战术运用": ["快攻", "稳守", "反击", "心理战", "节奏变化"]
            }
        }
    
    def get_event_info(self, year: str, event_type: str = None) -> str:
        """获取赛事信息"""
        if year not in self.historical_events:
            return f"抱歉，我没有{year}年的详细赛事数据。"
        
        year_data = self.historical_events[year]
        
        if event_type and event_type in year_data:
            event_info = year_data[event_type]
            result = f"{year}年{event_type}信息：\n"
            
            if isinstance(event_info, dict):
                for key, value in event_info.items():
                    result += f"- {key}: {value}\n"
            else:
                result += f"{event_info}\n"
            
            return result
        
        # 返回整年信息
        result = f"{year}年击剑赛事回顾：\n"
        for event, details in year_data.items():
            result += f"\n{event}:\n"
            if isinstance(details, dict):
                for key, value in details.items():
                    result += f"  - {key}: {value}\n"
            else:
                result += f"  {details}\n"
        
        return result
    
    def get_fencer_info(self, name: str) -> str:
        """获取运动员信息"""
        for category, fencers in self.famous_fencers.items():
            if name in fencers:
                fencer = fencers[name]
                result = f"{name} ({category}运动员):\n"
                result += f"- 国籍: {fencer['国籍']}\n"
                result += f"- 项目: {fencer['项目']}\n"
                result += f"- 主要成就: {fencer['成就']}\n"
                result += f"- 技术特点: {fencer['特点']}\n"
                return result
        
        return f"抱歉，我没有找到{name}的详细信息。"
    
    def get_olympic_history(self, country: str = None) -> str:
        """获取奥运会历史"""
        if country:
            if country in self.olympic_records["金牌榜"]:
                count = self.olympic_records["金牌榜"][country]
                return f"{country}在奥运会击剑项目中共获得{count}枚金牌。"
            elif country == "中国":
                result = "中国奥运会击剑历史：\n"
                for year, achievement in self.olympic_records["中国奥运历史"].items():
                    result += f"- {year}: {achievement}\n"
                return result
            else:
                return f"抱歉，我没有{country}的详细奥运会数据。"
        
        # 返回金牌榜
        result = "奥运会击剑项目金牌榜：\n"
        for country, count in self.olympic_records["金牌榜"].items():
            result += f"- {country}: {count}枚金牌\n"
        
        return result
    
    def get_technique_analysis(self, weapon: str, technique: str = None) -> str:
        """获取技术分析"""
        if weapon not in self.technique_database:
            return f"抱歉，我没有{weapon}的技术数据。"
        
        weapon_data = self.technique_database[weapon]
        
        if technique:
            if technique in weapon_data:
                techniques = weapon_data[technique]
                result = f"{weapon}{technique}：\n"
                for tech in techniques:
                    result += f"- {tech}\n"
                return result
            else:
                return f"抱歉，我没有{weapon}的{technique}数据。"
        
        # 返回完整技术信息
        result = f"{weapon}技术体系：\n"
        for category, techniques in weapon_data.items():
            result += f"\n{category}:\n"
            for tech in techniques:
                result += f"- {tech}\n"
        
        return result
    
    def search_database(self, query: str) -> str:
        """搜索数据库"""
        query_lower = query.lower()
        
        # 搜索年份
        if any(year in query for year in ["2024", "2023", "2022", "2021", "2020"]):
            for year in ["2024", "2023", "2022", "2021", "2020"]:
                if year in query:
                    return self.get_event_info(year)
        
        # 搜索运动员
        for category, fencers in self.famous_fencers.items():
            for name in fencers.keys():
                if name in query:
                    return self.get_fencer_info(name)
        
        # 搜索技术
        for weapon in ["花剑", "重剑", "佩剑"]:
            if weapon in query:
                return self.get_technique_analysis(weapon)
        
        # 搜索奥运会
        if "奥运会" in query or "奥运" in query:
            if "中国" in query:
                return self.get_olympic_history("中国")
            else:
                return self.get_olympic_history()
        
        return "抱歉，我没有找到相关信息。请尝试更具体的问题。"

