import sqlite3

conn = sqlite3.connect('intent_money.db')
cursor = conn.cursor()

# 查看 market_hots 表结构
cursor.execute("PRAGMA table_info(market_hots)")
print('market_hots 表结构:')
for row in cursor.fetchall():
    print(f'  {row}')

# 查看 content_tasks 表结构
cursor.execute("PRAGMA table_info(content_tasks)")
print('\ncontent_tasks 表结构:')
for row in cursor.fetchall():
    print(f'  {row}')

# 查看 content_structures 表结构
cursor.execute("PRAGMA table_info(content_structures)")
print('\ncontent_structures 表结构:')
for row in cursor.fetchall():
    print(f'  {row}')

conn.close()
