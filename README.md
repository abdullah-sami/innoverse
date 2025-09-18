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
