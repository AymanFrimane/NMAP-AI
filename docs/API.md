# NMAP-AI API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### GET /
API information and available endpoints

**Response:**
```json
{
  "status": "online",
  "message": "NMAP-AI API is running",
  "version": "1.0.0",
  "endpoints": {
    "docs": "/docs",
    "health": "/health",
    "validate": "/api/validate",
    "generate": "/api/generate"
  }
}
```

---

### GET /health
Health check endpoint

**Response:**
```json
{
  "status": "healthy"
}
```

---

### POST /api/validate
Validate an nmap command

**Request:**
```json
{
  "command": "nmap -sV -p 80,443 192.168.1.1"
}
```

**Response (Valid):**
```json
{
  "valid": true,
  "is_valid": true,
  "score": 1.0,
  "feedback": "Valid command with 1 warning(s)",
  "errors": [],
  "warnings": ["Version detection increases scan time"],
  "details": {
    "syntax": {
      "valid": true,
      "message": "Syntax valid"
    },
    "conflicts": {
      "valid": true,
      "message": "No conflicts detected"
    },
    "safety": {
      "valid": true,
      "errors": [],
      "warnings": ["Version detection increases scan time"]
    },
    "root": {
      "required": false,
      "flags": []
    }
  }
}
```

**Response (Invalid - Conflict):**
```json
{
  "valid": false,
  "is_valid": false,
  "score": 0.3,
  "feedback": "Command has 2 error(s)",
  "errors": [
    "Syntax: No target specified",
    "Conflict: -sS conflicts with -sT (cannot use multiple scan types)"
  ],
  "warnings": ["Requires root privileges for: -sS"],
  "details": {
    "syntax": {
      "valid": false,
      "message": "No target specified"
    },
    "conflicts": {
      "valid": false,
      "message": "Conflict detected: -sS conflicts with -sT"
    },
    "safety": {
      "valid": true,
      "errors": [],
      "warnings": []
    },
    "root": {
      "required": true,
      "flags": ["-sS"]
    }
  }
}
```

---

### POST /api/generate
Generate nmap command from natural language (STUB)

**Request:**
```json
{
  "query": "Scan web servers with version detection on 192.168.1.0/24"
}
```

**Response:**
```json
{
  "command": "nmap -sV -p 80,443 192.168.1.0/24",
  "confidence": 0.92,
  "explanation": "This command scans for web servers and detects versions",
  "validation": {
    "valid": true,
    "score": 0.95,
    "errors": [],
    "warnings": ["Version detection increases scan time"]
  },
  "metadata": {
    "complexity": "MEDIUM",
    "attempts": 1,
    "stub": true
  }
}
```

---

### GET /api/status
Service status check

**Response:**
```json
{
  "validator": {
    "available": true,
    "status": "online",
    "message": "Validator ready"
  },
  "generator": {
    "available": false,
    "status": "stub",
    "message": "Using stub implementation"
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request format"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Validation failed: [error message]"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Validation service unavailable"
}
```

---

## Validation Details

### Syntax Check
- Verifies command starts with 'nmap'
- Validates target format (IP, CIDR, domain)
- Checks flag syntax

### Conflict Detection
- Detects scan type conflicts (-sS vs -sT)
- Detects special conflicts (-sn vs -p)
- Uses fallback rules or Knowledge Graph

### Safety Check
- Blocks file redirection (>)
- Blocks command chaining (;, &&, ||)
- Blocks command injection ($(), `)
- Blocks pipes (|)

### Root Detection
- Identifies flags requiring sudo
- Lists specific flags needing root

---

## Score Calculation

Score ranges from 0.0 to 1.0:
- **1.0**: Perfect command, no issues
- **0.7-0.9**: Valid with warnings
- **0.3-0.6**: Invalid with recoverable errors
- **0.0-0.2**: Severe issues (unsafe, multiple errors)

---

## Examples

### Valid Command
```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"command":"nmap -sV -p 80,443 192.168.1.1"}'
```

### Invalid Syntax
```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"command":"scan 192.168.1.1"}'
```

### Conflict Detection
```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"command":"nmap -sS -sT 192.168.1.1"}'
```

### Unsafe Pattern
```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"command":"nmap 192.168.1.1 > output.txt"}'
```

---

## Interactive Documentation

Access Swagger UI at: http://localhost:8000/docs
