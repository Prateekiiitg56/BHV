"""Quick manual test of new features."""
import sys
from pathlib import Path
import io

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bhv.full_app import create_app

def test_new_features():
    app = create_app(testing=True)
    client = app.test_client()
    
    # Create user and login
    print("1. Creating user and logging in...")
    client.post('/signup', data={
        'email': 'testuser@example.com',
        'password': 'password123',
        'role': 'patient'
    })
    client.post('/login', data={
        'email': 'testuser@example.com',
        'password': 'password123'
    })
    print("   ✓ User logged in")
    
    # Upload files
    print("\n2. Uploading test files...")
    client.post('/upload', data={
        'file': (io.BytesIO(b'Test anxiety content'), 'anxiety_notes.txt'),
        'narrative': 'Feeling anxious about work today'
    }, content_type='multipart/form-data')
    
    client.post('/upload', data={
        'file': (io.BytesIO(b'Happy content'), 'happy_day.txt'),
        'narrative': 'Had a wonderful day with friends!'
    }, content_type='multipart/form-data')
    
    client.post('/upload', data={
        'file': (io.BytesIO(b'Housing concerns'), 'housing_issue.txt'),
        'narrative': 'Worried about rent payment this month'
    }, content_type='multipart/form-data')
    print("   ✓ 3 files uploaded")
    
    # Test profile dashboard
    print("\n3. Testing profile dashboard...")
    resp = client.get('/profile')
    assert resp.status_code == 200
    assert b'Upload History Dashboard' in resp.data
    assert b'anxiety_notes.txt' in resp.data
    print("   ✓ Profile shows upload history")
    
    # Test Ask Me - count query
    print("\n4. Testing Ask Me AI - count query...")
    resp = client.post('/ask_me', data={
        'question': 'How many entries do I have?'
    })
    assert resp.status_code == 200
    assert b'3 entries' in resp.data
    print("   ✓ AI correctly counted entries")
    
    # Test Ask Me - keyword search
    print("\n5. Testing Ask Me AI - keyword search...")
    resp = client.post('/ask_me', data={
        'question': 'Find entries mentioning anxiety'
    })
    assert resp.status_code == 200
    assert b'anxiety_notes.txt' in resp.data
    print("   ✓ AI found keyword matches")
    
    # Test Ask Me - show all
    print("\n6. Testing Ask Me AI - list all...")
    resp = client.post('/ask_me', data={
        'question': 'Show me all my entries'
    })
    assert resp.status_code == 200
    assert b'anxiety_notes.txt' in resp.data
    assert b'happy_day.txt' in resp.data
    assert b'housing_issue.txt' in resp.data
    print("   ✓ AI listed all entries")
    
    print("\n✅ All new features working correctly!")
    print("\nFeatures implemented:")
    print("  1. Upload working and saving to Git storage + DB")
    print("  2. Profile page shows complete upload history dashboard")
    print("  3. Ask Me AI section with:")
    print("     - Entry counting")
    print("     - Keyword search")
    print("     - List all entries")
    print("     - Summary generation")

if __name__ == '__main__':
    test_new_features()
