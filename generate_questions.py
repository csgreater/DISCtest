import json

templates = [
    {
        "D": "形容词1",
        "I": "形容词2", 
        "S": "形容词3",
        "C": "形容词4"
    },
    # ...共20个模板
]

patterns = [
    ['D', 'I', 'S', 'C'],  # 第1/6/11/16题
    ['C', 'S', 'I', 'D'],  # 第2/7/12/17题
    ['D', 'I', 'C', 'S'],  # 第3/8/13/18题
    ['C', 'I', 'D', 'S'],  # 第4/9/14/19题
    ['I', 'D', 'C', 'S']   # 第5/10/15/20题
]

questions = []
for i in range(20):
    pattern_idx = i % 5  # 每5题循环一次模式
    current_pattern = patterns[pattern_idx]
    
    question = [
        {"text": f"选项1描述", "dimension": current_pattern[0]},
        {"text": f"选项2描述", "dimension": current_pattern[1]},
        {"text": f"选项3描述", "dimension": current_pattern[2]},
        {"text": f"选项4描述", "dimension": current_pattern[3]}
    ]
    questions.append(question)

with open('questions.json', 'w', encoding='utf-8') as f:
    json.dump(questions, f, ensure_ascii=False, indent=2) 