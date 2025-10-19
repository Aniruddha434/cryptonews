"""
Migrations package for AI Market Insight Bot.

This package resolves the naming conflict between migrations.py file and migrations/ directory.
We import and re-export the functions from database_migrations.py (renamed from migrations.py).
"""

# Import from database_migrations.py (the renamed migrations.py file)
from database_migrations import run_all_migrations, MigrationManager

__all__ = ['run_all_migrations', 'MigrationManager']

