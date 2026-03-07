from app import app, db, User, Result
from flask import session

print("测试完整的测评流程...")

with app.app_context():
    # 模拟用户登录
    with app.test_client() as client:
        # 登录
        login_response = client.post('/login', data={
            'username': 'test',
            'password': 'test123'
        })
        print('登录状态码:', login_response.status_code)
        
        # 模拟测评数据
        test_data = {
            '1': {
                'M': '0',
                'L': '1'
            }
        }
        
        # 提交测评数据
        import json
        submit_response = client.post('/result', data={
            'data': json.dumps(test_data)
        })
        print('提交状态码:', submit_response.status_code)
        print('提交响应:', submit_response.data)

# 检查数据库中的测评记录
with app.app_context():
    results = Result.query.all()
    print(f"找到 {len(results)} 条测评记录")
    for result in results:
        print(f"记录ID: {result.id}, 用户ID: {result.user_id}, 时间: {result.timestamp}, 人格类型: {result.personality}")

print('测试完成')
