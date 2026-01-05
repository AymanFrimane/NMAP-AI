# NMAP-AI API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### POST /api/validate
Validate nmap command for syntax, conflicts, and safety.

**Request:**
```json
{
  "command": "nmap -sV -p 80,443 192.168.1.1"
}
```

**Response:**
```json
{
  "valid": true,
  "score": 1.0,
  "errors": [],
  "warnings": ["Version detection increases scan time"],
  "details": {
    "syntax": {"valid": true, "message": "Syntax valid"},
    "conflicts": {"valid": true, "message": "No conflicts detected"},
    "safety": {"valid": true, "errors": [], "warnings": []},
    "root": {"required": false, "flags": []}
  }
}
```

### Examples

#### Test valid command:
```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"command":"nmap -sV -p 80,443 192.168.1.1"}'
```

#### Test conflict detection:
```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"command":"nmap -sS -sT 192.168.1.1"}'
```

#### Test unsafe command:
```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"command":"nmap 192.168.1.1 > output.txt"}'
```

## Interactive Documentation
Visit Swagger UI at: http://localhost:8000/docs

## Error Responses

### Validation Failed (400)
```json
{
  "valid": false,
  "score": 0.3,
  "errors": ["Conflict: -sS conflicts with -sT"],
  "warnings": ["Requires root privileges for: -sS"]
}
```

### Service Error (500)
```json
{
  "detail": "Validation service unavailable"
}
```
