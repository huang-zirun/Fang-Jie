"""initial migration - all tables

Revision ID: 000000000000
Revises: 
Create Date: 2026-05-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '000000000000'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. platforms
    op.create_table(
        'platforms',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # 2. intents
    op.create_table(
        'intents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # 3. users
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone')
    )
    
    # 4. user_sessions
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user_sessions', schema=None) as batch_op:
        batch_op.create_index('ix_user_sessions_user_id', ['user_id'])
    
    # 5. content_structures
    op.create_table(
        'content_structures',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('intent_id', sa.Uuid(), nullable=False),
        sa.Column('platform_id', sa.Uuid(), nullable=False),
        sa.Column('hook_type', sa.String(length=30), nullable=False),
        sa.Column('emotion_structure', sa.JSON(), nullable=False),
        sa.Column('conversion_structure', sa.JSON(), nullable=False),
        sa.Column('prompt_template', sa.Text(), nullable=False),
        sa.Column('fallback_content', sa.JSON(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('market_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['intent_id'], ['intents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('content_structures', schema=None) as batch_op:
        batch_op.create_index('ix_content_structures_intent_id', ['intent_id'])
        batch_op.create_index('ix_content_structures_platform_id', ['platform_id'])
    
    # 6. diagnosis_results
    op.create_table(
        'diagnosis_results',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('problem_type', sa.String(length=30), nullable=False),
        sa.Column('problem_desc', sa.String(length=200), nullable=False),
        sa.Column('optimization_direction', sa.String(length=100), nullable=False),
        sa.Column('optimization_detail', sa.Text(), nullable=False),
        sa.Column('ai_analysis', sa.Text(), nullable=True),
        sa.Column('rule_confidence', sa.Float(), nullable=True),
        sa.Column('snapshot_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('days_since_deploy', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('play_trend', sa.String(length=20), nullable=True),
        sa.Column('avg_daily_play_growth', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('diagnosed_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('diagnosis_results', schema=None) as batch_op:
        batch_op.create_index('ix_diagnosis_results_task_id', ['task_id'])
        batch_op.create_unique_constraint('uq_diagnosis_results_task_id', ['task_id'])
    
    # 7. content_tasks
    op.create_table(
        'content_tasks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('intent_id', sa.Uuid(), nullable=False),
        sa.Column('platform_id', sa.Uuid(), nullable=False),
        sa.Column('structure_id', sa.Uuid(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('task_type', sa.String(length=10), nullable=False, server_default='video'),
        sa.Column('hook_text', sa.Text(), nullable=False),
        sa.Column('storyboard', sa.JSON(), nullable=False),
        sa.Column('script_text', sa.Text(), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('comment_template', sa.Text(), nullable=False),
        sa.Column('why_it_works', sa.Text(), nullable=False),
        sa.Column('is_optimized', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('optimization_note', sa.Text(), nullable=True),
        sa.Column('swap_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('prev_task_id', sa.Uuid(), nullable=True),
        sa.Column('diagnosis_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['intent_id'], ['intents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['structure_id'], ['content_structures.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['prev_task_id'], ['content_tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['diagnosis_id'], ['diagnosis_results.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('content_tasks', schema=None) as batch_op:
        batch_op.create_index('ix_content_tasks_user_id', ['user_id'])
        batch_op.create_index('ix_content_tasks_status', ['status'])
    
    # 8. performance_reports
    op.create_table(
        'performance_reports',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('play_count', sa.Integer(), nullable=False),
        sa.Column('comment_count', sa.Integer(), nullable=False),
        sa.Column('message_count', sa.Integer(), nullable=False),
        sa.Column('reported_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['content_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('performance_reports', schema=None) as batch_op:
        batch_op.create_index('ix_performance_reports_task_id', ['task_id'])
        batch_op.create_unique_constraint('uq_performance_reports_task_id', ['task_id'])
    
    # 9. performance_snapshots
    op.create_table(
        'performance_snapshots',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('play_count', sa.Integer(), nullable=False),
        sa.Column('comment_count', sa.Integer(), nullable=False),
        sa.Column('message_count', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False, server_default='manual'),
        sa.Column('snapshot_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['content_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('performance_snapshots', schema=None) as batch_op:
        batch_op.create_index('ix_performance_snapshots_task_id', ['task_id'])
    
    # 10. optimization_rules
    op.create_table(
        'optimization_rules',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('intent_id', sa.Uuid(), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('problem_type', sa.String(length=30), nullable=False),
        sa.Column('condition_expr', sa.JSON(), nullable=False),
        sa.Column('optimization_direction', sa.String(length=100), nullable=False),
        sa.Column('optimization_prompt', sa.Text(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accuracy_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['intent_id'], ['intents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('optimization_rules', schema=None) as batch_op:
        batch_op.create_index('ix_optimization_rules_intent_id', ['intent_id'])
        batch_op.create_index('ix_optimization_rules_problem_type', ['problem_type'])
    
    # 11. market_hots
    op.create_table(
        'market_hots',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('platform_id', sa.Uuid(), nullable=False),
        sa.Column('keyword', sa.String(length=100), nullable=False),
        sa.Column('hot_type', sa.String(length=30), nullable=False),
        sa.Column('analysis_result', sa.JSON(), nullable=True),
        sa.Column('recommended_structures', sa.JSON(), nullable=True),
        sa.Column('priority_boost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('comment_sentiment', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('market_hots', schema=None) as batch_op:
        batch_op.create_index('ix_market_hots_platform_id', ['platform_id'])
    
    # 12. user_events
    op.create_table(
        'user_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('page', sa.String(length=100), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user_events', schema=None) as batch_op:
        batch_op.create_index('ix_user_events_user_id', ['user_id'])
        batch_op.create_index('ix_user_events_session_id', ['session_id'])
        batch_op.create_index('ix_user_events_event_type', ['event_type'])
    
    # 13. extracted_structures
    op.create_table(
        'extracted_structures',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=False),
        sa.Column('platform_id', sa.Uuid(), nullable=False),
        sa.Column('hook_type', sa.String(length=50), nullable=False),
        sa.Column('emotion_structure', sa.JSON(), nullable=False),
        sa.Column('conversion_structure', sa.JSON(), nullable=False),
        sa.Column('key_elements', sa.JSON(), nullable=False),
        sa.Column('viral_score', sa.Integer(), nullable=False),
        sa.Column('analysis_summary', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('extracted_structures', schema=None) as batch_op:
        batch_op.create_index('ix_extracted_structures_platform_id', ['platform_id'])
    
    # 14. conversion_paths
    op.create_table(
        'conversion_paths',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('intent_id', sa.Uuid(), nullable=False),
        sa.Column('stage', sa.String(length=30), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('scripts', sa.JSON(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['intent_id'], ['intents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('conversion_paths', schema=None) as batch_op:
        batch_op.create_index('ix_conversion_paths_intent_id', ['intent_id'])


def downgrade() -> None:
    op.drop_table('conversion_paths')
    op.drop_table('extracted_structures')
    op.drop_table('user_events')
    op.drop_table('market_hots')
    op.drop_table('optimization_rules')
    op.drop_table('performance_snapshots')
    op.drop_table('performance_reports')
    op.drop_table('content_tasks')
    op.drop_table('diagnosis_results')
    op.drop_table('content_structures')
    op.drop_table('user_sessions')
    op.drop_table('users')
    op.drop_table('intents')
    op.drop_table('platforms')
