from flask import Blueprint, render_template, request, redirect, url_for, make_response
from .auth import create_user, authenticate_user, create_session
from config import Config
import logging
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']
        
        if password != confirm:
            return render_template('signup.html', error="Passwords do not match")
        
        try:
            user = create_user(username, password)
            session = create_session(user['id'])
            response = make_response(redirect(url_for('main.index')))
            response.set_cookie(
                Config.SESSION_COOKIE_NAME, 
                value=session['session_id'],
                expires=datetime.fromisoformat(session['expires_at']),
                httponly=True,
                path='/',
                samesite='Lax'
            )
            return response
        except Exception as e:
            logging.error(f"Signup failed: {e}")
            return render_template('signup.html', error="Username already exists")
    
    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = authenticate_user(username, password)
        if user:
            session = create_session(user['id'])
            response = make_response(redirect(url_for('main.index')))
            response.set_cookie(
                Config.SESSION_COOKIE_NAME, 
                value=session['session_id'],
                expires=datetime.fromisoformat(session['expires_at']),
                httponly=True,
                path='/',
                samesite='Lax'
            )
            return response
        else:
            return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    response = make_response(redirect(url_for('auth.login')))
    response.delete_cookie(
        Config.SESSION_COOKIE_NAME,
        path='/' 
    )
    return response