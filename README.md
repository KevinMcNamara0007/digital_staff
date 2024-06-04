## Installation
#### requires 
- python >= 3.9
### PIP
- pip install virtualenv
- virtualenv venv
- ./venv/Scripts/activate
- pip install -r requirements.txt

## Running APP
uvicorn src.asgi:digital_staff --host=127.0.0.1 --port=8080