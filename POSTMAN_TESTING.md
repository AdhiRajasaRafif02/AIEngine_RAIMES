# SERVER SETUP & TESTING GUIDE

## Quick Start: Run Server Locally

```powershell
cd 'C:\Users\Adhi Rajasa Rafif\OneDrive\Documents\Kuliah\RPL_Kelas\AI_Engine\AIEngine_RAIMES'
.\run-server.ps1
```

**Note:** If you get a PowerShell execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

The `run-server.ps1` script will:
- Check if port 8000 is in use
- Kill any process using port 8000 (safe — only affects that port)
- Wait for the port to become available
- Activate the virtual environment
- Start Uvicorn server on `http://127.0.0.1:8000`

---

## Testing with Postman

### Import Collection

1. Open Postman
2. **Import** → **File** → Select `postman_collection.json` from the repo root
3. Set environment variable:
   - **New Environment** (or edit existing)
   - Variable: `base_url`
   - Initial Value: `http://127.0.0.1:8000`

### Test Endpoints

#### 1. POST a Review

- **Request:** POST {{base_url}}/reviews
- **Headers:** Content-Type: application/json
- **Body (raw JSON):**
```json
{
  "author": "Alice",
  "text": "This is a test review",
  "rating": 5
}
```
- **Expected:** Status 201 Created + JSON response with id, author, text, rating, created_at

#### 2. GET All Reviews

- **Request:** GET {{base_url}}/reviews
- **Expected:** Status 200 OK + JSON array including the posted review

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `[Errno 10048]` - Port in use | Run `.\run-server.ps1` — it handles this automatically |
| Server won't start | Check firewall; try port 9000: `uvicorn main:app --port 9000` |
| 422 Unprocessable Entity | Verify JSON body has `author` and `text` (required fields) |
| GET returns empty array | Ensure server didn't restart between POST and GET (in-memory store) |
| Postman can't connect | Confirm server is running and shows "Uvicorn running on..." in terminal |

---

## Manual Alternative (without script)

If you prefer to start without the script:

```powershell
# Check if port 8000 is in use
netstat -aon | findstr :8000

# If in use, find and kill the process (replace 12345 with actual PID)
taskkill /PID 12345 /F

# Then start the server
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

---

## Endpoints Reference

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| POST | /reviews | {author, text, rating?} | 201 + Review JSON |
| GET | /reviews | — | 200 + Review[] JSON |
| GET | /health | — | 200 + {status: "ok"} |
| GET | /items/{id} | — | 200 + {id, name} |

---

## Next Steps

- Run the server using `.\run-server.ps1`
- Import `postman_collection.json` into Postman
- POST a review and confirm 201 response
- GET /reviews and confirm the posted review appears
- Use Postman Tests tab to validate assertions (included in collection)
