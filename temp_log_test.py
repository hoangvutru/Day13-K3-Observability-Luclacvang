from pathlib import Path
from fastapi.testclient import TestClient
import os
from app.main import app

os.environ['LOG_PATH'] = 'data/logs_test_run.jsonl'
log_path = Path('data/logs_test_run.jsonl')
if log_path.exists():
    log_path.unlink()

with TestClient(app) as client:
    for payload in [
        {'user_id':'user1','session_id':'s1','feature':'qa','message':'What is observability?'},
        {'user_id':'user2','session_id':'s2','feature':'summary','message':'Summarize the policy.'},
        {'user_id':'user3','session_id':'s3','feature':'qa','message':'Explain prompt versioning.'},
    ]:
        r = client.post('/chat', json=payload)
        print(r.status_code, r.json().get('correlation_id'))

print('readlog', log_path.exists())
print(log_path.read_text(encoding='utf-8'))
