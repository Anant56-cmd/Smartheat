from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.db import db
from database.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access the command portal.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Support login via Username or Email (e.g. Gmail)
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f'Welcome back, {user.username} ({user.role.capitalize()})!', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('dashboard.index'))
        else:
            flash('Invalid username/email or password. Please check your credentials.', 'danger')

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', 'admin').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not username or not email or not password:
            flash('Please fill out all required fields.', 'danger')
            return render_template('register.html')

        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address (e.g., yourname@gmail.com).', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match. Please re-type your password.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'warning')
            return render_template('register.html')

        # Check for existing username
        if User.query.filter_by(username=username).first():
            flash(f'Username "{username}" is already registered. Please choose another username.', 'warning')
            return render_template('register.html')

        # Check for existing email
        if User.query.filter_by(email=email).first():
            flash(f'An account with email "{email}" already exists. Please log in.', 'info')
            return redirect(url_for('auth.login'))

        # Standardize role: only allow 'admin' or 'user'
        assigned_role = 'admin' if role == 'admin' else 'user'

        # Create new user / admin
        new_user = User(
            username=username,
            email=email,
            role=assigned_role
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        role_label = 'Administrator' if assigned_role == 'admin' else 'User'
        flash(f'Account created successfully as {role_label}! You can now sign in using your username or Gmail.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('auth.login'))
