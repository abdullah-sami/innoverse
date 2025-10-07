# Innoverse API Documentation

Complete API documentation for the Innoverse event management system.

## Base URL

```bash
http://ekhonodeinai.com
```

---

## Authentication

The API uses JWT (JSON Web Token) authentication for protected endpoints.

### 1. Login

**Endpoint:** `POST /login/`

**Description:** Authenticate user and receive JWT tokens

**Request Body:**
```bash
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```bash
{
  "access": "string",
  "refresh": "string"
    "user": {
            "id": int,
            "username": "string",
            "email": "string",
			"role": "string" // only allow if role == admin
        }
},
```

---

### 2. Token Obtain Pair

**Endpoint:** `POST /auth/token`

**Description:** Obtain JWT access and refresh tokens

**Request Body:**
```bash
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```bash
{
  "access": "string",
  "refresh": "string"
}
```

---

### 3. Token Refresh

**Endpoint:** `POST /auth/token/refresh`

**Description:** Refresh JWT access token

**Request Body:**
```bash
{
  "refresh": "string"
}
```

**Response:**
```bash
{
  "access": "string"
}
```

---

### 4. Logout

**Endpoint:** `POST /logout/`

**Description:** Logout user

**Authentication:** Required

---

## Public Endpoints

### 5. Registration

**Endpoint:** `POST /api/register/`

**Content-type:** `application/json`

**Description:** Register a new participant / team

**Authentication:** Not required

**Request Body:**
```bash
{
  "participant": {
    "full_name": "John Doe",
    "gender": "M",
    "email": "john@example.com",
    "phone": "1234567890",
    "age": 22,
    "institution": "Example University",
    "institution_id": "EU12345",
    "address": "123 Main St",
    "t_shirt_size": "L",
    "club_reference": "Tech Club",
    "campus_ambassador": "Jane Smith"
  },
  "payment": {
    "amount": "500.00",
    "phone": "1234567890",
    "trx_id": "TRX123456789"
  },
  "segment": ["expo"],
  "competition": ["m_auction", "res_abs"],
  "team_competition": {
    "team": {
      "team_name": "Team Alpha",
      "participant": [
        {
          "full_name": "Alice Johnson",
          "gender": "F",
          "email": "alice@example.com",
          "phone": "9876543210",
          "age": 21,
          "institution": "Example University",
          "institution_id": "EU54321",
          "address": "456 Elm St",
          "t_shirt_size": "M",
          "club_reference": "Tech Club",
          "campus_ambassador": "Jane Smith"
        }
      ]
    },
    "competition": ["pr_show"]
  }
}
```

segment and competition code:
```bash
Segments:
    Innovation Expo : expo
	Sketch Talk : sktech
	Policy Bridge Dialogue : policy

Competitions:
    Math Auction : m_auction
	3-Minute Research : 3m-res
	Research Abstract : res_abs
	Science Olympiad : sc_olym
	Programming Contest : programming
Team Competitions:
    Project Showcasing : pr_show
	Science Quiz : sc_quiz
	Robo Soccer : robo_soc
```

**Response:**
```bash
{
  "success": true,
  "message": "Registration completed successfully",
  "data": {
    "participant": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "payment_verified": false
    },
    "payment": {
      "trx_id": "TRX123456789",
      "amount": "500.00"
    },
    "segments": ["expo"],
    "competitions": ["m_auction", "res_abs"],
    "team": {
      "id": 1,
      "name": "Team Alpha",
      "payment_verified": false,
      "members_count": 2,
      "competitions": ["pr_show"]
    },
    "team_payment": {
      "trx_id": "TRX123456789",
      "amount": "500.00"
    }
  }
}
```

**Error Response:**
```bash
{
  "success": false,
  "errors": {
    "field_name": ["error message"]
  }
}
```

---

## Admin Dashboard Endpoints

All admin endpoints require authentication with admin volunteer role.

### 6. List Participants

**Endpoint:** `GET /api/participant/`

**Description:** Get list of all participants with filtering options

**Authentication:** Required (Admin Volunteer)

**Query Parameters:**
- `segment` (optional): Filter by segment code
- `competition` (optional): Filter by competition code
- `payment_verified` (optional): Filter by payment status (true/false)
- `search` (optional): Search by name or email

**Example:**
```bash
GET /api/participant/?segment=SEG01&payment_verified=true&search=john
```

**Response:**
```bash
{
  "success": true,
  "count": 10,
  "data": [
    {
      "id": 1,
      "full_name": "John Doe",
      "email": "john@example.com",
      "phone": "1234567890",
      "institution": "Example University",
      "payment_verified": true,
      "segments": ["Segment 1", "Segment 2"],
      "competitions": ["Competition 1"],
      "has_entry": true
    }
  ]
}
```

---

### 7. Get Participant Details

**Endpoint:** `GET /api/participant/{id}/`

**Description:** Get detailed information about a specific participant

**Authentication:** Required (Admin Volunteer)

**Response:**
```bash
{
  "success": true,
  "data": {
    "id": 1,
    "f_name": "John",
    "l_name": "Doe",
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890",
    "age": 22,
    "institution": "Example University",
    "institution_id": "EU12345",
    "address": "123 Main St",
    "payment_verified": true,
    "segment_registrations": [
      {
        "segment_name": "Segment 1",
        "segment_code": "SEG01",
        "datetime": "2025-01-15T10:30:00Z"
      }
    ],
    "competition_registrations": [
      {
        "competition_name": "Competition 1",
        "competition_code": "COMP01",
        "datetime": "2025-01-15T10:30:00Z"
      }
    ],
    "gifts_received": [
      {
        "gift_name": "T-Shirt",
        "received_at": "2025-01-16T14:20:00Z",
        "volunteer": "Volunteer Name"
      }
    ],
    "payments": [
      {
        "id": 1,
        "phone": "1234567890",
        "amount": "500.00",
        "trx_id": "TRX123456789",
        "datetime": "2025-01-15T10:30:00Z"
      }
    ],
    "has_entry": true,
    "entry_datetime": "2025-01-16T09:00:00Z",
    "team_info": {
      "id": 1,
      "team_name": "Team Alpha",
      "payment_verified": true
    }
  }
}
```

---

### 8. List Teams

**Endpoint:** `GET /api/team/`

**Description:** Get list of all teams with filtering options

**Authentication:** Required (Admin Volunteer)

**Query Parameters:**
- `competition` (optional): Filter by competition code
- `payment_verified` (optional): Filter by payment status (true/false)

**Example:**
```bash
GET /api/team/?competition=TCOMP01&payment_verified=true
```

**Response:**
```bash
{
  "success": true,
  "count": 5,
  "data": [
    {
      "id": 1,
      "team_name": "Team Alpha",
      "payment_verified": true,
      "member_count": 3,
      "members": [
        {
          "id": 1,
          "f_name": "John",
          "l_name": "Doe",
          "full_name": "John Doe",
          "email": "john@example.com",
          "phone": "1234567890",
          "age": 22,
          "institution": "Example University",
          "institution_id": "EU12345",
          "is_leader": true
        }
      ],
      "competition_registrations": [
        {
          "competition_name": "Team Competition 1",
          "competition_code": "TCOMP01",
          "datetime": "2025-01-15T10:30:00Z"
        }
      ],
      "gifts_received": [
        {
          "gift_name": "Trophy",
          "received_at": "2025-01-16T14:20:00Z",
          "volunteer": "Volunteer Name"
        }
      ],
      "payments": [
        {
          "id": 1,
          "phone": "1234567890",
          "amount": "1000.00",
          "trx_id": "TRX987654321",
          "datetime": "2025-01-15T10:30:00Z"
        }
      ],
      "has_entry": true,
      "entry_datetime": "2025-01-16T09:00:00Z"
    }
  ]
}
```

---

### 9. Get Segment Details

**Endpoint:** `GET /api/segment/{code}/`

**Description:** Get segment details with participant list

**Authentication:** Required (Admin Volunteer)

**Response:**
```bash
{
  "success": true,
  "segment": {
    "id": 1,
    "segment_name": "Segment 1",
    "code": "SEG01"
  },
  "participant_count": 25,
  "participants": [
    {
      "id": 1,
      "full_name": "John Doe",
      "email": "john@example.com",
      "phone": "1234567890",
      "institution": "Example University",
      "payment_verified": true,
      "segments": ["Segment 1"],
      "competitions": ["Competition 1"],
      "has_entry": true
    }
  ]
}
```

---

### 10. Get Competition Details

**Endpoint:** `GET /api/competition/{code}/`

**Description:** Get competition details with participant list

**Authentication:** Required (Admin Volunteer)

**Response:**
```bash
{
  "success": true,
  "competition": {
    "id": 1,
    "competition": "Competition 1",
    "code": "COMP01"
  },
  "participant_count": 15,
  "participants": [
    {
      "id": 1,
      "full_name": "John Doe",
      "email": "john@example.com",
      "phone": "1234567890",
      "institution": "Example University",
      "payment_verified": true,
      "segments": ["Segment 1"],
      "competitions": ["Competition 1"],
      "has_entry": true
    }
  ]
}
```

---

### 11. Get Team Competition Details

**Endpoint:** `GET /api/team-competition/{code}/`

**Description:** Get team competition details with team list

**Authentication:** Required (Admin Volunteer)

**Response:**
```bash
{
  "success": true,
  "competition": {
    "id": 1,
    "competition": "Team Competition 1",
    "code": "TCOMP01"
  },
  "team_count": 8,
  "teams": [
    {
      "id": 1,
      "team_name": "Team Alpha",
      "payment_verified": true,
      "member_count": 3,
      "members": [...],
      "competition_registrations": [...],
      "gifts_received": [...],
      "payments": [...],
      "has_entry": true,
      "entry_datetime": "2025-01-16T09:00:00Z"
    }
  ]
}
```

---

### 12. Verify Payment

**Endpoint:** `POST /api/payment/verify/`

**Description:** Toggle payment verification status for a participant

**Authentication:** Required (Admin Volunteer)

**Request Body:**
```bash
{
  "id": 1
}
```

**Response:**
```bash
{
  "success": true,
  "message": "Payment verified for John Doe and team Team Alpha",
  "data": {
    "participant": {
      "id": 1,
      "name": "John Doe",
      "payment_verified": true
    },
    "team": {
      "id": 1,
      "name": "Team Alpha",
      "payment_verified": true
    }
  }
}
```

---

## Volunteer App Endpoints

### 13. Record Entry

**Endpoint:** `GET /api/recordentry/{id}/`

**Description:** Check if entry has been recorded

**Authentication:** Required (Volunteer)

**Parameters:**
- `id`: Participant ID (format: `p_{id}`) or Team ID (format: `t_{id}`)

**Example:**
```bash
GET /api/recordentry/p_1/
GET /api/recordentry/t_1/
```

**Response:**
```bash
{
  "success": true
}
```

**Error Response:**
```bash
{
  "success": false
}
```

---

### 14. Create Entry Record

**Endpoint:** `POST /api/recordentry/{id}/`

**Description:** Record entry for a participant or team

**Authentication:** Required (Volunteer)

**Parameters:**
- `id`: Participant ID (format: `p_{id}`) or Team ID (format: `t_{id}`)

**Example:**
```bash
POST /api/recordentry/p_1/
POST /api/recordentry/t_1/
```

**Response:**
```bash
{
  "success": true,
  "data": {
    "p_name": "John Doe",
    "t_name": null
  }
}
```

**Error Response:**
```bash
{
  "success": false,
  "error": "Already recorded entry"
}
```

---

### 15. Get Gift Status

**Endpoint:** `GET /api/gifts/{id}/`

**Description:** Get gift distribution status for participant or team

**Authentication:** Required (Volunteer)

**Parameters:**
- `id`: Participant ID (format: `p_{id}`) or Team ID (format: `t_{id}`)

**Example:**
```bash
GET /api/gifts/p_1/
GET /api/gifts/t_1/
```

**Response:**
```bash
{
  "t-shirt": 1,
  "badge": 0,
  "certificate": 1,
  "trophy": 0
}
```

---

### 16. Mark Gift as Received

**Endpoint:** `POST /api/gifts/{id}/`

**Description:** Mark a gift as received by participant or team

**Authentication:** Required (Volunteer)

**Parameters:**
- `id`: Participant ID (format: `p_{id}`) or Team ID (format: `t_{id}`)

**Request Body:**
```bash
{
  "gift_name": "T-Shirt"
}
```

**Response:**
```bash
{
  "message": "T-Shirt marked as received successfully"
}
```

**Error Response:**
```bash
{
  "message": "T-Shirt already marked as received"
}
```

---

### 17. Get Participant/Team Info

**Endpoint:** `GET /api/info/{id}/`

**Description:** Get detailed information about participant and associated team

**Authentication:** Required (Volunteer)

**Parameters:**
- `id`: Participant ID (format: `p_{id}`) or Team ID (format: `t_{id}`)

**Example:**
```bash
GET /api/info/p_1/
GET /api/info/t_1/
```

**Response (Participant):**
```bash
{
  "participant": {
    "id": 1,
    "f_name": "John",
    "l_name": "Doe",
    "email": "john@example.com",
    "phone": "1234567890",
    "age": 22,
    "institution": "Example University",
    "institution_id": "EU12345",
    "address": "123 Main St",
    "payment_verified": true,
    "segment_list": ["Segment 1", "Segment 2"],
    "comp_list": ["Competition 1"],
    "gift_list": ["T-Shirt", "Badge"],
    "entry_status": true
  },
  "team": {
    "id": 1,
    "team_name": "Team Alpha",
    "payment_verified": true,
    "comp_list": ["Team Competition 1"],
    "gift_list": ["Trophy"],
    "entry_status": true,
    "members": [
      {
        "id": 1,
        "f_name": "John",
        "l_name": "Doe",
        "full_name": "John Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "age": 22,
        "institution": "Example University",
        "institution_id": "EU12345",
        "is_leader": true
      }
    ]
  }
}
```

**Response (Team only):**
```bash
{
  "team": {
    "id": 1,
    "team_name": "Team Alpha",
    "payment_verified": true,
    "comp_list": ["Team Competition 1"],
    "gift_list": ["Trophy"],
    "entry_status": true,
    "members": [...]
  }
}
```

---

### 18. Check Access Permission

**Endpoint:** `GET /api/check/{page}/{event}/{id}/`

**Description:** Check if participant/team has access to specific event

**Authentication:** Required (Volunteer)

**Parameters:**
- `page`: Event type (`segment`, `solo`, or `team`)
- `event`: Event code
- `id`: Participant ID (format: `p_{id}`) or Team ID (format: `t_{id}`)

**Example:**
```bash
GET /api/check/segment/SEG01/p_1/
GET /api/check/solo/COMP01/p_1/
GET /api/check/team/TCOMP01/t_1/
```

**Response:**
```bash
{
  "allowed": true
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```bash
{
  "success": false,
  "errors": {
    "field_name": ["error message"]
  }
}
```

### 401 Unauthorized
```bash
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```bash
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```bash
{
  "success": false,
  "error": "Resource not found"
}
```

### 500 Internal Server Error
```bash
{
  "success": false,
  "error": "Internal server error",
  "details": "Error description"
}
```

---

## Data Models

### Participant
- `f_name`: First name
- `l_name`: Last name
- `gender`: M/F/O
- `email`: Email address (unique)
- `phone`: Phone number
- `age`: Age
- `institution`: Institution name
- `institution_id`: Institution ID
- `address`: Address (optional)
- `t_shirt_size`: XS/S/M/L/XL/XXL (optional)
- `club_reference`: Club reference (optional)
- `campus_ambassador`: Campus ambassador (optional)
- `payment_verified`: Boolean

### Team
- `team_name`: Team name (unique)
- `payment_verified`: Boolean
- `members`: List of TeamParticipant

### Payment
- `phone`: Phone number
- `amount`: Payment amount
- `trx_id`: Transaction ID (unique)
- `datetime`: Payment timestamp

### Segment
- `segment_name`: Segment name
- `code`: Segment code

### Competition
- `competition`: Competition name
- `code`: Competition code

### TeamCompetition
- `competition`: Team competition name
- `code`: Team competition code

### Gift
- `gift_name`: Gift name

---

## Notes

1. All timestamps are in ISO 8601 format
2. All monetary amounts use decimal with 2 decimal places
3. ID parameters starting with `p_` indicate participant, `t_` indicate team
4. Admin endpoints require user to have 'admin' role in Volunteer model
5. Transaction IDs must be unique across all payments
6. Email addresses must be unique for participants
7. Team names must be unique
8. Payment verification for a participant who is a team leader will also verify the team's payment

---

## Usage Examples

### Complete Registration Flow

```bash
# 1. Register participant with segments and competitions
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "participant": {
      "full_name": "John Doe",
      "gender": "M",
      "email": "john@example.com",
      "phone": "1234567890",
      "age": 22,
      "institution": "Example University",
      "institution_id": "EU12345",
      "t_shirt_size": "L"
    },
    "payment": {
      "amount": "500.00",
      "phone": "1234567890",
      "trx_id": "TRX123456789"
    },
    "segment": ["SEG01"],
    "competition": ["COMP01"]
  }'

# 2. Admin verifies payment
curl -X POST http://localhost:8000/api/payment/verify/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{"id": 1}'

# 3. Volunteer records entry
curl -X POST http://localhost:8000/api/recordentry/p_1/ \
  -H "Authorization: Bearer {access_token}"

# 4. Volunteer marks gift as received
curl -X POST http://localhost:8000/api/gifts/p_1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{"gift_name": "T-Shirt"}'
```

---


**Version:** 1.0  
**Last Updated:** 4 October 2025
