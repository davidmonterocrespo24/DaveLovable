# Integration Test Plan

Complete testing guide for frontend-backend integration.

## Prerequisites

1. Backend running on http://localhost:8000
2. Frontend running on http://localhost:8080
3. OPENAI_API_KEY configured in backend/.env
4. Test user created (ID: 1, email: demo@lovable.dev)

## Manual Integration Tests

### Test 1: Backend Health Check

**Steps:**
1. Open browser to http://localhost:8000/docs
2. Verify Swagger UI loads

**Expected:**
- API documentation displays correctly
- All endpoints are listed

**Status:** ☐ Pass ☐ Fail

---

### Test 2: Create Project via API

**Steps:**
```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Integration Test Project", "description": "Testing integration"}'
```

**Expected:**
- Returns 200 status
- Response includes project `id`, `name`, `files` array
- Initial files (App.tsx, main.tsx, etc.) are created

**Status:** ☐ Pass ☐ Fail

---

### Test 3: Access Editor with Project

**Steps:**
1. Note the project ID from Test 2 (e.g., 1)
2. Open browser to http://localhost:8080/editor/1
3. Wait for page to load

**Expected:**
- No errors in browser console
- Project name displays in header
- File explorer shows project files
- First file loads in code editor
- Chat panel is visible

**Status:** ☐ Pass ☐ Fail

---

### Test 4: File Explorer Interaction

**Steps:**
1. In editor, click different files in file explorer
2. Expand/collapse folders
3. Use search to filter files

**Expected:**
- Files load correctly when clicked
- Code editor updates with file content
- Tabs open for each file
- Search filters files correctly
- Folder expand/collapse works

**Status:** ☐ Pass ☐ Fail

---

### Test 5: Send Chat Message (Simple)

**Steps:**
1. In chat panel, type: "Add a comment to App.tsx"
2. Press Enter or click Send
3. Wait for AI response

**Expected:**
- Message appears in chat
- "Generating code..." indicator shows
- AI responds within 30 seconds
- Response appears in chat
- If code was modified, files refresh

**Status:** ☐ Pass ☐ Fail

---

### Test 6: Send Chat Message (Code Generation)

**Steps:**
1. In chat panel, type: "Create a Button component with primary and secondary variants"
2. Wait for AI response

**Expected:**
- AI processes request
- Multiple agents collaborate (visible in backend logs)
- New Button.tsx file appears in file explorer
- File contains proper TypeScript/React code
- Code includes the requested variants

**Status:** ☐ Pass ☐ Fail

---

### Test 7: File Content Updates

**Steps:**
1. Open a file (e.g., App.tsx)
2. Send chat message: "Add a header to the App component"
3. Watch file explorer and code editor

**Expected:**
- File explorer refreshes automatically
- If viewing modified file, content updates
- Changes are persisted to database

**Status:** ☐ Pass ☐ Fail

---

### Test 8: Multiple Tabs

**Steps:**
1. Open 3-4 different files
2. Verify tabs appear
3. Switch between tabs
4. Close tabs

**Expected:**
- Tabs open for each file
- Active tab is highlighted
- Switching tabs updates code editor
- Closing tabs works correctly
- Can't close last tab

**Status:** ☐ Pass ☐ Fail

---

### Test 9: Chat Session Persistence

**Steps:**
1. Send several chat messages
2. Refresh the page
3. Check if messages are restored

**Expected:**
- Messages persist across refreshes
- Session continues correctly

**Status:** ☐ Pass ☐ Fail

---

### Test 10: Error Handling

**Steps:**
1. Stop backend server
2. Try to send chat message
3. Try to click on files
4. Restart backend
5. Try operations again

**Expected:**
- Graceful error messages
- No crashes
- App recovers when backend restarts

**Status:** ☐ Pass ☐ Fail

---

## Automated Backend Tests

Run with: `pytest backend/tests/test_api.py -v`

### Expected Results

```
test_api.py::TestProjectAPI::test_create_project PASSED
test_api.py::TestProjectAPI::test_list_projects PASSED
test_api.py::TestProjectAPI::test_get_project PASSED
test_api.py::TestProjectAPI::test_update_project PASSED
test_api.py::TestProjectAPI::test_delete_project PASSED
test_api.py::TestFileAPI::test_create_file PASSED
test_api.py::TestFileAPI::test_list_files PASSED
test_api.py::TestFileAPI::test_update_file PASSED
test_api.py::TestFileAPI::test_delete_file PASSED
test_api.py::TestChatAPI::test_send_message PASSED or SKIPPED
test_api.py::TestChatAPI::test_list_sessions PASSED
test_api.py::TestHealthCheck::test_root_endpoint PASSED
test_api.py::TestHealthCheck::test_docs_available PASSED
test_api.py::TestHealthCheck::test_openapi_spec PASSED
```

**Status:** ☐ Pass ☐ Fail

---

## Performance Tests

### Test 11: Large Project Load Time

**Steps:**
1. Create project with 50+ files
2. Open in editor
3. Measure load time

**Expected:**
- Loads in < 3 seconds
- UI remains responsive

**Status:** ☐ Pass ☐ Fail

---

### Test 12: Chat Response Time

**Steps:**
1. Send 5 different chat messages
2. Measure response times

**Expected:**
- Average response < 15 seconds
- No timeouts
- Consistent performance

**Status:** ☐ Pass ☐ Fail

---

## Browser Compatibility

Test in:
- ☐ Chrome
- ☐ Firefox
- ☐ Safari
- ☐ Edge

---

## Common Issues and Solutions

### Issue: CORS Error

**Symptoms:** Console shows "CORS policy" errors

**Solution:**
1. Check backend CORS settings in `backend/app/main.py`
2. Ensure http://localhost:8080 is in allowed origins
3. Restart backend

### Issue: Files Not Loading

**Symptoms:** File explorer empty or files don't load

**Solution:**
1. Check browser console for errors
2. Verify project ID in URL is correct
3. Verify project has files: `curl http://localhost:8000/api/v1/projects/1`

### Issue: Chat Not Working

**Symptoms:** Messages sent but no response

**Solution:**
1. Check OPENAI_API_KEY in backend/.env
2. Check backend logs for errors
3. Verify OpenAI API has credits

### Issue: Backend Connection Failed

**Symptoms:** "Failed to fetch" or "Network error"

**Solution:**
1. Verify backend is running: `curl http://localhost:8000`
2. Check VITE_API_URL in frontend/.env
3. Ensure no firewall blocking requests

---

## Test Results Summary

**Date:** __________
**Tester:** __________
**Environment:** __________

| Test | Status | Notes |
|------|--------|-------|
| Backend Health | ☐ | |
| Create Project | ☐ | |
| Access Editor | ☐ | |
| File Explorer | ☐ | |
| Chat Simple | ☐ | |
| Chat Code Gen | ☐ | |
| File Updates | ☐ | |
| Multiple Tabs | ☐ | |
| Session Persist | ☐ | |
| Error Handling | ☐ | |
| Large Project | ☐ | |
| Chat Performance | ☐ | |
| Automated Tests | ☐ | |

**Overall Status:** ☐ Pass ☐ Fail

**Critical Issues:**

**Minor Issues:**

**Recommendations:**
