import json
import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_fallback_key')  # 从环境变量读取密钥

# 配置数据库
import os
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'disc_test.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 定义模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # user 或 admin

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    scores = db.Column(db.JSON, nullable=False)  # 存储各维度得分
    personality = db.Column(db.String(1), nullable=False)  # 最终人格类型
    raw_data = db.Column(db.JSON, nullable=True)  # 存储原始测评数据（M和L选择）

    user = db.relationship('User', backref=db.backref('results', lazy=True))

# 先定义验证函数
def validate_questions(questions):
    for q_num, question in enumerate(questions, 1):
        dimensions = [opt['dimension'] for opt in question]
        # 确保每个题目包含D/I/S/C四个不同维度
        if sorted(dimensions) != ['C', 'D', 'I', 'S']:
            raise ValueError(f"第{q_num}题维度错误，应包含D/I/S/C各一次")

# 然后加载数据
try:
    with open('questions.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)
    validate_questions(questions)
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

# 角色检查装饰器
from functools import wraps
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            return "权限不足", 403
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', questions=questions)  # 首页模板


@app.route('/test', methods=['GET'])
def test():
    if 'user' not in session:  # 应添加会话验证
        return redirect(url_for('login'))
    # 初始化会话中的题目进度和答案
    session['current_question'] = 1
    session['answers'] = {}
    return redirect(url_for('question', q_num=1))


@app.route('/question/<int:q_num>', methods=['GET', 'POST'])
def question(q_num):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # 确保q_num在有效范围内
    if q_num < 1 or q_num > len(questions):
        if q_num > len(questions):
            # 所有题目已完成，提交结果
            # 直接提交，不需要再点击提交按钮
            return redirect(url_for('submit_test', _method='POST'))
        return redirect(url_for('question', q_num=1))
    
    if request.method == 'POST':
        # 处理当前题目的提交
        try:
            m_value = request.form.get('m')
            l_value = request.form.get('l')
            
            if not m_value or not l_value:
                return render_template('question.html', 
                                   question=questions[q_num-1], 
                                   q_num=q_num, 
                                   total=len(questions),
                                   error='请选择最符合和最不符合的选项！')
            
            if m_value == l_value:
                return render_template('question.html', 
                                   question=questions[q_num-1], 
                                   q_num=q_num, 
                                   total=len(questions),
                                   error='最符合和最不符合不能选择相同的选项，请重新选择！')
            
            # 存储答案
            if 'answers' not in session:
                session['answers'] = {}
            session['answers'][str(q_num)] = {
                "M": m_value,
                "L": l_value
            }
            # 确保session数据被保存
            session.modified = True
            
            # 跳转到下一题
            if q_num < len(questions):
                return redirect(url_for('question', q_num=q_num+1))
            else:
                # 最后一题，直接提交
                return redirect(url_for('submit_test', _method='POST'))
        except Exception as e:
            return render_template('question.html', 
                               question=questions[q_num-1], 
                               q_num=q_num, 
                               total=len(questions),
                               error=f'处理请求时出错: {str(e)}')
    
    # GET请求，显示当前题目
    # 从session中获取之前的答案
    answers = session.get('answers', {})
    current_answer = answers.get(str(q_num), {})
    m_value = current_answer.get('M')
    l_value = current_answer.get('L')
    
    return render_template('question.html', 
                       question=questions[q_num-1], 
                       q_num=q_num, 
                       total=len(questions),
                       m_value=m_value,
                       l_value=l_value)


@app.route('/submit_test', methods=['POST', 'GET'])
def submit_test():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # 检查是否所有题目都已回答
    answers = session.get('answers', {})
    if len(answers) != len(questions):
        # 重定向到未完成的题目
        for i in range(1, len(questions)+1):
            if str(i) not in answers:
                return redirect(url_for('question', q_num=i))
    
    # 直接处理最终提交，无论请求方法是什么
    try:
        # 计算分数
        scores = calculate_scores(answers)
        session['scores'] = scores
        # 存储原始数据到session
        session['raw_data'] = answers
        # 确保session数据被保存
        session.modified = True
        personality = max(scores, key=scores.get)  # 获取最高分类型
        
        # 存储测评结果到数据库
        user_id = session['user_id']
        new_result = Result(user_id=user_id, scores=scores, personality=personality, raw_data=answers)
        db.session.add(new_result)
        db.session.commit()
        
        # 清除会话中的答案和进度
        session.pop('answers', None)
        session.pop('current_question', None)
        # 确保session数据被保存
        session.modified = True
        
        # 重定向到结果页面
        return redirect(url_for('result'))
    except Exception as e:
        print(f'处理提交时出错: {str(e)}')
        return f"处理请求时出错: {str(e)}", 500


@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录功能"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:  # 实际应该使用密码哈希
            session['user'] = username
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('test'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册功能"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "用户名已存在，请选择其他用户名"
        
        # 创建新用户，默认角色为user
        new_user = User(username=username, password=password, name=name, role='user')
        db.session.add(new_user)
        db.session.commit()
        
        # 注册成功后跳转到登录页面
        return redirect(url_for('login'))
    return render_template('register.html')


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


def generate_disc_report(scores, personality):
    """生成DISC测评文字版报告"""
    report = {
        'summary': '',
        'animal': '',
        'dimensions': {},
        'strengths': [],
        'weaknesses': [],
        'career': '',
        'communication': ''
    }
    
    # 计算各维度得分比例
    total = sum(scores.values())
    percentages = {dim: round(score/total*100, 1) for dim, score in scores.items()}
    
    # 总结部分
    if personality == 'D':
        report['animal'] = '老虎'
        report['summary'] = "您的性格类型为支配型(D)，像一只威风凛凛的老虎。您是一个目标明确、行动迅速的人，喜欢掌控局面，追求结果。您具有强烈的领导力和决策能力，能够在压力下保持冷静并迅速做出判断。"
    elif personality == 'I':
        report['animal'] = '孔雀'
        report['summary'] = "您的性格类型为影响型(I)，像一只光彩夺目的孔雀。您是一个热情开朗、善于社交的人，喜欢与人互动，富有感染力。您具有良好的沟通能力和创造力，能够激励他人并营造积极的氛围。"
    elif personality == 'S':
        report['animal'] = '考拉'
        report['summary'] = "您的性格类型为稳健型(S)，像一只温和可爱的考拉。您是一个稳重可靠、注重和谐的人，喜欢稳定的环境，善于团队合作。您具有强烈的责任心和耐心，能够为团队提供支持和保障。"
    elif personality == 'C':
        report['animal'] = '猫头鹰'
        report['summary'] = "您的性格类型为谨慎型(C)，像一只智慧敏锐的猫头鹰。您是一个逻辑严谨、注重细节的人，喜欢分析思考，追求完美。您具有较强的问题解决能力和专注力，能够确保工作的准确性和质量。"
    
    # 各维度详细分析
    report['dimensions'] = {
        'D': f"支配型(D)得分：{scores['D']}分 ({percentages['D']}%)。{'您在这一维度表现突出，' if scores['D'] == max(scores.values()) else ''}体现了您的目标导向、决策能力和领导力。",
        'I': f"影响型(I)得分：{scores['I']}分 ({percentages['I']}%)。{'您在这一维度表现突出，' if scores['I'] == max(scores.values()) else ''}体现了您的社交能力、创造力和感染力。",
        'S': f"稳健型(S)得分：{scores['S']}分 ({percentages['S']}%)。{'您在这一维度表现突出，' if scores['S'] == max(scores.values()) else ''}体现了您的可靠性、团队精神和耐心。",
        'C': f"谨慎型(C)得分：{scores['C']}分 ({percentages['C']}%)。{'您在这一维度表现突出，' if scores['C'] == max(scores.values()) else ''}体现了您的分析能力、专注力和追求完美的精神。"
    }
    
    # 优势分析
    if personality == 'D':
        report['strengths'] = [
            "目标明确，行动迅速",
            "决策果断，敢于冒险",
            "领导力强，能够掌控局面",
            "抗压能力强，在压力下保持冷静"
        ]
    elif personality == 'I':
        report['strengths'] = [
            "热情开朗，善于社交",
            "沟通能力强，富有感染力",
            "创造力丰富，思维活跃",
            "能够激励他人，营造积极氛围"
        ]
    elif personality == 'S':
        report['strengths'] = [
            "稳重可靠，责任心强",
            "注重团队和谐，善于合作",
            "耐心细致，服务意识强",
            "情绪稳定，能够提供支持"
        ]
    elif personality == 'C':
        report['strengths'] = [
            "逻辑严谨，分析能力强",
            "注重细节，追求完美",
            "专注力强，工作质量高",
            "问题解决能力强，思维缜密"
        ]
    
    # 待发展领域
    if personality == 'D':
        report['weaknesses'] = [
            "可能过于直接，忽视他人感受",
            "有时过于急躁，缺乏耐心",
            "可能过于强势，不善于倾听",
            "可能忽视细节，注重结果而忽略过程"
        ]
    elif personality == 'I':
        report['weaknesses'] = [
            "可能过于情绪化，缺乏理性",
            "有时注意力分散，不够专注",
            "可能过于乐观，忽视潜在风险",
            "可能缺乏条理性，不够细致"
        ]
    elif personality == 'S':
        report['weaknesses'] = [
            "可能过于保守，不愿冒险",
            "有时缺乏主见，容易妥协",
            "可能过于追求和谐，避免冲突",
            "可能反应较慢，适应变化能力有待提高"
        ]
    elif personality == 'C':
        report['weaknesses'] = [
            "可能过于挑剔，追求完美主义",
            "有时过于谨慎，决策缓慢",
            "可能过于理性，缺乏情感表达",
            "可能过于专注细节，忽视整体"
        ]
    
    # 职业建议
    if personality == 'D':
        report['career'] = "适合需要决策能力、领导力和目标导向的职业，如企业家、管理者、销售经理、项目经理等。"
    elif personality == 'I':
        report['career'] = "适合需要社交能力、创造力和表达能力的职业，如市场营销、公关、教育培训、演艺等。"
    elif personality == 'S':
        report['career'] = "适合需要稳定性、责任心和团队合作的职业，如人力资源、客户服务、行政助理、教师等。"
    elif personality == 'C':
        report['career'] = "适合需要分析能力、专注力和精确度的职业，如财务、IT、科研、质量控制等。"
    
    # 沟通建议
    if personality == 'D':
        report['communication'] = "在沟通中，建议您多倾听他人意见，注重团队合作，适当表达对他人的认可和赞赏。"
    elif personality == 'I':
        report['communication'] = "在沟通中，建议您保持专注，注重事实和数据，提高决策的客观性和条理性。"
    elif personality == 'S':
        report['communication'] = "在沟通中，建议您增强自信，勇于表达自己的观点，学会在适当的时候说'不'。"
    elif personality == 'C':
        report['communication'] = "在沟通中，建议您多关注他人的情感需求，增强灵活性，学会欣赏不同的观点和方法。"
    
    return report


@app.route('/result', methods=['GET', 'POST'])
def result():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # 从请求中获取测评数据
            if request.is_json:
                data = request.get_json()
            else:
                data_str = request.form.get('data')
                import json
                data = json.loads(data_str)
            print('接收到的测评数据:', data)
            # 计算分数
            scores = calculate_scores(data)
            print('计算的分数:', scores)
            session['scores'] = scores
            # 确保session数据被保存
            session.modified = True
            personality = max(scores, key=scores.get)  # 获取最高分类型
            print('最终人格类型:', personality)
            
            # 存储测评结果到数据库
            user_id = session['user_id']
            print('用户ID:', user_id)
            # 存储原始数据（如果有）
            raw_data = session.get('raw_data', None)
            new_result = Result(user_id=user_id, scores=scores, personality=personality, raw_data=raw_data)
            db.session.add(new_result)
            db.session.commit()
            print('测评结果存储成功')
            
            # 重定向到结果页面
            return redirect(url_for('result'))
        except Exception as e:
            print('处理POST请求时出错:', str(e))
            return f"处理请求时出错: {str(e)}", 500
    
    # GET请求时显示结果
    if 'scores' not in session:
        return redirect(url_for('index'))
    scores = session.get('scores', {})
    personality = max(scores, key=scores.get)  # 获取最高分类型
    
    # 生成文字版测评报告
    report = generate_disc_report(scores, personality)
    
    # 计算最符合(M)和差异值，用于绘制图表
    m_counts = {'D': 0, 'I': 0, 'S': 0, 'C': 0}
    l_counts = {'D': 0, 'I': 0, 'S': 0, 'C': 0}
    
    # 检查 raw_data 是否存在
    raw_data = session.get('raw_data', None)
    if not raw_data:
        # 如果没有raw_data，尝试从最近的测评记录中获取
        user_id = session['user_id']
        latest_result = Result.query.filter_by(user_id=user_id).order_by(Result.timestamp.desc()).first()
        if latest_result and latest_result.raw_data:
            raw_data = latest_result.raw_data
    
    if raw_data:
        for q_num, choices in raw_data.items():
            question = questions[int(q_num)-1]
            
            # 处理最符合选项
            if choices["M"] is not None:
                m_index = int(choices["M"])
                m_dimension = question[m_index]['dimension']
                m_counts[m_dimension] += 1
                
            # 处理最不符合选项
            if choices["L"] is not None:
                l_index = int(choices["L"])
                l_dimension = question[l_index]['dimension']
                l_counts[l_dimension] += 1
    
    # 计算差异值
    diff_counts = {
        'D': m_counts['D'] - l_counts['D'],
        'I': m_counts['I'] - l_counts['I'],
        'S': m_counts['S'] - l_counts['S'],
        'C': m_counts['C'] - l_counts['C']
    }
    
    return render_template('results.html',  # 结果页模板
                         scores=scores,
                         personality=personality,
                         report=report,
                         m_counts=m_counts,
                         l_counts=l_counts,
                         diff_counts=diff_counts)


@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.get_json()
        # 存储原始数据到 session
        session['raw_data'] = data
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
        
        # 准备计算分数的数据
        score_data = {}
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
            
            # 准备计算分数的数据
            score_data[q_num] = {
                "M": result["M"],
                "L": result["L"]
            }
        
        # 计算分数并存储到数据库
        if 'user_id' in session and score_data:
            scores = calculate_scores(score_data)
            session['scores'] = scores
            personality = max(scores, key=scores.get)  # 获取最高分类型
            
            # 存储测评结果到数据库
            user_id = session['user_id']
            new_result = Result(user_id=user_id, raw_data=score_data, scores=scores, personality=personality)
            db.session.add(new_result)
            db.session.commit()
            print('测评结果存储成功')
        
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
        print('处理results路由时出错:', str(e))
        error_message = f"渲染结果页面模板时出错: {str(e)}"
        return error_message, 500


@app.route('/validate')
def validate_questions_route():
    try:
        validate_questions(questions)
        return "题目数据验证通过", 200
    except Exception as e:
        return f"题目数据错误: {str(e)}", 500


@app.route('/logout')
def logout():
    """注销功能"""
    session.pop('user', None)
    session.pop('user_id', None)
    session.pop('role', None)
    session.pop('scores', None)
    return redirect(url_for('index'))


@app.route('/my_records')
def my_records():
    """查看个人测评记录"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    # 查询当前用户的所有测评记录，按时间倒序排列
    user_results = Result.query.filter_by(user_id=user_id).order_by(Result.timestamp.desc()).all()
    
    return render_template('my_records.html', results=user_results)


@app.route('/result/<int:result_id>')
def view_result(result_id):
    """查看完整的测评结果"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 查询测评记录
    result = Result.query.get(result_id)
    if not result:
        return "测评记录不存在", 404
    
    # 检查权限，只有记录所有者或管理员可以查看
    if result.user_id != session['user_id'] and session.get('role') != 'admin':
        return "权限不足", 403
    
    # 计算最符合(M)和差异值，用于绘制图表
    m_counts = {'D': 0, 'I': 0, 'S': 0, 'C': 0}
    l_counts = {'D': 0, 'I': 0, 'S': 0, 'C': 0}
    
    # 检查 raw_data 是否存在
    if result.raw_data:
        for q_num, choices in result.raw_data.items():
            question = questions[int(q_num)-1]
            
            # 处理最符合选项
            if choices["M"] is not None:
                m_index = int(choices["M"])
                m_dimension = question[m_index]['dimension']
                m_counts[m_dimension] += 1
                
            # 处理最不符合选项
            if choices["L"] is not None:
                l_index = int(choices["L"])
                l_dimension = question[l_index]['dimension']
                l_counts[l_dimension] += 1
    
    # 计算差异值
    diff_counts = {
        'D': m_counts['D'] - l_counts['D'],
        'I': m_counts['I'] - l_counts['I'],
        'S': m_counts['S'] - l_counts['S'],
        'C': m_counts['C'] - l_counts['C']
    }
    
    # 生成文字版测评报告
    report = generate_disc_report(result.scores, result.personality)
    
    return render_template('results.html',
                         result=result,
                         scores=result.scores,
                         personality=result.personality,
                         report=report,
                         m_counts=m_counts,
                         l_counts=l_counts,
                         diff_counts=diff_counts)


@app.route('/all_records')
@admin_required
def all_records():
    """管理员查看所有测评记录"""
    # 查询所有测评记录，按时间倒序排列，包含用户信息
    all_results = Result.query.options(db.joinedload(Result.user)).order_by(Result.timestamp.desc()).all()
    
    return render_template('all_records.html', results=all_results)





# 初始化数据库
print("开始初始化数据库...")
try:
    with app.app_context():
        db.create_all()
        print("数据库表创建成功")
        
        # 检查是否已存在管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # 创建管理员用户
            admin = User(username='admin', password='admin123', name='管理员', role='admin')
            db.session.add(admin)
            
            # 创建测试用户
            test_user = User(username='test', password='test123', name='测试用户', role='user')
            db.session.add(test_user)
            
            db.session.commit()
            print("默认用户创建成功")
        else:
            print("默认用户已存在")
except Exception as e:
    print(f"数据库初始化失败: {str(e)}")

if __name__ == '__main__':
    # 从环境变量获取调试模式，默认为False
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"调试模式: {debug_mode}")
    print("正在启动Flask应用...")
    try:
        # 在生产环境中，应该使用Gunicorn等WSGI服务器运行Flask应用
        print("尝试启动应用...")
        app.run(debug=debug_mode, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"启动 Flask 应用时出错: {str(e)}")
        import traceback
        traceback.print_exc()