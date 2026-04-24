import razorpay
from database import db, User, Transaction

# IMPORTANT: You can provide your official Test API Keys here.
# Updated with user-provided Test API Keys
RAZORPAY_KEY_ID = "rzp_test_SaUcrVHkmFY6cW"
RAZORPAY_KEY_SECRET = "0eby2m0MvQkLkVHMinyR03JM"

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def create_razorpay_order(amount, currency="INR"):
    """
    Creates a Razorpay order. Amount should be in paise.
    Checks if keys are placeholders for simulation.
    """
    if RAZORPAY_KEY_ID == "rzp_test_YOUR_KEY_ID":
        print("SIMULATION MODE: Using Mock Order (Replace keys for live testing)")
        return {
            "id": "order_mock_12345",
            "amount": int(amount * 100),
            "currency": currency
        }
    
    data = {
        "amount": int(amount * 100), # amount in the smallest currency unit (paise)
        "currency": currency,
        "payment_capture": "1" # auto capture
    }
    order = client.order.create(data=data)
    return order

def verify_payment_signature(razorpay_payment_id, razorpay_order_id, razorpay_signature):
    """
    Verifies the Razorpay payment signature.
    Checks if keys are placeholders for simulation.
    """
    if RAZORPAY_KEY_ID == "rzp_test_YOUR_KEY_ID":
        print("SIMULATION MODE: Signature Verified Automatically")
        return True
    
    try:
        params_dict = {
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_signature': razorpay_signature
        }
        client.utility.verify_payment_signature(params_dict)
        return True
    except Exception as e:
        print(f"Payment verification failed: {e}")
        return False

def get_wallet_balance(user_id):
    user = User.query.get(user_id)
    return user.wallet_balance if user else 0.0

def process_payment(user_id, amount):
    user = User.query.get(user_id)
    if user and user.wallet_balance >= amount:
        user.wallet_balance -= amount
        db.session.commit()
        return True, "Payment successful"
    return False, "Insufficient wallet balance"

def calculate_cost(duration):
    # ₹0.50 per minute for simplify
    return round(duration * 0.5, 2)
