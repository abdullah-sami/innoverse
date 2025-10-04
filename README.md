### Request format for registration
Endpoint:
```bash
Method: POST
BASE_URL/api/register/
```

Request body (JSON):
```bash
{
    "participant": {
        "full_name": "",
        "gender": "",
        "email": "",
        "phone": "",
        "age": "",
        "institution": "",
        "institution_id": "",
        "address": "",
        "t_shirt_size": "",
        "club_reference": "",
        "campus_ambassador": ""
    },
    "payment": {
        "amount": "",
        "phone": "",
        "trx_id": "",
    },
    "segment": [
        "segment_code_1",
        "segment_code_2",
    ],
    "competition": [
        "competition_code_1",
        "competition_code_2",
    ],
    "team_competition": {
        "team": {
            "team_name": "",
            "participant": [
                {
                    "full_name": "",
                    "gender": "",
                    "email": "",
                    "phone": "",
                    "age": "",
                    "institution": "",
                    "institution_id": "",
                    "address": "",
                    "t_shirt_size": "",
                    "club_reference": "",
                    "campus_ambassador": ""
                },
                {
                    "full_name": "",
                    "gender": "",
                    "phone": "",
                    "age": "",
                    "institution": "",
                    "institution_id": "",
                    "t_shirt_size": ""
                }
            ]
        },
        "competition": [
            "team_competition_code_1",
            "team_competition_code_2",
        ]
    },
}
```

Response:
```bash
{
    "success": true,
    "message": "Registration completed successfully",
    "data": {
        "participant": {
            "id": 2,
            "name": "Saeed Adnan",
            "email": "saeedadnan1219@gmail.com",
            "payment_verified": false
        },
        "payment": {
            "trx_id": "hf237ry298",
            "amount": "700.00"
        },
        "segments": [
            "expo"
        ],
        "competitions": [
            "3m-res"
        ],
        "team": {
            "id": 2,
            "name": "BabySharks",
            "payment_verified": false,
            "members_count": 2,
            "competitions": [
                "sc_quiz"
            ]
        },
        "team_payment": {
            "trx_id": "hf237ry298",
            "amount": "700.00"
        }
    }
}
```




###### How to run django server

### 1. Install Python  
Make sure **Python 3.10+** is installed.  
Check version:
```bash
python --version
```


### 2. Create a Virtual Environment
```bash
python -m venv venv
```
Activeate virtual environment
```bash
venv\Scripts\activate
```


### 3. Install Dependencies
```bash
pip install -r ../requirements.txt
```


### 4. Environment Variable
Put .env file in the same directory as manage.py



### 5. Run Development Server
Start the Django server:
```bash
python manage.py runserver 0.0.0.0:8000
```
You’ll see something like:
Starting development server at http://0.0.0.0:8000/

Open in browser:
go to your local ip
e.g. http://127.0.0.1:8000/
