import os
import sys

# 从packages/core目录运行
os.chdir('C:/Users/Administrator/.openclaw/workspace/neuralsite/packages/core')

# 添加路径
sys.path.insert(0, 'C:/Users/Administrator/.openclaw/workspace/neuralsite/packages/core')
sys.path.insert(0, 'C:/Users/Administrator/.openclaw/workspace/neuralsite/packages/core/core')

os.environ['DATABASE_URL'] = 'sqlite:///./neuralsite.db'

try:
    from api.main import app
    print("OK: API import successful!")
    print("Routes registered:", len(app.routes))
    
    # 列出所有路由
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append(route.path)
    
    print("Total routes:", len(routes))
    
    # 检查P0路由
    p0_routes = [r for r in routes if '/api/v1/' in r]
    print("\nP0 routes:", len(p0_routes))
    for r in p0_routes:
        print("  ", r)
    
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
