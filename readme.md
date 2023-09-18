# Aspire Loan App

## Prerequisites

Python (>=3.8)

pip (Python package manager)

MySQL

## Installation

### Run the following command in the terminal to clone the repository:

git clone [https://github.com/ninad365/AspireLoanApi.git](https://github.com/ninad365/AspireLoanApi.git)

### Navigate to the project directory:

cd your-application

### Create a virtual environment (recommended):

python -m venv env

### Activate the virtual environment (on macOS/Linux):
source venv/bin/activate

### Install dependencies:
pip install -r requirements.txt

### Run the following sql script from the following file in MySQL to set up the database:

Database/Upgrade 1.sql

Create a .env file. There is an example .env file in root folder

## Running the Application

uvicorn main:app --reload

## API Documentation

Visit http://127.0.0.1:8000/docs

## Testing

### Run tests using following command:
pytest
