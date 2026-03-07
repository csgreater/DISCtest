import requests
import json

class KimiDISCAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.moonshot.cn/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def analyze_disc(self, disc_scores: dict, context: str = "") -> dict:
        """
        分析DISC测评结果
        
        Args:
            disc_scores: DISC各维度分数，如 {"D": 85, "I": 60, "S": 45, "C": 70}
            context: 补充背景信息（岗位、场景等）
        """
        
        # 构建专业提示词
        system_prompt = """你是一位专业的DISC行为风格分析师和职业顾问。你的任务是：
1. 深度解读DISC测评结果，分析行为风格特征
2. 识别优势领域和潜在发展盲区
3. 提供针对性的职业发展、团队配合、沟通策略建议
4. 保持客观专业，避免刻板印象

输出结构：
- 核心风格画像（2-3句话概括）
- 四维解读（各维度表现及影响）
- 优势 leverage 建议
- 潜在盲点提醒
- 应用场景指导（职场/团队/沟通）"""

        # 构建用户输入
        user_content = self._format_disc_input(disc_scores, context)
        
        payload = {
            "model": "kimi-k2-5",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        return {
            "analysis": response.json()["choices"][0]["message"]["content"],
            "usage": response.json().get("usage", {})
        }
    
    def _format_disc_input(self, scores: dict, context: str) -> str:
        """格式化DISC数据"""
        # 排序找出主导风格
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_scores[0][0]
        secondary = sorted_scores[1][0] if len(sorted_scores) > 1 else None
        
        text = f"""请分析以下DISC测评结果：

**测评分数**:
- D (支配型): {scores.get('D', 0)}%
- I (影响型): {scores.get('I', 0)}%
- S (稳健型): {scores.get('S', 0)}%
- C (谨慎型): {scores.get('C', 0)}%

**主导风格**: {primary}{f'+{secondary}' if secondary else ''}型

"""
        if context:
            text += f"\n**背景信息**: {context}\n"
        
        text += "\n请提供详细的专业解读和发展建议。"
        return text
    
    def generate_team_report(self, team_discs: list) -> dict:
        """
        生成团队DISC组合分析报告
        
        team_discs: [{"name": "张三", "D": 80, "I": 60, "S": 40, "C": 50}, ...]
        """
        system_prompt = """你是团队动力学专家。分析团队成员的DISC组合，提供：
1. 团队整体风格画像
2. 潜在冲突点预警
3. 协作优化建议
4. 任务分配策略"""
        
        user_content = "团队成员DISC数据:\n" + json.dumps(team_discs, ensure_ascii=False, indent=2)
        
        payload = {
            "model": "kimi-k2-5",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.6,
            "max_tokens": 2500
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        
        return response.json()["choices"][0]["message"]["content"]


# ============ 使用示例 ============

if __name__ == "__main__":
    # 初始化（替换为你的API Key）
    analyzer = KimiDISCAnalyzer(api_key="sk-your-api-key-here")
    
    # 示例1：个人DISC分析
    personal_scores = {
        "D": 85,  # 高支配型
        "I": 45,
        "S": 30,
        "C": 65
    }
    
    result = analyzer.analyze_disc(
        disc_scores=personal_scores,
        context="软件公司技术总监，管理团队15人，面临产品上线压力"
    )
    
    print("=== DISC分析报告 ===")
    print(result["analysis"])
    print(f"\nToken消耗: {result['usage']}")
    
    # 示例2：团队分析
    team_data = [
        {"name": "李明", "role": "产品经理", "D": 70, "I": 80, "S": 40, "C": 50},
        {"name": "王芳", "role": "开发主管", "D": 60, "I": 30, "S": 50, "C": 85},
        {"name": "张伟", "role": "UI设计师", "D": 40, "I": 75, "S": 70, "C": 45}
    ]
    
    team_report = analyzer.generate_team_report(team_data)
    print("\n=== 团队分析报告 ===")
    print(team_report)