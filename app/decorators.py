from functools import wraps
from flask import redirect, url_for, g
from .utils import get_current_user

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('auth.login'))
        g.user = user
        return f(*args, **kwargs)
    return decorated_function