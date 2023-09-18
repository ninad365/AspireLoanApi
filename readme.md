Aspire Loan App

Prerequisites

Python (>=3.x)
pip (Python package manager)
MySQL

Run the sql script in MySQL to set up the database
Database/Upgrade 1.sql

Installation

# Clone the repository
git clone https://github.com/yourusername/your-application.git

# Navigate to the project directory
cd your-application

# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment (on macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt


Create a .env file. There is an example .env file in root folder

Running the Application

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

API Documentation

Visit http://127.0.0.1:8000/docs

Testing

# Run tests using pytest
pytest