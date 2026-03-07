from app import app, db, User, Result

print("测试数据库连接和数据存储...")

# 测试数据库连接
with app.app_context():
    print("测试数据库连接...")
    try:
        # 尝试查询用户
        users = User.query.all()
        print(f"数据库查询成功，找到 {len(users)} 个用户")
        for user in users:
            print(f"用户: {user.username}, 角色: {user.role}")
        
        # 尝试查询测评记录
        results = Result.query.all()
        print(f"找到 {len(results)} 条测评记录")
        for result in results:
            print(f"记录ID: {result.id}, 用户ID: {result.user_id}, 时间: {result.timestamp}, 人格类型: {result.personality}")
        
    except Exception as e:
        print(f"数据库查询失败: {str(e)}")

print("测试完成")
