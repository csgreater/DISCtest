

```markdown'''
# DISC 性格测试系统

基于Flask框架开发的DISC性格测评工具，提供完整的测试流程、自动计分和可视化分析功能。

## 主要功能

✅ 自动题目验证  
✅ 动态计分系统  
✅ 双维度图表分析  
✅ 响应式界面设计  
✅ 测试结果持久化

## 技术栈

- **前端**: HTML5/CSS3 + ECharts 可视化
- **后端**: Python 3.10 + Flask 2.0
- **数据存储**: JSON 格式题目库
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

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 安装依赖
pip install flask
```

### 运行应用
```bash
flask run --port 8080
```
访问 http://localhost:8080 开始测试

## 项目结构
```
disctest/
├── app.py                 # 主程序
├── questions.json         # 题目数据库
├── templates/            # 前端模板
│   ├── index.html         # 首页
│   ├── test.html          # 测试页
│   └── results.html       # 结果页
└── generate_questions.py  # 题目生成工具
```

## 核心配置

### 题目验证规则
```python
def validate_questions():
    # 每个题目必须包含D/I/S/C四个维度
    required_dimensions = {'D', 'I', 'S', 'C'}
    # 题目顺序模式验证
    expected_patterns = [...]
```

### 计分规则
```python
def calculate_scores(answers):
    # 最符合选项 +3分
    # 最不符合选项触发其他维度 +1分
    # 详细计分逻辑见源码
```

## 定制开发

### 修改题目
1. 编辑 `questions.json`
2. 保持维度顺序模式
3. 访问 `/validate` 验证题目结构

### 调整样式
- 图表样式: 修改 `templates/results.html` 中的 ECharts 配置
- 页面布局: 调整 `static/css/main.css`

## 常见问题

Q: 启动时报错 "未找到questions.json"  
A: 确保文件位于项目根目录，并验证JSON格式

Q: 图表不显示  
A: 检查浏览器控制台，确保网络可访问CDN资源

Q: 测试结果异常  
A: 访问 `/validate` 验证题目数据完整性

## 授权协议
MIT License
```