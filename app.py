from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'outdoor-gear-manager-2025-secure-key-' + str(hash('your-unique-identifier')))

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///gear.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Association table for many-to-many relationship between trips and gear
trip_gear = db.Table('trip_gear',
    db.Column('trip_id', db.Integer, db.ForeignKey('trip.id'), primary_key=True),
    db.Column('gear_item_id', db.Integer, db.ForeignKey('gear_item.id'), primary_key=True),
    db.Column('is_packed', db.Boolean, default=False),
    db.Column('date_packed', db.DateTime)
)

# Database Models
class GearItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(50))
    category = db.Column(db.String(50), nullable=False)
    weight_grams = db.Column(db.Integer)
    condition = db.Column(db.String(20), default='Good')
    notes = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<GearItem {self.name}>'

class ActivityTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # Climbing, Camping, Hiking
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f'<ActivityTemplate {self.name}>'

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    location = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Many-to-many relationship with gear items
    gear_items = db.relationship('GearItem', secondary=trip_gear, backref='trips')
    
    def __repr__(self):
        return f'<Trip {self.name}>'

@app.route('/debug-db-info')
def debug_database_info():
    import os
    
    output = ["<style>body{font-family:monospace;}</style>"]
    output.append("<h2>🔍 DATABASE CONNECTION INFO</h2>")
    
    db_url = os.environ.get('DATABASE_URL', 'Not set')
    output.append(f"<b>DATABASE_URL:</b> {db_url}<br><br>")
    
    if db_url.startswith('sqlite'):
        output.append("📁 <b>Type:</b> SQLite (file-based database)<br>")
        output.append("💡 <b>Access:</b> File is stored locally on Render server<br>")
    elif db_url.startswith('postgresql'):
        output.append("🐘 <b>Type:</b> PostgreSQL<br>")
        output.append("💡 <b>Access:</b> Can connect directly with psql or pgAdmin<br>")
    else:
        output.append(f"❓ <b>Type:</b> Unknown database type<br>")
    
    output.append(f"<br><b>SQLAlchemy config:</b> {app.config['SQLALCHEMY_DATABASE_URI']}<br>")
    
    output.append("<br><a href='/debug-db'>← View Database Contents</a> | <a href='/'>← Home</a>")
    return "".join(output)

@app.route('/debug-db')
def debug_database():
    from sqlalchemy import text
    
    output = ["<style>body{font-family:monospace;}</style>"]
    output.append("<h2>🗄️ PRODUCTION DATABASE STATUS</h2>")
    
    # Gear Items
    output.append("<h3>📦 GEAR ITEMS</h3>")
    gear_items = GearItem.query.all()
    if gear_items:
        for item in gear_items:
            output.append(f"ID {item.id}: <b>{item.name}</b> ({item.category}) - {item.weight_grams}g - {item.condition}<br>")
    else:
        output.append("No gear items found<br>")
    
    # Trips
    output.append("<h3>🗓️ TRIPS</h3>")
    trips = Trip.query.all()
    if trips:
        for trip in trips:
            output.append(f"ID {trip.id}: <b>{trip.name}</b> - {trip.activity_type}<br>")
            output.append(f"  📍 {trip.location or 'No location'}<br>")
            output.append(f"  🎒 {len(trip.gear_items)} gear items<br>")
    else:
        output.append("No trips found<br>")
    
    # Activity Templates
    output.append("<h3>🏃‍♂️ ACTIVITY TEMPLATES</h3>")
    templates = ActivityTemplate.query.all()
    for template in templates:
        output.append(f"ID {template.id}: <b>{template.name}</b> - {template.description}<br>")
    
    # Trip-Gear Relationships (Packing Status)
    output.append("<h3>✅ PACKING STATUS</h3>")
    try:
        result = db.session.execute(text("SELECT trip_id, gear_item_id, is_packed FROM trip_gear"))
        relationships = result.fetchall()
        if relationships:
            for row in relationships:
                trip_name = Trip.query.get(row[0]).name
                gear_name = GearItem.query.get(row[1]).name
                packed_status = "✅ PACKED" if row[2] else "⭕ NOT PACKED"
                output.append(f"Trip '<b>{trip_name}</b>' → {gear_name}: {packed_status}<br>")
        else:
            output.append("No trip-gear relationships found<br>")
    except Exception as e:
        output.append(f"Error checking packing status: {e}<br>")
    
    output.append("<br><a href='/'>← Back to Home</a>")
    return "".join(output)

# Add this route for production database setup
@app.route('/init-db')
def init_database():
    try:
        # Create all tables (this might recreate if structure changed)
        db.create_all()
        
        # Always ensure activity templates exist
        if ActivityTemplate.query.count() == 0:
            activities = [
                ActivityTemplate(name='Climbing', description='Rock climbing and mountaineering'),
                ActivityTemplate(name='Camping', description='Overnight camping trips'),
                ActivityTemplate(name='Hiking', description='Day hikes and backpacking')
            ]
            for activity in activities:
                db.session.add(activity)
            db.session.commit()
        
        return "Database updated successfully! Add your gear at <a href='/gear/add'>Add Gear</a> | <a href='/'>Go to Home</a>"
    except Exception as e:
        return f"Error: {str(e)}"

# Routes
@app.route('/')
def home():
    recent_gear = GearItem.query.order_by(GearItem.date_added.desc()).limit(5).all()
    total_items = GearItem.query.count()
    return render_template('home.html', recent_gear=recent_gear, total_items=total_items)

@app.route('/gear')
def gear_list():
    category = request.args.get('category', 'all')
    if category == 'all':
        gear = GearItem.query.order_by(GearItem.name).all()
    else:
        gear = GearItem.query.filter_by(category=category).order_by(GearItem.name).all()
    
    categories = db.session.query(GearItem.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('gear_list.html', gear=gear, categories=categories, current_category=category)

@app.route('/gear/add', methods=['GET', 'POST'])
def add_gear():
    if request.method == 'POST':
        gear = GearItem(
            name=request.form['name'],
            brand=request.form['brand'],
            category=request.form['category'],
            weight_grams=int(request.form['weight_grams']) if request.form['weight_grams'] else None,
            condition=request.form['condition'],
            notes=request.form['notes']
        )
        db.session.add(gear)
        db.session.commit()
        flash(f'{gear.name} added successfully!', 'success')
        return redirect(url_for('gear_list'))
    
    return render_template('add_gear.html')

@app.route('/gear/edit/<int:gear_id>', methods=['GET', 'POST'])
def edit_gear(gear_id):
    gear = GearItem.query.get_or_404(gear_id)
    
    if request.method == 'POST':
        gear.name = request.form['name']
        gear.brand = request.form['brand']
        gear.category = request.form['category']
        gear.weight_grams = int(request.form['weight_grams']) if request.form['weight_grams'] else None
        gear.condition = request.form['condition']
        gear.notes = request.form['notes']
        
        db.session.commit()
        flash(f'{gear.name} updated successfully!', 'success')
        return redirect(url_for('gear_list'))
    
    return render_template('edit_gear.html', gear=gear)

@app.route('/gear/delete/<int:gear_id>', methods=['POST'])
def delete_gear(gear_id):
    gear = GearItem.query.get_or_404(gear_id)
    gear_name = gear.name
    
    db.session.delete(gear)
    db.session.commit()
    flash(f'{gear_name} deleted successfully!', 'success')
    return redirect(url_for('gear_list'))

@app.route('/activities')
def activities():
    templates = ActivityTemplate.query.all()
    return render_template('activities.html', templates=templates)

@app.route('/trips')
def trips():
    trips = Trip.query.order_by(Trip.created_date.desc()).all()
    return render_template('trips.html', trips=trips)

@app.route('/trips/create', methods=['GET', 'POST'])
def create_trip():
    if request.method == 'POST':
        trip = Trip(
            name=request.form['name'],
            activity_type=request.form['activity_type'],
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form['start_date'] else None,
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form['end_date'] else None,
            location=request.form['location'],
            notes=request.form['notes']
        )
        db.session.add(trip)
        db.session.commit()
        flash(f'Trip "{trip.name}" created successfully!', 'success')
        return redirect(url_for('trip_detail', trip_id=trip.id))
    
    activity_templates = ActivityTemplate.query.all()
    return render_template('create_trip.html', activity_templates=activity_templates)

@app.route('/trips/<int:trip_id>')
def trip_detail(trip_id):
    from sqlalchemy import text
    
    trip = Trip.query.get_or_404(trip_id)
    all_gear = GearItem.query.order_by(GearItem.category, GearItem.name).all()
    
    # Get packed status for each item - Fixed query
    packed_status = {}
    result = db.session.execute(text("""
        SELECT gear_item_id, is_packed FROM trip_gear 
        WHERE trip_id = :trip_id
    """), {"trip_id": trip_id})
    
    for row in result:
        packed_status[row[0]] = bool(row[1])
    
    return render_template('trip_detail.html', trip=trip, all_gear=all_gear, packed_status=packed_status)

@app.route('/trips/<int:trip_id>/add_gear/<int:gear_id>')
def add_gear_to_trip(trip_id, gear_id):
    trip = Trip.query.get_or_404(trip_id)
    gear = GearItem.query.get_or_404(gear_id)
    
    if gear not in trip.gear_items:
        trip.gear_items.append(gear)
        db.session.commit()
        flash(f'Added {gear.name} to trip checklist!', 'success')
    else:
        flash(f'{gear.name} is already in this trip!', 'warning')
    
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/trips/<int:trip_id>/debug')
def debug_trip(trip_id):
    from sqlalchemy import text
    
    result = db.session.execute(text("""
        SELECT gear_item_id, is_packed FROM trip_gear 
        WHERE trip_id = :trip_id
    """), {"trip_id": trip_id})
    
    debug_info = []
    for row in result:
        gear = GearItem.query.get(row[0])
        debug_info.append(f"Gear: {gear.name}, Packed: {row[1]}")
    
    return f"<h1>Debug Trip {trip_id}</h1>" + "<br>".join(debug_info)

@app.route('/trips/<int:trip_id>/toggle_packed/<int:gear_id>')
def toggle_packed(trip_id, gear_id):
    from sqlalchemy import text
    
    # Toggle packed status in the association table
    result = db.session.execute(text("""
        SELECT is_packed FROM trip_gear 
        WHERE trip_id = :trip_id AND gear_item_id = :gear_id
    """), {"trip_id": trip_id, "gear_id": gear_id})
    
    current_status = result.fetchone()
    new_status = not (current_status[0] if current_status else False)
    
    db.session.execute(text("""
        UPDATE trip_gear 
        SET is_packed = :packed, date_packed = :date_packed
        WHERE trip_id = :trip_id AND gear_item_id = :gear_id
    """), {
        "packed": new_status,
        "date_packed": datetime.utcnow() if new_status else None,
        "trip_id": trip_id,
        "gear_id": gear_id
    })
    
    db.session.commit()
    
    gear_name = GearItem.query.get(gear_id).name
    status_text = "packed" if new_status else "unpacked"
    flash(f'{gear_name} marked as {status_text}!', 'success')
    
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/trips/<int:trip_id>/remove_gear/<int:gear_id>')
def remove_gear_from_trip(trip_id, gear_id):
    trip = Trip.query.get_or_404(trip_id)
    gear = GearItem.query.get_or_404(gear_id)
    
    if gear in trip.gear_items:
        trip.gear_items.remove(gear)
        db.session.commit()
        flash(f'Removed {gear.name} from trip checklist!', 'success')
    
    return redirect(url_for('trip_detail', trip_id=trip_id))

if __name__ == '__main__':
    # Initialize database
    with app.app_context():
        # Drop and recreate all tables to ensure new structure
        db.drop_all()
        db.create_all()
        
        # Add sample data if no gear exists
        if GearItem.query.count() == 0:
            sample_headlamp = GearItem(
                name='Black Diamond Spot 400',
                brand='Black Diamond',
                category='Lighting',
                weight_grams=88,
                condition='Good',
                notes='Primary headlamp for all activities'
            )
            db.session.add(sample_headlamp)
            
            # Add basic activity templates
            activities = [
                ActivityTemplate(name='Climbing', description='Rock climbing and mountaineering'),
                ActivityTemplate(name='Camping', description='Overnight camping trips'),
                ActivityTemplate(name='Hiking', description='Day hikes and backpacking')
            ]
            for activity in activities:
                db.session.add(activity)
            
            db.session.commit()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)