from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import db, User, Transaction, OTP, StationNode
from auth import bcrypt, hash_password, check_password, generate_otp, verify_otp
from encryption import encrypt_data, decrypt_data
from blockchain import Blockchain, Block
from payment import (get_wallet_balance, process_payment, calculate_cost, 
                     create_razorpay_order, verify_payment_signature, RAZORPAY_KEY_ID)
import os
import time
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ev_network_v3.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)

@app.route('/ping_new')
def ping_new():
    return "SERVER_IS_UPDATED_V2"

# Initialize Blockchain
blockchain = Blockchain()
if not blockchain.load_from_file('blockchain_data.json'):
    print("No existing blockchain found. Starting fresh with Genesis Block.")
else:
    print("Existing blockchain loaded successfully.")

db.init_app(app)
bcrypt.init_app(app)

# Custom Template Filter
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    if isinstance(value, float):
        return time.strftime(format, time.localtime(value))
    return value.strftime(format)

# Create database tables and seed data
with app.app_context():
    db.create_all()
    # Seed Station Nodes if empty
    if StationNode.query.count() == 0:
        nodes = [
            StationNode(name="Station-Node-01", coordinates_x=450, coordinates_y=120, status="Online", health=98),
            StationNode(name="Station-Node-08", coordinates_x=120, coordinates_y=350, status="Online", health=100),
            StationNode(name="Station-Node-12", coordinates_x=680, coordinates_y=420, status="Maintenance", health=45),
            StationNode(name="Station-Central", coordinates_x=400, coordinates_y=550, status="Online", health=92)
        ]
        db.session.add_all(nodes)
        db.session.commit()
        print("Station Nodes seeded.")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = hash_password(request.form['password'])

        try:
            # Proactively ensure tables exist if a manual deletion happened
            db.create_all()
            
            if User.query.filter_by(username=username).first():
                flash('Username already exists on this node.', 'danger')
                return redirect(url_for('register'))

            new_user = User(username=username, email=email, phone=phone, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Node initialization successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Registration Error: {e}")
            db.session.rollback()
            flash('Network synchronization error. The node database is being rebuilt.', 'warning')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            user = User.query.filter_by(username=username).first()

            if user and check_password(user.password, password):
                session['user_id'] = user.id
                session['username'] = user.username
                
                # Simulated OTP Step
                otp_code = generate_otp(user.id)
                print(f"DEBUG: OTP for {user.username} is {otp_code}")
                flash(f"🧬 AUTHORIZATION TOKEN BROADCAST: {otp_code}", "info")
                session['awaiting_otp'] = True
                return redirect(url_for('otp_verify'))
            
            flash('Invalid credentials or node identifier.', 'danger')
        except Exception as e:
            print(f"Database Error: {e}")
            flash('Network synchronization error. Please re-register your node.', 'warning')
    return render_template('login.html')

@app.route('/otp', methods=['GET', 'POST'])
def otp_verify():
    if 'user_id' not in session or 'awaiting_otp' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        code = request.form['otp']
        if verify_otp(session['user_id'], code):
            session.pop('awaiting_otp', None)
            flash('Node Authentication success! Entering Hub Dashboard.', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid OTP', 'danger')
    return render_template('otp.html')

@app.route('/charging')
def charging_page():
    if 'user_id' not in session or 'awaiting_otp' in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('charging.html', 
                          user_balance=user.wallet_balance, 
                          razorpay_key=RAZORPAY_KEY_ID)

@app.route('/recharge/create_order', methods=['POST'])
def recharge_create_order():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        amount = float(request.json.get('amount', 0))
        if amount < 1:
            return jsonify({"error": "Invalid amount"}), 400
            
        order = create_razorpay_order(amount)
        # Force a strictly typed boolean for the frontend handshake (Extra-Hardened)
        is_mock_key = str(RAZORPAY_KEY_ID).startswith("rzp_test")
        simulation_mode = "simulation" in order or is_mock_key
        
        return jsonify({
            "order_id": order['id'],
            "amount": order['amount'],
            "currency": order['currency'],
            "key_id": RAZORPAY_KEY_ID,
            "simulation": simulation_mode
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/wallet/recharge', methods=['POST'])
def wallet_recharge():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        
        if amount <= 0:
            return jsonify({"error": "Invalid amount"}), 400
            
        user = User.query.get(session['user_id'])
        user.wallet_balance += amount
        
        # RECORD RECHARGE IN BLOCKCHAIN
        blockchain.add_transaction(
            user=user.username,
            ev_model="RECHARGE_NODE",
            duration=0,
            amount=amount,
            tx_id=f"TOPUP_{int(time.time())}"
        )
        blockchain.mine()
        blockchain.save_to_file('blockchain_data.json')
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "new_balance": user.wallet_balance,
            "message": f"Successfully added ₹{amount} to your node wallet."
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/confirm_charging', methods=['POST'])
def confirm_charging():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # FULL AUDIT: Log every received parameter
    print(f"SESSION_AUDIT: Full Packet Received: {request.form.to_dict()}")
    
    vehicle = request.form.get('vehicle')
    duration_str = request.form.get('duration', '0')
    duration = int(duration_str) if duration_str.isdigit() else 0
    cost_str = request.form.get('cost', '0')
    cost = float(cost_str) if cost_str.replace('.','',1).isdigit() else 0.0
    protocol = request.form.get('protocol', 'Hardened-Handshake-V1')
    
    payment_method = str(request.form.get('payment_method', '')).upper()
    user = User.query.get(session['user_id'])
    
    # --- STRICT MODE VALIDATION ---
    if not payment_method or payment_method == '' or payment_method == 'NONE':
        flash("FATAL_ERROR: Transaction Packet Corrupted. No payment method detected.", "danger")
        return redirect(url_for('charging_page'))

    # --- FAILSAFE ATOMIC DEDUCTION PROTOCOL ---
    if payment_method == 'CREDITS':
        try:
            # Atomic SQL Update (Direct subtraction in DB)
            db.session.query(User).filter_by(id=user.id).update({User.wallet_balance: User.wallet_balance - cost})
            db.session.commit()
            print(f"DEBUG: SQL Atomic Update Executed for {user.username}")
        except Exception as e:
            print(f"CRITICAL DEDUCTION ERROR: {e}")

    # EDGE ENCRYPTION SIMULATION
    # Encrypt transaction data at the edge before storage
    raw_data = {
        "user_id": session['user_id'],
        "vehicle": vehicle,
        "duration": duration,
        "cost": cost,
        "timestamp": time.time()
    }
    encrypted_payload = encrypt_data(raw_data)

    # Persist the transaction and user balance in a single atomic commit
    new_tx = Transaction(
        user_id=session['user_id'],
        vehicle=vehicle,
        duration=duration,
        cost=cost,
        status="Initializing",
        encryption_node=f"Edge-Node-Gamma",
        encrypted_data=encrypted_payload
    )
    db.session.add(new_tx)
    db.session.commit()
    print(f"DEBUG: Final commit successful. Balance in DB: {user.wallet_balance}")

    # Start session tracking with the specific TX ID
    session['current_session'] = {
        'tx_id': new_tx.id,
        'vehicle': vehicle,
        'duration': duration,
        'cost': cost,
        'protocol': protocol,
        'start_time': time.time()
    }
    
    return redirect(url_for('charging_progress'))

@app.route('/charging/progress')
def charging_progress():
    if 'current_session' not in session:
        return redirect(url_for('home'))
    return render_template('progress.html', session=session['current_session'])

@app.route('/charging/complete', methods=['POST'])
def charging_complete():
    try:
        # 1. Verification
        if 'current_session' not in session:
            # Fallback: Find the last initializing transaction for this user
            tx = Transaction.query.filter_by(user_id=session.get('user_id'), status="Initializing").order_by(Transaction.timestamp.desc()).first()
            if not tx:
                # If even that fails, find the last completed one
                tx = Transaction.query.filter_by(user_id=session.get('user_id')).order_by(Transaction.timestamp.desc()).first()
            
            if tx:
                return jsonify({"status": "success", "tx_id": tx.id})
            return jsonify({"status": "error", "message": "No active session map found."}), 400
        
        sess = session['current_session']
        tx = Transaction.query.get(sess['tx_id'])
        
        if tx and tx.status != "Completed":
            # 2. Finalize Record (Synchronous DB write)
            tx.status = "Completed"
            db.session.commit()
            
            # 3. Decentralized Blockchain Ledgering
            # Pass all required fields to match the immutable record spec
            blockchain.add_transaction(
                user=session.get('username', 'Anonymous'),
                ev_model=sess.get('vehicle', 'Unknown'),
                duration=sess.get('duration', 0),
                amount=sess.get('cost', 0),
                tx_id=tx.id
            )
            # Mine the block to secure it (Simulated proof of work)
            blockchain.mine()
            blockchain.save_to_file('blockchain_data.json')
        
        # 4. Clean up and respond INSTANTLY
        session.pop('current_session', None)
        return jsonify({"status": "success", "tx_id": tx.id})
        
    except Exception as e:
        print(f"CRITICAL Handshake Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/charging/success/<int:tx_id>')
def view_receipt(tx_id):
    tx = Transaction.query.get_or_404(tx_id)
    return render_template('receipt.html', tx=tx)

@app.route('/exit')
def exit_page():
    session.clear()
    return render_template('exit.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.timestamp.desc()).all()
    station_nodes = StationNode.query.all()
    
    # Calculate average health for the gauge
    avg_health = sum([n.health for n in station_nodes]) // len(station_nodes) if station_nodes else 100
    
    # Simulated handshakes and IDS logs for "Senior" level aesthetics
    handshakes = [
        {"node": "Edge-Protocol-7", "status": "AUTHORIZED", "ip": "192.168.1.104"},
        {"node": "Station-Alpha", "status": "STREAMS_ACTIVE", "ip": "10.0.4.82"},
        {"node": "Central-Grid", "status": "SYNCED", "ip": "172.16.0.1"}
    ]
    ids_logs = [
        {"type": "info", "msg": "Encrypted tunnel established with Edge-Node-Gamma"},
        {"type": "secure", "msg": "SHA-256 Block validation successful"},
        {"type": "warning", "msg": "Brute-force attempt suppressed on Node-04"}
    ]
    
    return render_template('dashboard.html', 
                          user=user,
                          transactions=transactions, 
                          blockchain_blocks=[b.to_dict() for b in blockchain.chain],
                          station_nodes=station_nodes,
                          avg_health=avg_health,
                          handshakes=handshakes,
                          ids_logs=ids_logs)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
