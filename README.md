

# DISC 性格测试系统

基于Flask框架开发的DISC性格测评工具，提供完整的测试流程、自动计分和可视化分析功能。

## 主要功能

✅ 用户注册与登录系统  
✅ 完整的DISC测试流程  
✅ 自动题目验证  
✅ 动态计分系统  
✅ 双维度图表分析  
✅ 响应式界面设计  
✅ 测试结果持久化  
✅ 个人测评记录管理  
✅ 管理员查看所有记录  
✅ 测评记录导出功能

## 技术栈

- **前端**: HTML5/CSS3 + ECharts 可视化
- **后端**: Python 3.10 + Flask 2.0
- **数据存储**: SQLite 数据库 + JSON 格式题目库
- **依赖管理**: pip

## 快速启动

### 环境要求
- Python 3.10+
- Chrome/Firefox 最新版

### 安装步骤
```bash
# 克隆仓库
git clone https://github.com/yourusername/disctest.git
cd disctest

# 安装依赖
python -m pip install -r requirements.txt
```

### 运行应用
```bash
# 方法1: 直接运行
python app.py

# 方法2: 使用Flask命令
python -m flask run --port 8080
```
访问 http://localhost:5000 (方法1) 或 http://localhost:8080 (方法2) 开始测试

## 项目结构
```
disctest/
├── app.py                 # 主程序
├── questions.json         # 题目数据库
├── requirements.txt       # 依赖配置
├── templates/            # 前端模板
│   ├── index.html         # 首页
│   ├── login.html         # 登录页
│   ├── register.html      # 注册页
│   ├── test.html          # 测试页
│   ├── result.html        # 结果页
│   ├── results.html       # 结果统计页
│   ├── my_records.html    # 个人记录页
│   └── all_records.html   # 管理员记录页
├── test_app.py            # 测试脚本
└── generate_questions.py  # 题目生成工具
```

## 核心功能说明

### 用户系统
- **注册**: 创建新用户账号
- **登录**: 使用账号密码登录
- **注销**: 退出当前账号
- **默认账号**: 
  - 管理员: admin / admin123
  - 测试用户: test / test123

### 测试流程
1. 登录系统
2. 进入测试页面，回答20道题目
3. 每道题目选择最符合和最不符合的选项
4. 提交后系统自动计算得分
5. 查看测试结果和分析报告

### 计分规则
```python
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
```

### 结果分析
- **人格类型**: 得分最高的维度
- **维度得分**: 四个维度的具体得分
- **可视化图表**: 使用ECharts展示得分情况
- **历史记录**: 查看个人过往测评记录

### 管理功能
- **查看所有记录**: 管理员可以查看所有用户的测评记录
- **导出记录**: 支持导出个人或所有用户的测评记录为CSV格式

## 定制开发

### 修改题目
1. 编辑 `questions.json`
2. 保持每个题目包含D/I/S/C四个维度
3. 访问 `/validate` 验证题目结构

### 调整样式
- 图表样式: 修改 `templates/result.html` 中的 ECharts 配置
- 页面布局: 调整模板文件中的HTML和CSS

## 常见问题

Q: 启动时报错 "未找到questions.json"  
A: 确保文件位于项目根目录，并验证JSON格式

Q: 图表不显示  
A: 检查浏览器控制台，确保网络可访问CDN资源

Q: 测试结果异常  
A: 访问 `/validate` 验证题目数据完整性

Q: 无法登录  
A: 检查用户名和密码是否正确，默认账号为admin/admin123或test/test123

## 授权协议
MIT License