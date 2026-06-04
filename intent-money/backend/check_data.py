import sqlite3
from datetime import datetime
import json

conn = sqlite3.connect('intent_money.db')
cursor = conn.cursor()

# 查看最新的任务
cursor.execute('''
    SELECT id, platform_id, title, created_at, status, hook_text, structure_id
    FROM content_tasks
    ORDER BY created_at DESC
    LIMIT 3
''')
print('最新任务 (最近3条):')
tasks = cursor.fetchall()
if tasks:
    for row in tasks:
        task_id, platform_id, title, created_at, status, hook_text, structure_id = row
        print(f'\n任务ID: {task_id}')
        print(f'平台ID: {platform_id}')
        print(f'标题: {title}')
        print(f'创建时间: {created_at}')
        print(f'状态: {status}')
        print(f'钩子文本: {hook_text[:80]}...' if hook_text and len(hook_text) > 80 else f'钩子文本: {hook_text}')
        print(f'使用结构ID: {structure_id}')
else:
    print('没有找到任务')

# 查看市场热门数据
cursor.execute('''
    SELECT id, platform_id, keyword, hot_type, created_at, is_active, priority_boost, analysis_result
    FROM market_hots
    ORDER BY created_at DESC
    LIMIT 5
''')
print('\n' + '='*80)
print('\n最新市场热门数据 (最近5条):')
hots = cursor.fetchall()
if hots:
    for row in hots:
        hot_id, platform_id, keyword, hot_type, created_at, is_active, priority_boost, analysis_result = row
        print(f'\n热门ID: {hot_id}')
        print(f'平台ID: {platform_id}')
        print(f'关键词: {keyword}')
        print(f'类型: {hot_type}')
        print(f'创建时间: {created_at}')
        print(f'是否活跃: {is_active}')
        print(f'优先级提升: {priority_boost}')
        if analysis_result:
            try:
                result = json.loads(analysis_result)
                print(f'分析结果: {json.dumps(result, ensure_ascii=False, indent=2)[:200]}...')
            except:
                print(f'分析结果: {analysis_result[:100]}...')
else:
    print('没有找到市场热门数据')

# 查看内容结构
cursor.execute('''
    SELECT id, intent_id, platform_id, hook_type, priority, market_score
    FROM content_structures
    WHERE is_active = 1
    ORDER BY priority DESC
    LIMIT 5
''')
print('\n' + '='*80)
print('\n活跃的内容结构 (按优先级排序):')
structures = cursor.fetchall()
if structures:
    for row in structures:
        struct_id, intent_id, platform_id, hook_type, priority, market_score = row
        print(f'\n结构ID: {struct_id}')
        print(f'意图ID: {intent_id}')
        print(f'平台ID: {platform_id}')
        print(f'钩子类型: {hook_type}')
        print(f'优先级: {priority}')
        print(f'市场分数: {market_score}')
else:
    print('没有找到活跃的内容结构')

conn.close()
