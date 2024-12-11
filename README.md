# Hospital-Management-System
A Python-based web application for managing hospital operations, including patient management, appointment scheduling, staff records, room assignments, lab tests, and billing. Built using Flask for the backend, Bootstrap for the frontend, and PostgreSQL for the database.

# Hospital Database Management System (HDMS)

A web application designed to streamline hospital management processes. This system provides functionalities for handling patients, staff, appointments, rooms, lab tests, and billing operations.

## Features
- **Patient Management**: Add, search, update, and remove patient details.
- **Appointment Scheduling**: Schedule, view, and manage appointments between doctors and patients.
- **Staff Records**: Manage doctor and nurse records.
- **Room Assignments**: Allocate rooms for patients and doctors with availability tracking.
- **Lab Tests**: Record and view lab test information.
- **Billing**: Generate and track bills with payment status.

## Technology Stack
- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, Bootstrap
- **Database**: PostgreSQL
- **Libraries**:
  - `psycopg2` for database connectivity
  - Flask for routing and templates

## Database Design
The system uses the following database tables:
1. Doctor
2. Patient
3. Nurse
4. Room
5. DoctorRoom
6. Appointment
7. LabTest
8. Billing

### ER Diagram
[Include the ER Diagram here if available]

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/hospital-dbms.git
   cd hospital-dbms

2. Set up the PostgreSQL database:
- Create a database named Hospital.
- Update database credentials in app.py
- Setup Database Credentials:
  ```
    psycopg2.connect(
        host="localhost",
        dbname="Hospital",
        user="your_username",
        password="your_password",
        port=5432
    )
3. Run the application:
   ```
     python app.py
## Usage
- Use the navigation bar to access different functionalities.
- Manage patients, staff, rooms, and appointments through intuitive interfaces.
- Monitor lab tests and billing details.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Author
A S Abhishek - [GitHub](https://github.com/abhishek12345678900987654)
