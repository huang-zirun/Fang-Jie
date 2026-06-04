from app.services.ai_service import FALLBACK_POOL

print(f'FALLBACK_POOL总数: {len(FALLBACK_POOL)}\n')

# 检查每个fallback的完整性
issues = []
for i, f in enumerate(FALLBACK_POOL, 1):
    # 检查必需字段
    if not f.get('hook_text'):
        issues.append(f'Fallback {i}: 缺少hook_text')
    if not f.get('storyboard') or len(f.get('storyboard', [])) < 3:
        issues.append(f'Fallback {i}: storyboard不足3个')
    if not f.get('script_text'):
        issues.append(f'Fallback {i}: 缺少script_text')
    if not f.get('title'):
        issues.append(f'Fallback {i}: 缺少title')
    if not f.get('comment_template'):
        issues.append(f'Fallback {i}: 缺少comment_template')
    if not f.get('why_it_works'):
        issues.append(f'Fallback {i}: 缺少why_it_works')
    if not f.get('tags'):
        issues.append(f'Fallback {i}: 缺少tags')
    if not f.get('platforms'):
        issues.append(f'Fallback {i}: 缺少platforms')
    
    # 检查长度要求
    if len(f.get('hook_text', '')) > 30:
        issues.append(f'Fallback {i}: hook_text超过30字 ({len(f.get("hook_text", ""))}字)')
    
    script_len = len(f.get('script_text', ''))
    if script_len < 200:
        issues.append(f'Fallback {i}: script_text不足200字 ({script_len}字)')

if issues:
    print('⚠️ 发现以下问题:')
    for issue in issues:
        print(f'  - {issue}')
else:
    print('✅ 所有fallback都符合要求!')

# 统计信息
print(f'\n统计信息:')
script_lengths = [len(f.get('script_text', '')) for f in FALLBACK_POOL]
print(f'  script_text长度范围: {min(script_lengths)}-{max(script_lengths)}字')
print(f'  script_text平均长度: {sum(script_lengths)/len(script_lengths):.0f}字')

hook_lengths = [len(f.get('hook_text', '')) for f in FALLBACK_POOL]
print(f'  hook_text长度范围: {min(hook_lengths)}-{max(hook_lengths)}字')

storyboard_counts = [len(f.get('storyboard', [])) for f in FALLBACK_POOL]
print(f'  storyboard数量范围: {min(storyboard_counts)}-{max(storyboard_counts)}个')
