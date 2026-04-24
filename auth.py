from flask_bcrypt import Bcrypt
from database import db, User, OTP
import random
import string

bcrypt = Bcrypt()

def hash_password(password):
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password(hashed, password):
    return bcrypt.check_password_hash(hashed, password)

def generate_otp(user_id):
    code = ''.join(random.choices(string.digits, k=6))
    new_otp = OTP(user_id=user_id, code=code)
    db.session.add(new_otp)
    db.session.commit()
    return code

def verify_otp(user_id, code):
    otp_record = OTP.query.filter_by(user_id=user_id, code=code).order_by(OTP.created_at.desc()).first()
    if otp_record:
        # Check if otp is too old (e.g., > 5 mins) if needed
        return True
    return False
