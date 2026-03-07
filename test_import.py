print("测试模块导入...")
try:
    import json
    import os
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    print("基础模块导入成功")
except Exception as e:
    print(f"基础模块导入失败: {e}")

print("测试完成")
