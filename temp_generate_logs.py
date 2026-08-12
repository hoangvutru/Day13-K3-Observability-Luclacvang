from pathlib import Path
from fastapi.testclient import TestClient
import os
from app.main import app

os.environ['LOG_PATH'] = 'data/logs.jsonl'
log_path = Path('data/logs.jsonl')
if log_path.exists():
    log_path.unlink()
log_path.parent.mkdir(parents=True, exist_ok=True)

with TestClient(app) as client:
    payloads = [
        {'user_id': 'user1', 'session_id': 's1', 'feature': 'qa', 'message': 'What is observability?'},
        {'user_id': 'user2', 'session_id': 's2', 'feature': 'summary', 'message': 'Summarize the policy.'},
        {'user_id': 'user3', 'session_id': 's3', 'feature': 'qa', 'message': 'Explain prompt versioning.'},
        {'user_id': 'user4', 'session_id': 's4', 'feature': 'qa', 'message': 'How do latency and traces relate?'},
        {'user_id': 'user5', 'session_id': 's5', 'feature': 'qa', 'message': 'What is proper logging context?'},
        {'user_id': 'user6', 'session_id': 's6', 'feature': 'summary', 'message': 'Summarize the alert design guidance.'},
        {'user_id': 'user7', 'session_id': 's7', 'feature': 'qa', 'message': 'Why redact PII in logs?'},
        {'user_id': 'user8', 'session_id': 's8', 'feature': 'qa', 'message': 'Explain prompt label and version.'},
        {'user_id': 'user9', 'session_id': 's9', 'feature': 'qa', 'message': 'What evidence do we need for dashboard?'},
        {'user_id': 'user10', 'session_id': 's10', 'feature': 'summary', 'message': 'Summarize how to use Langfuse traces.'},
    ]
    for payload in payloads:
        r = client.post('/chat', json=payload)
        print(r.status_code, r.json().get('correlation_id'))

print('readlog', log_path.exists())
if log_path.exists():
    print(log_path.read_text(encoding='utf-8'))
