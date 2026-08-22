#\!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Try alternative DNS approach
os.environ['RES_OPTIONS'] = 'inet6'

import psycopg2

load_dotenv('backend/.env')
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'), connect_timeout=10)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM properties LIMIT 1')
    count = cur.fetchone()[0]
    print(f'✅ Connected\! {count:,} properties')
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f'❌ Failed: {e}')
    sys.exit(1)
