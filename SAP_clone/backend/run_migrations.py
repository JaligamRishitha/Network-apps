"""
Run database migrations
"""
import subprocess
import sys
import os

# Change to backend directory where alembic.ini is located
os.chdir('/app/backend')

# Run alembic upgrade
result = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)

sys.exit(result.returncode)
