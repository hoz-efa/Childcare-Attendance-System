from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'teacher'


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    parent_name = db.Column(db.String(100), nullable=False)
    parent_email = db.Column(db.String(120), nullable=False)
    emergency_contact_name = db.Column(db.String(100), nullable=False)
    emergency_contact_phone = db.Column(db.String(20), nullable=False)
    pickup_person_name = db.Column(db.String(100))
    pickup_person_phone = db.Column(db.String(20))
    allergies = db.Column(db.Text)
    teacher_id = db.Column(db.Integer,
                           db.ForeignKey('user.id'),
                           nullable=False)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    student_id = db.Column(db.Integer,
                           db.ForeignKey('student.id'),
                           nullable=False)
    in_time = db.Column(db.String(10))
    out_time = db.Column(db.String(10))
    remark = db.Column(db.Text)
