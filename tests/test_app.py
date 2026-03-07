from app import app, db, User

print("测试Flask应用初始化...")

# 测试数据库连接
with app.app_context():
    print("测试数据库连接...")
    try:
        # 尝试查询用户
        users = User.query.all()
        print(f"数据库查询成功，找到 {len(users)} 个用户")
    except Exception as e:
        print(f"数据库查询失败: {str(e)}")

print("测试完成")
