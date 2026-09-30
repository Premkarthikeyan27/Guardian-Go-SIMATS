import uvicorn
import os
import sys

# Ensure backend package can be imported from root directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("==================================================")
    print("  GUARDIAN GO - Caregiver & Family Care Platform  ")
    print("  Tagline: Verified care. Connected safety. Peace of mind.")
    print("==================================================")
    print("Starting FastAPI server at http://127.0.0.1:8000")
    print("  - Landing / Login:    http://127.0.0.1:8000/")
    print("  - Parent Portal:       http://127.0.0.1:8000/portals/user/")
    print("  - Guardian Portal:     http://127.0.0.1:8000/portals/guardian/")
    print("  - Admin Portal:        http://127.0.0.1:8000/portals/admin/")
    print("==================================================")
    
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
