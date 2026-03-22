from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Company, Student, Drive, Application
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "final_submission_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.db'

db.init_app(app)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(role='Admin').first():
        admin = User(username='admin', password=generate_password_hash('admin123'), role='Admin', status='Approved')
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def home(): return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form['username']
        role = request.form['role']
        new_user = User(username=uname, password=generate_password_hash(request.form['password']), 
                        role=role, status='Approved' if role=='Student' else 'Pending')
        db.session.add(new_user)
        db.session.commit()
        if role == 'Student': db.session.add(Student(user_id=new_user.id, name=request.form['name']))
        else: db.session.add(Company(user_id=new_user.id, name=request.form['name']))
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(username=request.form['username']).first()
    if user and check_password_hash(user.password, request.form['password']):
        if user.role == 'Company' and user.status == 'Pending': return "Admin Approval Pending!"
        session['user_id'], session['role'] = user.id, user.role
        return redirect(url_for('dashboard'))
    return "Invalid!"

@app.route('/dashboard')
def dashboard():
    u = User.query.get(session['user_id'])
    if u.role == 'Admin':
        pending_comps = User.query.filter_by(role='Company', status='Pending').all()
        pending_drives = Drive.query.filter_by(status='Pending').all()
        return render_template('admin_dashboard.html', companies=pending_comps, drives=pending_drives)
    elif u.role == 'Company':
        comp = Company.query.filter_by(user_id=u.id).first()
        return render_template('company_dashboard.html', company=comp)
    else:
        stu = Student.query.filter_by(user_id=u.id).first()
        drives = Drive.query.filter_by(status='Approved').all()
        return render_template('student_dashboard.html', student=stu, drives=drives)

@app.route('/approve_company/<int:id>')
def approve_comp(id):
    User.query.get(id).status = 'Approved'
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/approve_drive/<int:id>')
def approve_drive(id):
    Drive.query.get(id).status = 'Approved'
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/create_drive', methods=['POST'])
def create_drive():
    comp = Company.query.filter_by(user_id=session['user_id']).first()
    db.session.add(Drive(company_id=comp.id, job_title=request.form['title'], description=request.form['desc']))
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/apply/<int:id>')
def apply(id):
    stu = Student.query.filter_by(user_id=session['user_id']).first()
    if not Application.query.filter_by(student_id=stu.id, drive_id=id).first():
        db.session.add(Application(student_id=stu.id, drive_id=id))
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__': app.run(debug=True)