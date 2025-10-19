# Innoverse API Documentation

Complete API documentation for the Innoverse event management system.

## Base URL

```bash
http://innoversebd.bdix.cloud
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
  "refresh": "string",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "role": "admin"
  }
}
```

**Note:** Only users with role `admin` are allowed to access admin endpoints.

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
  "refresh": "string",
  "user": {
    "id": int,
    "username": "string",
    "email": "string",
    "role": "string"
  }
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

### 5. Get Registration Info

**Endpoint:** `GET /api/register/`

**Description:** Get registration endpoint information

**Authentication:** Not required

**Response:**
```bash
{
  "message": "Registration endpoint is ready",
  "method": "POST",
  "endpoint": "/api/register/"
}
```

---

### 6. Registration

**Endpoint:** `POST /api/register/`

**Content-Type:** `application/json`

**Description:** Register a new participant with optional segments, competitions, and team competitions

**Authentication:** Not required

**Request Body:**
```bash
{
  "participant": {
    "full_name": "John Doe",
    "gender": "M",
    "email": "john@example.com",
    "phone": "1234567890",
    "grade": "12",
    "institution": "Example University",
    "guardian_phone": "1234567890",
    "address": "123 Main St",
    "t_shirt_size": "L"
  },
  "payment": {
    "amount": "500.00",
    "phone": "1234567890",
    "method": "bkash",
    "trx_id": "TRX123456789"
  },
  "competition": ["sc_olym", "programming"],
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
          "address": "456 Elm St",
          "t_shirt_size": "M"
        }
      ]
    },
    "competition": ["quiz"]
  },
  "coupon": {
    "coupon_code": "SAVE20"
  }
}
```

**Field Requirements:**

**Participant Fields:**
- `full_name` (required): Full name of the participant
- `gender` (required): M/F/O
- `email` (required): Unique email address
- `phone` (required): Phone number
- `age` (required): Age as integer
- `institution` (required): Institution name
- `address` (optional): Address
- `t_shirt_size` (optional): XS/S/M/L/XL/XXL

**Payment Fields:**
- `amount` (required): Payment amount (decimal)
- `phone` (required): Payment phone number
- `trx_id` (required): Unique transaction ID

**Optional Fields:**
- `competition` (optional): Array of competition codes
- `team_competition` (optional): Team competition details
- `coupon` (optional): Coupon information

**Segments and Competition Codes:**
```bash
Solo Competitions:
  - Science Olympiad: sc_olym
  - Programming Contest: programming
  - 3-Minute Research: 3m_res
  - Research Article Contest: res_art
  - Math Maestro: math
  
Team Competitions:
  - Science Quiz: quiz
  - Robo Soccer: robo_soc
```

**Response:**
```bash
{
  "success": true,
  "message": "Registration completed successfully. Confirmation email sent.",
  "email_sent": true,
  "data": {
    "participant": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "payment_verified": false
    },
    "payment": {
      "coupon": "SAVE20",
      "trx_id": "TRX123456789",
      "method": "bkash",
      "amount": "500.00"
    },
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
    "participant": ["Email john@example.com is already registered"],
    "payment": ["Transaction ID TRX123456789 already exists"],
    "team_competition": ["Team name 'Team Alpha' already exists"]
  }
}
```

**Validation Rules:**
1. Participant email must be unique
2. Transaction ID must be unique
3. Team name must be unique (if team_competition provided)
4. Team leader email cannot match any team member email
5. Team member emails must be unique within the team
6. Valid segment and competition codes must be provided
7. Coupon must exist and have remaining uses

---

### 7. Validate Coupon

**Endpoint:** `GET /api/coupon/{code}/`

**Description:** Validate a coupon code and get discount information

**Authentication:** Not required

**Parameters:**
- `code`: Coupon code to validate

**Example:**
```bash
GET /api/coupon/SAVE20/
```

**Response:**
```bash
{
  "success": true,
  "coupon": {
    "code": "SAVE20",
    "discount": 20
  }
}
```

**Error Response:**
```bash
{
  "success": false,
  "error": "Invalid or inactive coupon code"
}
```

---

## Admin Dashboard Endpoints

All admin endpoints require authentication with admin volunteer role.

### 8. List Participants

**Endpoint:** `GET /api/participant/`

**Description:** Get list of all participants with filtering options

**Authentication:** Required (Admin Volunteer)

**Query Parameters:**
- `segment` (optional): Filter by segment code
- `competition` (optional): Filter by competition code
- `payment_verified` (optional): Filter by payment status (true/false)
- `search` (optional): Search by first name, last name, or email

**Example:**
```bash
GET /api/participant/?segment=expo&payment_verified=true&search=john
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
      "segments": ["Innovation Expo", "Sketch Talk"],
      "competitions": ["Math Auction"],
      "has_entry": true
    }
  ]
}
```

**Error Response:**
```bash
{
  "success": false,
  "error": "Failed to fetch participants"
}
```

---

### 9. Get Participant Details

**Endpoint:** `GET /api/participant/{id}/`

**Description:** Get detailed information about a specific participant

**Authentication:** Required (Admin Volunteer)

**Parameters:**
- `id`: Participant ID

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
    "grade": "12",
    "institution": "Example University",
    "guardian_phone": "1234567890",
    "address": "123 Main St",
    "payment_verified": true,
    "segment_registrations": [
      {
        "segment_name": "Innovation Expo",
        "segment_code": "expo",
        "datetime": "2025-01-15T10:30:00Z"
      }
    ],
    "competition_registrations": [
      {
        "competition_name": "Math Auction",
        "competition_code": "m_auction",
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
        "method": "bkash",
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

**Error Response:**
```bash
{
  "success": false,
  "error": "Participant not found"
}
```

---

### 10. List Teams

**Endpoint:** `GET /api/team/`

**Description:** Get list of all teams with filtering options

**Authentication:** Required (Admin Volunteer)

**Query Parameters:**
- `competition` (optional): Filter by team competition code
- `payment_verified` (optional): Filter by payment status (true/false)

**Example:**
```bash
GET /api/team/?competition=pr_show&payment_verified=true
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
          "is_leader": true
        },
        {
          "id": 2,
          "f_name": "Alice",
          "l_name": "Johnson",
          "full_name": "Alice Johnson",
          "email": "alice@example.com",
          "phone": "9876543210",
          "age": 21,
          "institution": "Example University",
          "is_leader": false
        }
      ],
      "competition_registrations": [
        {
          "competition_name": "Project Showcasing",
          "competition_code": "pr_show",
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
          "method": "bkash",
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

**Error Response:**
```bash
{
  "success": false,
  "error": "Failed to fetch teams"
}
```

---

### 11. Get Team Details

**Endpoint:** `GET /api/team/{id}/`

**Description:** Get detailed information about a specific team

**Authentication:** Required (Admin Volunteer)

**Parameters:**
- `id`: Team ID

**Response:** Same structure as individual team in list response

---

### 12. List Segments

**Endpoint:** `GET /api/segment/`

**Description:** Get list of all segments

**Authentication:** Required (Admin Volunteer)

**Response:**
```bash
{
  "success": true,
  "count": 3,
  "data": [
    {
      "id": 1,
      "segment_name": "Innovation Expo",
      "code": "expo"
    },
    {
      "id": 2,
      "segment_name": "Sketch Talk",
      "code": "sketch"
    }
  ]
}
```

---

### 13. Get Segment Details

**Endpoint:** `GET /api/segment/{code}/`

**Description:** Get segment details with participant list

**Authentication:** Required (Admin Volunteer)

**Parameters:**
- `code`: Segment code

**Example:**
```bash
GET /api/segment/expo/
```

**Response:**
```bash
{
  "success": true,
  "segment": {
    "id": 1,
    "segment_name": "Innovation Expo",
    "code": "expo"
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
      "segments": ["Innovation Expo"],
      "competitions": ["Math Auction"],
      "has_entry": true
    }
  ]
}
```

**Error Response:**
```bash
{
  "success": false,
  "error": "Segment not found"
}
```

---

### 14. List Competitions

**Endpoint:** `GET /api/competition/`

**Description:** Get list of all solo competitions

**Authentication:** Required (Admin Volunteer)

**Response:**
```bash
{
  "success": true,
  "count": 5,
  "data": [
    {
      "id": 1,
      "competition": "Math Auction",
      "code": "m_auction"
    }
  ]
}
```

---

### 15. Get Competition Details

**Endpoint:** `GET /api/competition/{code}/`

**Description:** Get competition details with participant list

**Authentication:** Required (Admin Volunteer)

**Parameters:**
- `code`: Competition code

**Example:**
```bash
GET /api/competition/m_auction/
```

**Response:**
```bash
{
  "success": true,
  "competition": {
    "id": 1,
    "competition": "Math Auction",
    "code": "m_auction"
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
      "segments": ["Innovation Expo"],
      "competitions": ["Math Auction"],
      "has_entry": true
    }
  ]
}
```

**Error Response:**
```bash
{
  "success": false,
  "error": "Competition not found"
}
```

---

### 16. List Team Competitions

**Endpoint:** `GET /api/team-competition/`

**Description:** Get list of all team competitions

**Authentication:** Required (Admin Volunteer)

**Response:**
```bash
{
  "success": true,
  "count": 3,
  "data": [
    {
      "id": 1,
      "competition": "Project Showcasing",
      "code": "pr_show"
    }
  ]
}
```

---

### 17. Get Team Competition Details

**Endpoint:** `GET /api/team-competition/{code}/`

**Description:** Get team competition details with team list

**Authentication:** Required (Admin Volunteer)

**Parameters:**
- `code`: Team competition code

**Example:**
```bash
GET /api/team-competition/pr_show/
```

**Response:**
```bash
{
  "success": true,
  "competition": {
    "id": 1,
    "competition": "Project Showcasing",
    "code": "pr_show"
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

**Error Response:**
```bash
{
  "success": false,
  "error": "Team competition not found"
}
```

---

### 18. Verify Payment

**Endpoint:** `POST /api/payment/verify/`

**Description:** Toggle payment verification status for a participant. If the participant is a team leader, the team's payment status will also be toggled. Sends confirmation email when payment is verified (changes from false to true).

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
  "message": "Payment verified for John Doe and team Team Alpha. Confirmation email sent.",
  "email_sent": true,
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

**Response (Without Team):**
```bash
{
  "success": true,
  "message": "Payment verified for John Doe. Confirmation email sent.",
  "email_sent": true,
  "data": {
    "participant": {
      "id": 1,
      "name": "John Doe",
      "payment_verified": true
    }
  }
}
```

**Error Response:**
```bash
{
  "success": false,
  "error": "Participant not found"
}
```

**Note:** Email is only sent when payment status changes from unverified (false) to verified (true).

---

## Volunteer App Endpoints

### 19. Check Entry Status

**Endpoint:** `GET /api/recordentry/{id}/`

**Description:** Check if entry has been recorded for participant or team

**Authentication:** Required (Volunteer)

**Parameters:**
- `id`: Participant ID (format: `p_{id}`) or Team ID (format: `t_{id}`)

**Example:**
```bash
GET /api/recordentry/p_1/
GET /api/recordentry/t_1/
```

**Response (Entry exists):**
```bash
{
  "success": true
}
```

**Response (Entry does not exist):**
```bash
{
  "success": false
}
```

---

### 20. Record Entry

**Endpoint:** `POST /api/recordentry/{id}/`

**Description:** Record entry for a participant or team. Automatically associates the volunteer who records the entry.

**Authentication:** Required (Volunteer)

**Parameters:**
- `id`: Participant ID (format: `p_{id}`) or Team ID (format: `t_{id}`)

**Example:**
```bash
POST /api/recordentry/p_1/
POST /api/recordentry/t_1/
```

**Response (Participant - Success):**
```bash
{
  "success": true,
  "message": "Entry recorded successfully",
  "participant": {
    "id": 12,
    "name": "Sajid",
    "email": "photos.rafidabdullahsami@gmail.com",
    "phone": "+8801894515222",
    "institution": "Cox's Bazar Hashemia Madrasa",
    "guardian_phone": null,
    "payment_verified": true
  }
}
```

**Response (Team - Success):**
```bash
{
  "success": true,
  "message": "Entry recorded successfully",
  "team": {
    "id": 9,
    "name": "Shreks 6",
    "member_count": 2,
    "payment_verified": false,
    "members": [
      {
        "name": "Ahmad Saeed Anas",
        "email": "rafidabdullahsami+4@gmail.com",
        "is_leader": true
      },
      {
        "name": "Sami Sami",
        "email": "sami@sami.com",
        "is_leader": false
      }
    ]
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

```bash
{
  "success": false,
  "error": "No participant with the ID"
}
```

```bash
{
  "success": false,
  "error": "Volunteer not found for this user"
}
```

---

### 21. Delete Entry Record

**Endpoint:** `DELETE /api/recordentry/{id}/`

**Description:** Delete entry record for a participant or team

**Authentication:** Required (Volunteer)

**Parameters:**
- `id`: Participant ID (format: `p_{id}`) or Team ID (format: `t_{id}`)

**Example:**
```bash
DELETE /api/recordentry/p_1/
DELETE /api/recordentry/t_1/
```

---

### 22. Get Gift Status

**Endpoint:** `GET /api/gifts/{id}/`

**Description:** Get gift distribution status for participant or team along with participant/team information.

**Authentication:** Required (Volunteer)

**Parameters:**
- `id`: Participant ID (format: `p_{id}`) or Team ID (format: `t_{id}`)

**Example:**
```bash
GET /api/gifts/p_1/
GET /api/gifts/t_1/
```

**Response (Participant):**
```bash
{
  "gifts": {
    "tshirt": 0,
    "breakfast": 0,
    "snacks": 0,
    "notebook": 1
  },
  "participant": {
    "id": 11,
    "name": "Sadia a",
    "email": "rafidabdullahsami+5@gmail.com",
    "phone": "+8801894515222",
    "institution": "Cox's Bazar Hashemia Madrasa",
    "guardian_phone": "904857",
    "grade": "12",
    "payment_verified": true
  }
}
```

**Response (Team with Participant):**
```bash
{
  "gifts": {
    "tshirt": 0,
    "breakfast": 0,
    "snacks": 0,
    "notebook": 1
  },
  "participant": {
    "id": 11,
    "name": "Sadia a",
    "email": "rafidabdullahsami+5@gmail.com",
    "phone": "+8801894515222",
    "institution": "Cox's Bazar Hashemia Madrasa",
    "guardian_phone": "904857",
    "grade": "12",
    "payment_verified": true
  },
  "team": {
    "id": 10,
    "name": "Sadia",
    "member_count": 2,
    "payment_verified": true,
    "members": [
      {
        "name": "Sadia",
        "email": "rafidabdullahsami+5@gmail.com",
        "is_leader": true
      },
      {
        "name": "Sami Sami",
        "email": "abdullahsami4103+1@gmail.com",
        "is_leader": false
      }
    ]
  }
}
```

**Note:** Gift status values: 0 = not received, 1 = received. Response includes participant/team information along with gift status.

**Error Response:**
```bash
{
  "error": "No participant with the ID"
}
```

```bash
{
  "error": "Invalid ID format. Use 'p_' for participant or 't_' for team"
}
```

---

### 23. Mark Gift as Received

**Endpoint:** `POST /api/gifts/{id}/`

**Description:** Mark a gift as received by participant or team. Gift name is case-insensitive. Automatically associates the volunteer who marks the gift.

**Authentication:** Required (Volunteer)

**Parameters:**
- `id`: Participant ID (format: `p_{id}`) or Team ID (format: `t_{id}`)

**Request Body:**
```bash
{
  "gift_name": "tshirt"
}
```

**Response:**
```bash
{
  "message": "T-Shirt marked as received successfully"
}
```

**Response (Already marked):**
```bash
{
  "message": "T-Shirt already marked as received"
}
```

**Error Response:**
```bash
{
  "error": "gift_name is required in request body"
}
```

```bash
{
  "error": "Gift 'Invalid Gift' not found"
}
```

```bash
{
  "error": "No participant with the ID"
}
```

```bash
{
  "error": "Volunteer not found for this user"
}
```

---

### 24. Get Participant/Team Info

**Endpoint:** `GET /api/info/{id}/`

**Description:** Get detailed information about participant and/or team. If participant ID is provided and the participant is part of a team, both participant and team information are returned.

**Authentication:** Required (Volunteer)

**Parameters:**
- `id`: Participant ID (format: `p_{id}`) or Team ID (format: `t_{id}`)

**Example:**
```bash
GET /api/info/p_1/
GET /api/info/t_1/
```

**Response (Participant only):**
```bash
{
  "participant": {
    "id": 9,
    "f_name": "Ahmad",
    "l_name": "Saeed Anas",
    "email": "rafidabdullahsami+3@gmail.com",
    "phone": "+8801894515222",
    "age": 19,
    "institution": "Cox's Bazar Hashemia Madrasa",
    "address": "Cox's Bazar",
    "guardian_phone": null,
    "payment_verified": true,
    "segment_list": [
      "Innovation Expo"
    ],
    "comp_list": [
      "3-Minute Research"
    ],
    "gift_list": [],
    "entry_status": false
  }
}
```

**Response (Participant with Team):**
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
    "address": "123 Main St",
    "guardian_phone": "1234567890",
    "payment_verified": true,
    "segment_list": ["Innovation Expo", "Sketch Talk"],
    "comp_list": ["Math Auction"],
    "gift_list": ["T-Shirt", "Badge"],
    "entry_status": true
  },
  "team": {
    "id": 1,
    "team_name": "Team Alpha",
    "payment_verified": true,
    "comp_list": ["Project Showcasing"],
    "gift_list": ["Trophy"],
    "entry_status": true,
    "members": [
      {
        "id": 1,
        "f_name": "John",
        "l_name": "Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "age": 22,
        "institution": "Example University",
        "is_leader": true
      },
      {
        "id": 2,
        "f_name": "Alice",
        "l_name": "Johnson",
        "email": "alice@example.com",
        "phone": "9876543210",
        "age": 21,
        "institution": "Example University",
        "is_leader": false
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
    "comp_list": ["Project Showcasing"],
    "gift_list": ["Trophy"],
    "entry_status": true,
    "members": [...]
  }
}
```

**Error Response:**
```bash
{
  "error": "No participant with the ID"
}
```

```bash
{
  "error": "Invalid ID format. Use 'p_' for participant or 't_' for team"
}
```

---


### 25. Check Access Permission

**Endpoint:** `GET /api/check/{page}/{event}/{id}/`

**Description:** Check if participant/team has registered for and has access to a specific event

**Authentication:** Required (Volunteer)

**Parameters:**
- `page`: Event type
  - `segment` - Check segment registration
  - `solo` - Check solo competition registration
  - `team` - Check team competition registration
- `event`: Event code (e.g., expo, m_auction, pr_show)
- `id`: Participant ID (format: `p_{id}`) or Team ID (format: `t_{id}`)

**Example:**
```bash
GET /api/check/segment/expo/p_1/
GET /api/check/solo/m_auction/p_1/
GET /api/check/team/pr_show/t_1/
```

**Response (Access allowed):**
```bash
{
    "allowed": true,
    "page": "segment",
    "event": "expo",
    "participant": {
        "id": 11,
        "name": "Sadia a",
        "email": "rafidabdullahsami+5@gmail.com",
        "phone": "+8801894515222",
        "institution": "Cox's Bazar Hashemia Madrasa",
        "guardian_phone": "904857",
        "grade": "12",
        "payment_verified": true
    },
    "team": {
        "id": 10,
        "name": "Sadia",
        "member_count": 2,
        "payment_verified": true,
        "members": [
            {
                "name": "Sadia ",
                "email": "rafidabdullahsami+5@gmail.com",
                "is_leader": true
            },
            {
                "name": "Sami Sami",
                "email": "abdullahsami4103+1@gmail.com",
                "is_leader": false
            }
        ]
    }
}
```

**Response (Access not allowed):**
```bash
{
  "allowed": false
}
```

**Error Response:**
```bash
{
  "error": "No participant with the ID"
}
```

```bash
{
  "error": "Invalid page type"
}
```

```bash
{
  "error": "Invalid ID format. Use 'p_' for participant or 't_' for team"
}
```

**Notes:**
- For `segment` and `solo` pages, only participant IDs (`p_{id}`) are valid
- For `team` page, only team IDs (`t_{id}`) are valid
- The endpoint checks if the participant/team is registered for the specified event

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

or

```bash
{
  "success": false,
  "error": "Error message"
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

or

```bash
{
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

or

```bash
{
  "error": "Failed to perform operation"
}
```

---

## Data Models

### Participant
- `f_name`: First name (derived from full_name)
- `l_name`: Last name (derived from full_name)
- `gender`: M (Male) / F (Female) / O (Other)
- `email`: Email address (unique)
- `phone`: Phone number (optional)
- `age`: Age (integer)
- `institution`: Institution name (optional)
- `guardian_phone`: Guardian Phone number (optional)
- `address`: Address (optional)
- `t_shirt_size`: XS/S/M/L/XL/XXL (optional)
- `payment_verified`: Boolean (default: false)

### TeamParticipant
- `f_name`: First name
- `l_name`: Last name
- `gender`: M/F/O
- `email`: Email address
- `phone`: Phone number
- `age`: Age (integer)
- `institution`: Institution name
- `address`: Address (optional)
- `t_shirt_size`: XS/S/M/L/XL/XXL (optional)
- `team`: Foreign key to Team
- `is_leader`: Boolean (indicates team leader)

### Team
- `team_name`: Team name (unique)
- `payment_verified`: Boolean (default: false)
- `members`: Related TeamParticipant objects

### Payment
- `participant`: Foreign key to Participant (nullable)
- `team`: Foreign key to Team (nullable)
- `phone`: Phone number
- `amount`: Payment amount (decimal, 2 places)
- `trx_id`: Transaction ID (unique)
- `datetime`: Auto-generated timestamp

**Note:** Payment must be linked to either a participant or a team, but not both.

### Registration
- `participant`: Foreign key to Participant
- `segment`: Foreign key to Segment
- `datetime`: Auto-generated timestamp

### CompetitionRegistration
- `participant`: Foreign key to Participant
- `competition`: Foreign key to Competition
- `datetime`: Auto-generated timestamp

### TeamCompetitionRegistration
- `team`: Foreign key to Team
- `competition`: Foreign key to TeamCompetition
- `datetime`: Auto-generated timestamp

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



**Version:** 1.4
**Last Updated:** 19 October 2025
