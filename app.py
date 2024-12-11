from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2 import errors
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'DBMS')


def create_connection():
    return psycopg2.connect(
        host="localhost",
        dbname="Hospital",
        user="postgres",
        password="abhishek@sql123",
        port=5432
    )


def setup_database():
    conn = create_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Nurse (
            Nurse_ID SERIAL PRIMARY KEY,
            Name VARCHAR(100),
            Phone_Number VARCHAR(15)
        );
        ''')

        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Room (
            Room_ID SERIAL PRIMARY KEY,
            Room_Type VARCHAR(50),
            Availability_Status VARCHAR(20) DEFAULT 'Available',
            Nurse_ID INTEGER,
            FOREIGN KEY (Nurse_ID) REFERENCES Nurse(Nurse_ID)
        );
        ''')

        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Patient (
            Patient_ID SERIAL PRIMARY KEY,
            Name VARCHAR(100),
            Age INTEGER,
            Gender VARCHAR(10),
            Address TEXT,
            Phone_Number VARCHAR(15),
            Room_ID INTEGER,
            FOREIGN KEY(Room_ID) REFERENCES Room(Room_ID)
        );
        ''')

        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Doctor (
            Doctor_ID SERIAL PRIMARY KEY,
            Name VARCHAR(100),
            Specialty VARCHAR(100),
            Phone_Number VARCHAR(15),
            Room_id INTEGER
        );
        ''')

        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS Appointment (
            Appointment_ID SERIAL PRIMARY KEY,
            Patient_ID INTEGER,
            Doctor_ID INTEGER,
            Appointment_Date DATE,
            Diagnosis TEXT,
            Prescription TEXT,
            FOREIGN KEY(Patient_ID) REFERENCES Patient(Patient_ID),
            FOREIGN KEY(Doctor_ID) REFERENCES Doctor(Doctor_ID)
        );
        ''')

        cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS DoctorRoom (
            DoctorRoom_ID SERIAL PRIMARY KEY,
            Room_Type VARCHAR(50),
            Availability_Status VARCHAR(20) DEFAULT 'Available',
            Doctor_ID INTEGER,
            FOREIGN KEY(Doctor_ID) REFERENCES Doctor(Doctor_ID)
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS LabTest (
            Test_ID SERIAL PRIMARY KEY,
            Patient_ID INTEGER,
            Doctor_ID INTEGER,
            Test_Type VARCHAR(100),
            Test_Date DATE
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Billing (
            Bill_ID SERIAL PRIMARY KEY,
            Patient_ID INTEGER,
            Appointment_ID INTEGER,
            Total_Amount DECIMAL(10, 2),
            Payment_Status VARCHAR(20)
        );
        ''')

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error setting up database: {e}")
    finally:
        cursor.close()
        conn.close()


setup_database()


def get_db_connection():
    return create_connection()


# Routes

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/')
def index():
    return render_template('base.html', main_menu=True)


@app.route('/patients')
def patients():
    return render_template('Patient_interface.html', main_menu=False)


@app.route('/staff')
def staff():
    return render_template('Staff_interface.html', main_menu=False)


@app.route('/doctor_operations')
def doctor_operations():
    return render_template('doctor_interface.html')


@app.route('/nurse_operations')
def nurse_operations():
    return render_template('nurse_interface.html')


@app.route('/room_operations')
def room_operations():
    return render_template('room_interface.html')


@app.route('/appointment_operations')
def appointment_operations():
    return render_template('appointment_interface.html')


# Doctor Operations

@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DoctorRoom_ID FROM DoctorRoom WHERE Availability_Status = 'Available'")
            available_rooms = cur.fetchall()
    except Exception as e:
        print(f"Error fetching available rooms: {e}")
        flash(f'Error fetching available rooms: {str(e)}', 'error')
        available_rooms = []
    finally:
        conn.close()

    if request.method == 'POST':
        name = request.form['name']
        specialty = request.form['specialty']
        phone_number = request.form['phone_number']
        room_id = request.form['room_id']

        print(f"Received form data: name={name}, specialty={specialty}, phone_number={phone_number}, room_id={room_id}")

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT Availability_Status FROM DoctorRoom WHERE DoctorRoom_ID = %s", (room_id,))
                room_status = cur.fetchone()
                if not room_status:
                    raise Exception(f"Room with ID {room_id} does not exist")
                if room_status[0] != 'Available':
                    raise Exception(f"Room with ID {room_id} is not available")

                cur.execute(''' 
                    INSERT INTO Doctor (Name, Specialty, Phone_Number, Room_ID)
                    VALUES (%s, %s, %s, %s)
                    RETURNING Doctor_ID;
                ''', (name, specialty, phone_number, room_id))
                doctor_id = cur.fetchone()[0]
                print(f"Doctor inserted with ID: {doctor_id}")

                cur.execute(''' 
                    UPDATE DoctorRoom
                    SET Availability_Status = 'Occupied', Doctor_ID = %s
                    WHERE DoctorRoom_ID = %s;
                ''', (doctor_id, room_id))
                print(f"Room {room_id} updated to Occupied and associated with Doctor ID: {doctor_id}")

                conn.commit()
                flash(f'Doctor added successfully! Doctor ID: {doctor_id}', 'add_doctor_success')
        except Exception as e:
            conn.rollback()
            print(f"Error adding doctor: {e}")
            flash(f'Error adding doctor: {str(e)}', 'error')
        finally:
            conn.close()
        return redirect(url_for('staff'))
    return render_template('add_doctor.html', available_rooms=available_rooms)


@app.route('/search_doctors', methods=['GET', 'POST'])
def search_doctors():
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        if search_term:
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM Doctor WHERE Name ILIKE %s OR Doctor_ID::text = %s",
                        (f'%{search_term}%', search_term)
                    )
                    doctors = cur.fetchall()
            except Exception as e:
                flash(f'Error searching for doctors: {str(e)}', 'error')
                patients = []
            finally:
                conn.close()
            return render_template('search_doctors.html', doctors=doctors)
        else:
            flash("Search term is required.", "error")
    return render_template('search_doctors.html')


@app.route('/remove_doctor/<int:doctor_id>', methods=['POST'])
def remove_doctor(doctor_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT DoctorRoom_ID FROM DoctorRoom WHERE Doctor_ID = %s', (doctor_id,))
            room_id = cur.fetchone()

            cur.execute('SELECT COUNT(*) FROM Appointment WHERE Doctor_ID = %s', (doctor_id,))
            appointment_count = cur.fetchone()[0]

            if appointment_count > 0:
                raise Exception("Doctor has associated appointments")

            if room_id:
                room_id = room_id[0]
                cur.execute(''' 
                    UPDATE DoctorRoom
                    SET Availability_Status = 'Available', Doctor_ID = NULL
                    WHERE DoctorRoom_ID = %s;
                ''', (room_id,))
            else:
                flash('No room found for this doctor.', 'warning')

            cur.execute('DELETE FROM Doctor WHERE Doctor_ID = %s', (doctor_id,))

            conn.commit()
            flash('Doctor removed successfully and room set to available.', 'success')
    except Exception as e:
        conn.rollback()
        if "associated appointments" in str(e):
            flash(
                'Cannot remove doctor. They have associated appointments. Please remove or reassign these appointments first.',
                'error')
        elif "DoctorRoom_ID" in str(e):
            flash('Error retrieving doctor room assignment.', 'error')
        else:
            flash(f'Error removing Doctor: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('search_doctors'))


@app.route('/show_doctors')
def show_doctors():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Doctor")
            doctors = cur.fetchall()
    except Exception as e:
        flash(f'Error fetching doctors: {str(e)}', 'error')
        doctors = []
    finally:
        conn.close()
    return render_template('show_doctors.html', doctors=doctors)


# Patient Operations

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT Room_ID FROM Room WHERE Availability_Status = 'Available'")
            available_rooms = cur.fetchall()
    except Exception as e:
        flash(f'Error fetching available rooms: {str(e)}', 'error')
        available_rooms = []
    finally:
        conn.close()

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        address = request.form['address']
        phone_number = request.form['phone_number']
        room_id = request.form['room_id']

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(''' 
                    INSERT INTO Patient (Name, Age, Gender, Address, Phone_Number, Room_ID)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING Patient_ID;
                ''', (name, age, gender, address, phone_number, room_id))
                patient_id = cur.fetchone()[0]

                cur.execute(''' 
                    UPDATE Room
                    SET Availability_Status = 'Occupied'
                    WHERE Room_ID = %s;
                ''', (room_id,))

                conn.commit()
                flash(f'Patient added successfully! Patient ID: {patient_id}', 'add_patient_success')
        except Exception as e:
            conn.rollback()
            flash(f'Error adding patient: {str(e)}', 'error')
        finally:
            conn.close()
        return redirect(url_for('show_patients'))

    return render_template('add_patient.html', available_rooms=available_rooms)


@app.route('/search_patient', methods=['GET', 'POST'])
def search_patient():
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        if search_term:
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM Patient WHERE Name ILIKE %s OR Patient_ID::text = %s",
                        (f'%{search_term}%', search_term)
                    )
                    patients = cur.fetchall()
            except Exception as e:
                flash(f'Error searching for patients: {str(e)}', 'error')
                patients = []
            finally:
                conn.close()
            return render_template('search_patient.html', patients=patients)
        else:
            flash("Search term is required.", "error")
    return render_template('search_patient.html')


@app.route('/remove_patient/<int:patient_id>', methods=['POST'])
def remove_patient(patient_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT Room_ID FROM Patient WHERE Patient_ID = %s', (patient_id,))
            room_id = cur.fetchone()

            if room_id:
                room_id = room_id[0]

                cur.execute(''' 
                    UPDATE Room
                    SET Availability_Status = 'Available'
                    WHERE Room_ID = %s;
                ''', (room_id,))

            cur.execute('DELETE FROM Patient WHERE Patient_ID = %s', (patient_id,))

            conn.commit()
            flash(f'Patient removed successfully and room set to available.', 'success')
    except errors.ForeignKeyViolation:
        conn.rollback()
        flash(
            'Cannot remove patient. They have associated appointments. Please remove or reassign these appointments first.',
            'error')
    except Exception as e:
        conn.rollback()
        print(f"Error removing patient: {e}")
        flash(f'Error removing patient: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('search_patient'))


@app.route('/show_patients')
def show_patients():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Patient")
            patients = cur.fetchall()
    except Exception as e:
        flash(f'Error fetching patients: {str(e)}', 'error')
        patients = []
    finally:
        conn.close()
    return render_template('show_patients.html', patients=patients)


# Room Operations

@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT Nurse_ID FROM Nurse")
            nurses = cur.fetchall()
    except Exception as e:
        flash(f'Error fetching Nurses: {str(e)}', 'error')
        nurses = []
    finally:
        conn.close()

    if request.method == 'POST':
        room_type = request.form['room_type']
        nurse_id = request.form['nurse_id']
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(''' 
                    INSERT INTO Room (Room_Type, Nurse_ID)
                    VALUES (%s, %s)
                    RETURNING Room_ID;
                ''', (room_type, nurse_id))
                room_id = cur.fetchone()[0]
                conn.commit()
                flash(f'Room added successfully! Room ID: {room_id}', 'add_room_success')
        except Exception as e:
            conn.rollback()
            flash(f'Error adding room: {str(e)}', 'error')
        finally:
            conn.close()
        return redirect(url_for('show_rooms'))
    return render_template('add_room.html', nurses=nurses)


@app.route('/add_doctor_room', methods=['GET', 'POST'])
def add_doctor_room():
    if request.method == 'POST':
        room_type = request.form['room_type']
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(''' 
                    INSERT INTO DoctorRoom (Room_Type)
                    VALUES (%s)
                    RETURNING DoctorRoom_ID;
                ''', (room_type,))
                doctor_room_id = cur.fetchone()[0]
                conn.commit()
                flash(f'Doctor Room added successfully! Room ID: {doctor_room_id}', 'add_doctorroom_success')
        except Exception as e:
            conn.rollback()
            flash(f'Error adding doctor room: {str(e)}', 'error')
        finally:
            conn.close()
        return redirect(url_for('show_doctor_rooms'))
    return render_template('add_doctor_room.html')


@app.route('/show_rooms')
def show_rooms():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Room")
            rooms = cur.fetchall()
    except Exception as e:
        flash(f'Error fetching rooms: {str(e)}', 'error')
        rooms = []
    finally:
        conn.close()
    return render_template('show_rooms.html', rooms=rooms)


@app.route('/show_doctor_rooms')
def show_doctor_rooms():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM DoctorRoom")
            rooms = cur.fetchall()
    except Exception as e:
        flash(f'Error fetching rooms: {str(e)}', 'error')
        rooms = []
    finally:
        conn.close()
    return render_template('show_doctor_rooms.html', rooms=rooms)


@app.route('/check_room_availability')
def check_room_availability():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Room WHERE Availability_Status = 'Available'")
            available_rooms = cur.fetchall()
    except Exception as e:
        flash(f'Error checking room availability: {str(e)}', 'error')
        available_rooms = []
    finally:
        conn.close()
    return render_template('check_room_availability.html', available_rooms=available_rooms)


# Nurse Operations

@app.route('/add_nurse', methods=['GET', 'POST'])
def add_nurse():
    if request.method == 'POST':
        name = request.form['name']
        phone_number = request.form['phone_number']

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(''' 
                    INSERT INTO Nurse (Name, Phone_Number)
                    VALUES (%s, %s)
                    RETURNING Nurse_ID;
                ''', (name, phone_number))
                nurse_id = cur.fetchone()[0]
                conn.commit()
                flash(f'Nurse added successfully! Nurse ID: {nurse_id}', 'add_nurse_success')
        except Exception as e:
            conn.rollback()
            flash(f'Error adding nurse: {str(e)}', 'error')
        finally:
            conn.close()
        return redirect(url_for('staff'))
    return render_template('add_nurse.html')


@app.route('/show_nurses')
def show_nurses():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Nurse")
            nurses = cur.fetchall()
    except Exception as e:
        flash(f'Error fetching Nurses: {str(e)}', 'error')
        nurses = []
    finally:
        conn.close()
    return render_template('show_nurses.html', nurses=nurses)


@app.route('/search_nurse', methods=['GET', 'POST'])
def search_nurse():
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        if search_term:
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM Nurse WHERE Name ILIKE %s OR Nurse_ID::text = %s",
                        (f'%{search_term}%', search_term)
                    )
                    nurses = cur.fetchall()
            except Exception as e:
                flash(f'Error searching for nurses: {str(e)}', 'error')
                nurses = []
            finally:
                conn.close()
            return render_template('search_nurse.html', nurses=nurses)
        else:
            flash("Search term is required.", "error")
    return render_template('search_nurse.html')


@app.route('/remove_nurse/<int:nurse_id>', methods=['POST'])
def remove_nurse(nurse_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM Nurse WHERE Nurse_ID = %s', (nurse_id,))
            conn.commit()
            flash('Nurse removed successfully.', 'success')
    except errors.ForeignKeyViolation:
        conn.rollback()
        flash('Cannot remove nurse. They are assigned to a room. Please reassign the room first.', 'error')
    except Exception as e:
        conn.rollback()
        flash(f'Error removing Nurse: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('search_nurse'))


# Appointment Operations

@app.route('/create_appointment', methods=['GET', 'POST'])
def create_appointment():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT Patient_ID, Name FROM Patient")
            patients = cur.fetchall()
            cur.execute("SELECT Doctor_ID, Name FROM Doctor")
            doctors = cur.fetchall()
    except Exception as e:
        flash(f'Error fetching patients and doctors: {str(e)}', 'error')
        patients, doctors = [], []
    finally:
        conn.close()

    if request.method == 'POST':
        patient_id = request.form['patient_id']
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        diagnosis = request.form['diagnosis']
        prescription = request.form['prescription']

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(''' 
                    INSERT INTO Appointment (Patient_ID, Doctor_ID, Appointment_Date, Diagnosis, Prescription)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING Appointment_ID;
                ''', (patient_id, doctor_id, appointment_date, diagnosis, prescription))
                appointment_id = cur.fetchone()[0]
                conn.commit()
                flash(f'Appointment created successfully! Appointment ID: {appointment_id}', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error creating appointment: {str(e)}', 'error')
        finally:
            conn.close()
        return redirect(url_for('home'))

    return render_template('create_appointment.html', patients=patients, doctors=doctors)


@app.route('/view_appointments')
def view_appointments():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(''' 
                SELECT A.Appointment_ID, P.Name AS Patient_Name, D.Name AS Doctor_Name, A.Appointment_Date, A.Diagnosis, A.Prescription
                FROM Appointment A
                JOIN Patient P ON A.Patient_ID = P.Patient_ID
                JOIN Doctor D ON A.Doctor_ID = D.Doctor_ID;
            ''')
            appointments = cur.fetchall()
    except Exception as e:
        flash(f'Error fetching appointments: {str(e)}', 'error')
        appointments = []
    finally:
        conn.close()
    return render_template('view_appointments.html', appointments=appointments)


@app.route('/remove_appointment/<int:appointment_id>', methods=['POST'])
def remove_appointment(appointment_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Appointment WHERE Appointment_ID = %s', (appointment_id,))
        conn.commit()
        flash('Appointment removed successfully.', 'success')
    except Exception as e:
        flash(f'Error removing appointment: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('view_appointments'))


# Bill Operations

@app.route('/create_bill', methods=['GET', 'POST'])
def create_bill():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        patient_id = request.form['patient_id']
        appointment_id = request.form['appointment_id']
        total_amount = request.form['total_amount']
        payment_status = request.form['payment_status']

        cursor.execute('''
            INSERT INTO Billing (Patient_ID, Appointment_ID, Total_Amount, Payment_Status)
            VALUES (%s, %s, %s, %s)
        ''', (patient_id, appointment_id, total_amount, payment_status))

        conn.commit()
        flash('Bill created successfully!', 'success')
        return redirect(url_for('view_bills'))

    cursor.execute('SELECT Patient_ID, Name FROM Patient')
    patients = cursor.fetchall()

    cursor.execute('SELECT Appointment_ID, Appointment_Date FROM Appointment')
    appointments = cursor.fetchall()

    conn.close()
    return render_template('create_bill.html', patients=patients, appointments=appointments)


@app.route('/view_bills')
def view_bills():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM Billing')
            bills = cur.fetchall()
    except Exception as e:
        flash(f'Error fetching bills: {str(e)}', 'error')
        bills = []
    finally:
        conn.close()
    return render_template('view_bills.html', bills=bills)


@app.route('/view_unpaid_bills')
def view_unpaid_bills():
    conn = get_db_connection()
    unpaid_bills = []

    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM Billing WHERE Payment_Status = %s', ('Pending',))
            unpaid_bills = cur.fetchall()
    except Exception as e:
        flash(f'Error fetching unpaid bills: {str(e)}', 'error')
    finally:
        conn.close()

    return render_template('view_unpaid_bills.html', unpaid_bills=unpaid_bills)


@app.route('/pay_bill/<int:bill_id>', methods=['POST'])
def pay_bill(bill_id):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE Billing
                SET Payment_Status = %s
                WHERE Bill_ID = %s
            ''', ('Paid', bill_id))
            conn.commit()
            flash(f'Bill ID {bill_id} has been marked as paid!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error updating bill status: {str(e)}', 'error')
    finally:
        conn.close()

    return redirect(url_for('view_unpaid_bills'))


# Lab Operations

@app.route('/create_lab_test', methods=['GET', 'POST'])
def create_lab_test():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT Patient_ID, Name FROM Patient')
    patients = cursor.fetchall()

    cursor.execute('SELECT Doctor_ID, Name FROM Doctor')
    doctors = cursor.fetchall()

    test_types = [
        'Blood Test',
        'Urine Test',
        'X-Ray',
        'MRI',
        'CT Scan',
        'Ultrasound',
        'Allergy Test',
        'Lipid Profile',
        'Blood Sugar Test',
        'Thyroid Function Test'
    ]

    if request.method == 'POST':
        patient_id = request.form['patient_id']
        doctor_id = request.form['doctor_id']
        test_type = request.form['test_type']
        test_date = request.form['test_date']

        try:
            cursor.execute('''
                INSERT INTO LabTest (Patient_ID, Doctor_ID, Test_Type, Test_Date)
                VALUES (%s, %s, %s, %s);
            ''', (patient_id, doctor_id, test_type, test_date))
            conn.commit()
            flash('Lab test created successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error creating lab test: {str(e)}', 'error')
        finally:
            conn.close()
        return redirect(url_for('view_lab_tests'))

    return render_template('create_lab_test.html', patients=patients, doctors=doctors, test_types=test_types)


@app.route('/view_lab_tests')
def view_lab_tests():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM LabTest')
            lab_tests = cur.fetchall()
    except Exception as e:
        flash(f'Error fetching lab tests: {str(e)}', 'error')
        lab_tests = []
    finally:
        conn.close()
    return render_template('view_lab_tests.html', lab_tests=lab_tests)


if __name__ == '__main__':
    app.run(debug=True)
