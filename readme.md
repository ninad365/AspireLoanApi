# Aspire Loan App

### Prerequisites

Python (>=3.8)

pip (Python package manager)

MySQL

### Installation

#### Run the following command in the terminal to clone the repository:

git clone [https://github.com/ninad365/AspireLoanApi.git](https://github.com/ninad365/AspireLoanApi.git)

#### Navigate to the project directory:

cd your-application

### Create a virtual environment (recommended):

python -m venv env

#### Activate the virtual environment (on macOS/Linux):
source venv/bin/activate
#### Activate the virtual environment (on windows):
env\Scripts\activate

### Install dependencies:
pip install -r requirements.txt

#### Run the sql script from the following file in MySQL to set up the database:

Database/Main_Database.sql

#### Run the sql script from the following file in MySQL to set up the database for testing:

Database/Test_Database.sql

Create a .env file. There is an example .env file in the root folder

### Running the Application

uvicorn app.main:app --reload

### API Documentation

Visit http://127.0.0.1:8000/docs

### Testing

#### Run tests using following command to run all tests:
pytest
