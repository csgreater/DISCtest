from app import app

print("测试Flask应用创建...")
print(f"应用创建成功: {app is not None}")
print(f"应用配置: {app.config}")

# 测试路由
print("\n测试路由...")
for rule in app.url_map.iter_rules():
    print(f"路由: {rule}")

print("\n测试完成")