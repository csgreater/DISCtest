import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 硬编码密钥
# 应改为从环境变量读取

# 先定义验证函数
def validate_questions():
    for q_num, question in enumerate(questions, 1):
        dimensions = [opt['dimension'] for opt in question]
        # 确保每个题目包含D/I/S/C四个不同维度
        if sorted(dimensions) != ['C', 'D', 'I', 'S']:
            raise ValueError(f"第{q_num}题维度错误，应包含D/I/S/C各一次")

# 然后加载数据
try:
    with open('questions.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)
    validate_questions()
except FileNotFoundError:
    print("未找到questions.json文件")
    import sys
    sys.exit(1)
except json.JSONDecodeError:
    print("questions.json 文件格式有误，请检查 JSON 格式。")
    import sys
    sys.exit(1)

# 存储用户选择结果
results = {i: {"M": None, "L": None} for i in range(1, len(questions) + 1)}


@app.route('/')
def index():
    return render_template('index.html', questions=questions)  # 首页模板


@app.route('/test', methods=['GET', 'POST'])
def test():
    if 'user' not in session:  # 应添加会话验证
        return redirect(url_for('index'))
    if request.method == 'POST':
        # 处理答案并计算分数
        session['scores'] = calculate_scores(request.form)
        return redirect(url_for('result'))
    return render_template('test.html', questions=questions)  # 测试页模板


def calculate_scores(answers):
    scores = {'D':0, 'I':0, 'S':0, 'C':0}
    for q_id, choices in answers.items():
        question = questions[int(q_id)-1]
        
        # 最符合选项处理
        m_index = int(choices["M"])
        m_dim = question[m_index]['dimension']
        scores[m_dim] += 3  # 最符合得3分
        
        # 最不符合选项处理
        l_index = int(choices["L"])
        l_dim = question[l_index]['dimension']
        
        # 根据DISC四象限规则调整分数
        if l_dim == 'D':
            scores['I'] += 1
            scores['S'] += 1
            scores['C'] += 1
        elif l_dim == 'I':
            scores['D'] += 1
            scores['S'] += 1
            scores['C'] += 1
        elif l_dim == 'S':
            scores['D'] += 1
            scores['I'] += 1
            scores['C'] += 1
        elif l_dim == 'C':
            scores['D'] += 1
            scores['I'] += 1
            scores['S'] += 1
    return scores


@app.route('/result')
def result():
    if 'scores' not in session:
        return redirect(url_for('index'))
    scores = session.get('scores', {})
    personality = max(scores, key=scores.get)  # 获取最高分类型
    return render_template('result.html',  # 结果页模板
                         personality=personality,
                         scores=scores)


@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.get_json()
        for q_num, choices in data.items():
            q_num = int(q_num)
            # 确保数值类型正确
            results[q_num]["M"] = int(choices["M"])
            results[q_num]["L"] = int(choices["L"])
        return jsonify({"status": "success"})
    except Exception as e:
        error_message = f"提交数据时出错: {str(e)}"
        return jsonify({"status": "error", "message": error_message}), 500


@app.route('/results')
def show_results():
    try:
        # 初始化四个维度的计数器
        m_dimension_counts = {'D':0, 'I':0, 'S':0, 'C':0}
        l_dimension_counts = {'D':0, 'I':0, 'S':0, 'C':0}
        
        for q_num, result in results.items():
            question = questions[int(q_num)-1]
            
            # 处理最符合选项
            if result["M"] is not None:
                m_index = result["M"]
                m_dimension = question[m_index]['dimension']
                m_dimension_counts[m_dimension] += 1
                
            # 处理最不符合选项
            if result["L"] is not None:
                l_index = result["L"]
                l_dimension = question[l_index]['dimension']
                l_dimension_counts[l_dimension] += 1
                
        return render_template('results.html',
                             m_counts=m_dimension_counts,
                             l_counts=l_dimension_counts,
                             # 新增差值计算
                             diff_counts={
                                 'D': m_dimension_counts['D'] - l_dimension_counts['D'],
                                 'I': m_dimension_counts['I'] - l_dimension_counts['I'],
                                 'S': m_dimension_counts['S'] - l_dimension_counts['S'],
                                 'C': m_dimension_counts['C'] - l_dimension_counts['C']
                             })
    except Exception as e:
        error_message = f"渲染结果页面模板时出错: {str(e)}"
        return error_message, 500


@app.route('/validate')
def validate_questions_route():
    try:
        validate_questions()
        return "题目数据验证通过", 200
    except Exception as e:
        return f"题目数据错误: {str(e)}", 500


if __name__ == '__main__':
    try:
        app.run(debug=True)
    except Exception as e:
        print(f"启动 Flask 应用时出错: {str(e)}")