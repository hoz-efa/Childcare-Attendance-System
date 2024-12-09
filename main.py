from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
import io, os, calendar, random
from datetime import datetime
import openpyxl

from models import db, User, Student, Attendance

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

db.init_app(app)

with app.app_context():
    db.create_all()
    # Ensure admin exists
    admin = User.query.filter_by(email='admin@mail.com').first()
    if not admin:
        admin_user = User(email='admin@mail.com',
                          password='admin123',
                          first_name='System',
                          last_name='Admin',
                          phone='0000000000',
                          role='admin')
        db.session.add(admin_user)
        db.session.commit()


def check_admin():
    if 'user_id' not in session:
        return None
    user = User.query.get(session['user_id'])
    if user and user.role == 'admin':
        return user
    return None


def check_teacher():
    if 'user_id' not in session:
        return None
    user = User.query.get(session['user_id'])
    if user and user.role == 'teacher':
        return user
    return None


@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('teacher_dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


### Admin Routes
@app.route('/admin/dashboard')
def admin_dashboard():
    user = check_admin()
    if not user:
        return redirect(url_for('index'))
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('admin_dashboard.html', teachers=teachers)


@app.route('/admin/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    user = check_admin()
    if not user:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        fname = request.form.get('first_name')
        lname = request.form.get('last_name')
        phone = request.form.get('phone')
        if email == 'admin@mail.com':
            return redirect(url_for('admin_dashboard'))
        new_teacher = User(email=email,
                           password=password,
                           first_name=fname,
                           last_name=lname,
                           phone=phone,
                           role='teacher')
        db.session.add(new_teacher)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_teacher.html')


@app.route('/admin/delete_teacher/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    user = check_admin()
    if not user:
        return redirect(url_for('index'))
    teacher = User.query.get(teacher_id)
    if teacher and teacher.email != 'admin@mail.com':
        db.session.delete(teacher)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/teacher_profile/<int:teacher_id>')
def admin_view_teacher_profile(teacher_id):
    user = check_admin()
    if not user:
        return redirect(url_for('index'))
    teacher = User.query.get(teacher_id)
    if not teacher or teacher.role != 'teacher':
        return "Teacher not found."
    return render_template('view_teacher_profile.html', teacher=teacher)


### Teacher Routes
@app.route('/teacher/dashboard')
def teacher_dashboard():
    user = check_teacher()
    if not user:
        return redirect(url_for('index'))
    students = Student.query.filter_by(teacher_id=user.id).all()
    return render_template('teacher_dashboard.html',
                           students=students,
                           teacher=user)


@app.route('/teacher/profile')
def teacher_profile():
    user = check_teacher()
    if not user:
        return redirect(url_for('index'))
    return render_template('teacher_profile.html', teacher=user)


@app.route('/teacher/add_student', methods=['GET', 'POST'])
def add_student():
    user = check_teacher()
    if not user:
        return redirect(url_for('index'))
    if request.method == 'POST':
        fname = request.form.get('first_name')
        lname = request.form.get('last_name')
        parent_name = request.form.get('parent_name')
        parent_email = request.form.get('parent_email')
        emergency_contact_name = request.form.get('emergency_contact_name')
        emergency_contact_phone = request.form.get('emergency_contact_phone')
        pickup_person_name = request.form.get('pickup_person_name')
        pickup_person_phone = request.form.get('pickup_person_phone')
        allergies = request.form.get('allergies')
        student = Student(first_name=fname,
                          last_name=lname,
                          parent_name=parent_name,
                          parent_email=parent_email,
                          emergency_contact_name=emergency_contact_name,
                          emergency_contact_phone=emergency_contact_phone,
                          pickup_person_name=pickup_person_name,
                          pickup_person_phone=pickup_person_phone,
                          allergies=allergies,
                          teacher_id=user.id)
        db.session.add(student)
        db.session.commit()
        return redirect(url_for('teacher_dashboard'))
    return render_template('add_student.html')


@app.route('/teacher/student_profile/<int:student_id>')
def student_profile(student_id):
    user = check_teacher()
    if not user:
        return redirect(url_for('index'))
    student = Student.query.get(student_id)
    if not student or student.teacher_id != user.id:
        return "Student not found."
    return render_template('student_profile.html', student=student)


@app.route('/teacher/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    user = check_teacher()
    if not user:
        return redirect(url_for('index'))
    student = Student.query.get(student_id)
    if not student or student.teacher_id != user.id:
        return "Not allowed"
    if request.method == 'POST':
        student.first_name = request.form.get('first_name')
        student.last_name = request.form.get('last_name')
        student.parent_name = request.form.get('parent_name')
        student.parent_email = request.form.get('parent_email')
        student.emergency_contact_name = request.form.get(
            'emergency_contact_name')
        student.emergency_contact_phone = request.form.get(
            'emergency_contact_phone')
        student.pickup_person_name = request.form.get('pickup_person_name')
        student.pickup_person_phone = request.form.get('pickup_person_phone')
        student.allergies = request.form.get('allergies')
        db.session.commit()
        return redirect(url_for('teacher_dashboard'))
    return render_template('edit_student.html', student=student)


@app.route('/teacher/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    user = check_teacher()
    if not user:
        return redirect(url_for('index'))
    student = Student.query.get(student_id)
    if student and student.teacher_id == user.id:
        db.session.delete(student)
        db.session.commit()
    return redirect(url_for('teacher_dashboard'))


### Attendance
@app.route('/teacher/attendance', methods=['GET', 'POST'])
def teacher_attendance():
    user = check_teacher()
    if not user:
        return redirect(url_for('index'))
    today_str = datetime.now().strftime('%Y-%m-%d')
    students = Student.query.filter_by(teacher_id=user.id).all()
    if request.method == 'POST':
        for s in students:
            in_time = request.form.get(f'in_{s.id}')
            out_time = request.form.get(f'out_{s.id}')
            remark = request.form.get(f'remark_{s.id}')
            att = Attendance.query.filter_by(date=today_str,
                                             student_id=s.id).first()
            if att:
                # Update existing attendance
                if in_time:
                    att.in_time = in_time
                if out_time:
                    att.out_time = out_time
                if remark:
                    att.remark = remark
            else:
                # Only add attendance if in_time or out_time is provided
                # If neither is provided, student is absent
                if in_time or out_time:
                    new_att = Attendance(
                        date=today_str,
                        student_id=s.id,
                        in_time=in_time if in_time else None,
                        out_time=out_time if out_time else None,
                        remark=remark if remark else None)
                    db.session.add(new_att)
        db.session.commit()
        return redirect(url_for('teacher_attendance'))
    attendance_records = {
        a.student_id: a
        for a in Attendance.query.filter_by(date=today_str).all()
    }
    return render_template('attendance.html',
                           students=students,
                           attendance_records=attendance_records)


@app.route('/teacher/finalize_attendance')
def finalize_attendance():
    user = check_teacher()
    if not user:
        return redirect(url_for('index'))
    now = datetime.now()
    if now.hour >= 17:
        today_str = now.strftime('%Y-%m-%d')
        records = Attendance.query.filter_by(date=today_str).all()
        for r in records:
            if r.in_time and not r.out_time:
                r.out_time = "16:00"
        db.session.commit()
    return redirect(url_for('teacher_attendance'))


### Reports
@app.route('/teacher/reports')
def teacher_reports():
    user = check_teacher()
    if not user:
        return redirect(url_for('index'))
    now = datetime.now()
    month = request.args.get('month', now.month)
    year = request.args.get('year', now.year)
    month = int(month)
    year = int(year)

    students = Student.query.filter_by(teacher_id=user.id).all()

    # Calculate attendance percentage for each student
    # Count working days (Monday-Friday) in the month
    month_days = calendar.monthrange(year, month)[1]
    working_days = 0
    for day in range(1, month_days + 1):
        weekday = datetime(year, month, day).weekday()
        if weekday < 5:
            working_days += 1

    # For each student, count how many days they attended
    student_data = []
    for s in students:
        attended = 0
        for day in range(1, month_days + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            weekday = datetime(year, month, day).weekday()
            if weekday < 5:
                att = Attendance.query.filter_by(date=date_str,
                                                 student_id=s.id).first()
                # Consider present if att exists and has in_time
                if att and att.in_time:
                    attended += 1
        attendance_percentage = (attended / working_days *
                                 100) if working_days > 0 else 0
        student_data.append((s, attendance_percentage))

    return render_template('reports.html',
                           student_data=student_data,
                           month=month,
                           year=year)


@app.route('/teacher/download_student_report/<int:student_id>')
def download_student_report(student_id):
    user = check_teacher()
    if not user:
        return redirect(url_for('index'))
    student = Student.query.get(student_id)
    if not student or student.teacher_id != user.id:
        return "Not allowed"
    month = int(request.args.get('month', datetime.now().month))
    year = int(request.args.get('year', datetime.now().year))
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Report"
    ws.append(["Date", "In Time", "Out Time", "Status", "Remark"])
    month_days = calendar.monthrange(year, month)[1]
    for day in range(1, month_days + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        weekday = datetime(year, month, day).weekday()
        if weekday < 5:
            att = Attendance.query.filter_by(date=date_str,
                                             student_id=student.id).first()
            if att and att.in_time:
                status = "Present"
                in_t = att.in_time if att.in_time else ""
                out_t = att.out_time if att.out_time else ""
                rem = att.remark if att.remark else ""
            else:
                status = "Absent"
                in_t = ""
                out_t = ""
                rem = ""
            ws.append([date_str, in_t, out_t, status, rem])
    file_data = io.BytesIO()
    wb.save(file_data)
    file_data.seek(0)
    filename = f"{student.first_name}_{student.last_name}_{year}_{month}.xlsx"
    return send_file(
        file_data,
        as_attachment=True,
        download_name=filename,
        mimetype=
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/teacher/download_monthly_report')
def download_monthly_report():
    user = check_teacher()
    if not user:
        return redirect(url_for('index'))
    month = int(request.args.get('month', datetime.now().month))
    year = int(request.args.get('year', datetime.now().year))
    students = Student.query.filter_by(teacher_id=user.id).all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "All Students"
    ws.append(
        ["Student Name", "Date", "In Time", "Out Time", "Status", "Remark"])
    month_days = calendar.monthrange(year, month)[1]
    for s in students:
        for day in range(1, month_days + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            weekday = datetime(year, month, day).weekday()
            if weekday < 5:
                att = Attendance.query.filter_by(date=date_str,
                                                 student_id=s.id).first()
                if att and att.in_time:
                    status = "Present"
                    in_t = att.in_time if att.in_time else ""
                    out_t = att.out_time if att.out_time else ""
                    rem = att.remark if att.remark else ""
                else:
                    status = "Absent"
                    in_t = ""
                    out_t = ""
                    rem = ""
                ws.append([
                    f"{s.first_name} {s.last_name}", date_str, in_t, out_t,
                    status, rem
                ])
    file_data = io.BytesIO()
    wb.save(file_data)
    file_data.seek(0)
    filename = f"All_Students_{year}_{month}.xlsx"
    return send_file(
        file_data,
        as_attachment=True,
        download_name=filename,
        mimetype=
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
