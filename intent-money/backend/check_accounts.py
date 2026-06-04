import sqlite3

conn = sqlite3.connect('intent_money.db')
cursor = conn.cursor()

# 查看表结构
cursor.execute("PRAGMA table_info(user_platform_accounts)")
print('user_platform_accounts 表结构:')
for row in cursor.fetchall():
    print(f'  {row}')

# 查看数据
cursor.execute('SELECT * FROM user_platform_accounts LIMIT 5')
print('\n用户平台账号数据:')
for row in cursor.fetchall():
    print(row)

conn.close()
