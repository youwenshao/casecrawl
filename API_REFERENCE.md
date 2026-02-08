# CaseCrawl API Reference

## Base URL
```
http://localhost:8000/api/v1
```

## WebSocket
```
ws://localhost:8000/ws/batch-progress
```

## Endpoints

### Batches

#### Upload Cases
```http
POST /batches
Content-Type: multipart/form-data
```

**Parameters:**
- `file` (required): CSV or Excel file with columns: `party_name`, `citation`, `notes`
- `auto_download_exact_matches` (optional, default: true): Auto-download exact matches
- `user_id` (optional): User identifier

**Response:**
```json
{
  "batch_id": "uuid",
  "total_cases": 10,
  "message": "Batch created successfully"
}
```

#### Get Batch
```http
GET /batches/{batch_id}
```

#### Get Batch Statistics
```http
GET /batches/{batch_id}/statistics
```

**Response:**
```json
{
  "batch_id": "uuid",
  "status": "processing",
  "total_cases": 10,
  "completed": 5,
  "pending": 3,
  "errors": 0,
  "ambiguous": 1,
  "civil_procedure_blocked": 1,
  "awaiting_selection": 0,
  "progress_percentage": 50.0
}
```

#### List Cases in Batch
```http
GET /batches/{batch_id}/cases?status=&confidence=&skip=0&limit=100
```

### Cases

#### Get Case
```http
GET /cases/{case_id}
```

#### Get Search Results (Disambiguation)
```http
GET /cases/{case_id}/search-results
```

**Response:**
```json
{
  "case_id": "uuid",
  "party_names_raw": "Smith v Jones",
  "citation_raw": "[2020] HKCFI 123",
  "results": [
    {
      "id": "uuid",
      "westlaw_citation": "[2020] HKCFI 123",
      "where_reported": ["[2020] 1 HKLRD 100"],
      "principal_subject": "Contract Law",
      "is_civil_procedure": false,
      "parties_display": "Smith v Jones",
      "year": 2020,
      "available_documents": {
        "pdf": true,
        "transcript": false,
        "analysis": true
      },
      "citation_match_type": "exact",
      "similarity_score": 1.0
    }
  ],
  "has_exact_match": true,
  "has_civil_procedure": false
}
```

#### Select Result
```http
POST /cases/{case_id}/select
Content-Type: application/json

{
  "result_id": "uuid",
  "override_civil_procedure": false
}
```

#### Force Manual Review
```http
POST /cases/{case_id}/force-manual
Content-Type: application/json

{
  "reason": "Civil Procedure case"
}
```

#### Download Case
```http
GET /cases/{case_id}/download
```

### Sessions

#### Create Session (Login)
```http
POST /sessions
Content-Type: application/json

{
  "username": "string",
  "password": "string",
  "totp_code": "123456"
}
```

#### Check Session Health
```http
GET /sessions/{session_id}/health
```

## WebSocket Events

### Client → Server
```json
{"type": "subscribe", "batch_id": "uuid"}
{"type": "ping"}
```

### Server → Client
```json
// Connected
{"type": "connected", "message": "..."}

// Case completed
{
  "type": "case_completed",
  "case_id": "uuid",
  "batch_id": "uuid",
  "file_name": "case.pdf",
  "timestamp": "2024-01-01T00:00:00Z"
}

// Case error
{
  "type": "case_error",
  "case_id": "uuid",
  "batch_id": "uuid",
  "error": "Error message",
  "timestamp": "2024-01-01T00:00:00Z"
}

// Civil procedure detected
{
  "type": "civil_procedure_detected",
  "case_id": "uuid",
  "batch_id": "uuid",
  "citation": "[2020] HKCFI 123",
  "timestamp": "2024-01-01T00:00:00Z"
}

// Ambiguous results
{
  "type": "ambiguous_requires_selection",
  "case_id": "uuid",
  "batch_id": "uuid",
  "results_count": 3,
  "timestamp": "2024-01-01T00:00:00Z"
}

// Batch complete
{
  "type": "batch_complete",
  "batch_id": "uuid",
  "statistics": {...},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Status Codes

### Batch Status
- `pending`: Waiting to start
- `processing`: Currently processing
- `completed`: All cases finished
- `failed`: Batch failed
- `paused`: Manually paused

### Case Status
- `pending`: Not yet processed
- `searching`: Currently searching
- `ambiguous`: Multiple matches found
- `awaiting_selection`: Human selection needed
- `civil_procedure_blocked`: Civil procedure detected
- `citation_mismatch`: Citation doesn't match
- `analysis_only`: Only analysis available
- `downloading`: Download in progress
- `completed`: Successfully downloaded
- `error`: Processing failed
