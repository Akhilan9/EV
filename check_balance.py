from app import app, db, User
import sys

with app.app_context():
    users = User.query.all()
    print("--- USER WALLET BALANCES ---")
    for u in users:
        print(f"ID: {u.id} | User: {u.username} | Balance: {u.wallet_balance}")
    print("---------------------------")
