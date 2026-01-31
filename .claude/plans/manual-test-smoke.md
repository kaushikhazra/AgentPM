# Smoke Test Plan

Quick sanity checks to verify AgentPM is installed and working.

## Prerequisites
```bash
cd C:\Projects\AgentPM
pip install -e .
```

## 1. CLI Starts
```bash
apm --help
```
**Expected**: Shows help with available commands (company, project, node, etc.)

## 2. Database Initializes
```bash
apm company list
```
**Expected**: Empty list or table (no errors about missing tables)

## 3. Create Company
```bash
apm company create "Smoke Test Co"
```
**Expected**: "Created company: Smoke Test Co" with ID displayed

## 4. Create Project
```bash
apm project create <company_id> "Smoke Project"
```
**Expected**: "Created project: Smoke Project"

## 5. Create Task
```bash
apm node create <project_id> task "Smoke Task"
```
**Expected**: "Created task: Smoke Task"

## 6. Dashboard Works
```bash
apm dashboard
```
**Expected**: Dashboard panel displays (may be empty)

## 7. JSON Output Works
```bash
apm --json company list
```
**Expected**: JSON array output (valid JSON)

## 8. MCP Server Starts
```bash
python -m agentpm.mcp --help
```
**Expected**: Shows transport options (stdio, streamable-http)

## 9. MCP HTTP Server Starts
```bash
# Start in background, then Ctrl+C after 2 seconds
timeout 3 python -m agentpm.mcp --transport streamable-http --port 8765
```
**Expected**: Server starts on port 8765 (may show Uvicorn startup message)

## Smoke Test Checklist
- [x] All 9 checks pass without errors
- [x] No stack traces in output
- [x] Database file created at expected location
