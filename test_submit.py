import requests
import json

# 测试登录
login_data = {
    'username': 'test',
    'password': 'test123'
}

# 首先登录获取会话
with requests.Session() as session:
    # 登录
    login_response = session.post('http://localhost:5000/login', data=login_data)
    print('登录状态码:', login_response.status_code)
    
    # 模拟测评数据
    test_data = {}
    # 假设只有一个题目
    test_data['1'] = {
        'M': '0',  # 最符合选项
        'L': '1'   # 最不符合选项
    }
    
    # 提交测评数据
    submit_response = session.post('http://localhost:5000/result', json=test_data)
    print('提交状态码:', submit_response.status_code)
    print('提交响应:', submit_response.json())

print('测试完成')
