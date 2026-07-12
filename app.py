"""
Shidow Tours & Adventures
Flask Application - Production Ready
Deployment: Render
Database: PostgreSQL (Supabase via psycopg2)
Storage: Supabase Storage
"""

import os
import uuid
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from supabase import create_client, Client
import re

# ============================================================
# APPLICATION INITIALIZATION
# ============================================================

app = Flask(__name__)

# Environment Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL')

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

# ============================================================
# DATABASE CONNECTION HELPER
# ============================================================

def get_db_connection():
    """
    Create and return a PostgreSQL database connection.
    Uses DATABASE_URL from environment variables.
    Returns a connection object with dictionary cursor.
    """
    try:
        conn = psycopg2.connect(app.config['DATABASE_URL'])
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    except psycopg2.OperationalError as e:
        print(f"Database connection error: {e}")
        return None

def close_db_connection(conn, cursor=None):
    """
    Safely close database connection and cursor.
    """
    try:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    except Exception as e:
        print(f"Error closing database connection: {e}")

# ============================================================
# IMAGE UPLOAD HELPER
# ============================================================

def upload_image(file, folder='destinations'):
    """
    Upload an image to Supabase Storage and return the public URL.
    """
    if not supabase:
        print("Supabase client not initialized")
        return None
    
    if not file or not file.filename:
        return None
    
    try:
        # Get file extension
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        
        # Generate unique filename
        filename = f"{folder}/{uuid.uuid4().hex}.{ext}"
        
        # Upload to Supabase
        response = supabase.storage.from_('images').upload(
            filename,
            file.read(),
            {'content-type': file.content_type or 'image/jpeg'}
        )
        
        # Get public URL
        public_url = supabase.storage.from_('images').get_public_url(filename)
        return public_url
    except Exception as e:
        print(f"Upload error: {e}")
        return None

# ============================================================
# AUTHENTICATION DECORATOR
# ============================================================

def login_required(f):
    """
    Decorator to require admin login for routes.
    Redirects to admin login page if not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login to access the admin panel.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================
# ADMIN AUTHENTICATION ROUTES
# ============================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """
    Admin login page.
    GET: Display login form.
    POST: Authenticate admin user.
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('admin/login.html')
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error. Please try again.', 'danger')
            return render_template('admin/login.html')
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, password_hash, role FROM admins WHERE username = %s AND status = 'active'",
                (username,)
            )
            admin = cursor.fetchone()
            close_db_connection(conn, cursor)
            
            if admin and check_password_hash(admin['password_hash'], password):
                session['admin_id'] = admin['id']
                session['admin_username'] = admin['username']
                session['admin_role'] = admin['role']
                
                # Update last login
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE admins SET last_login = NOW() WHERE id = %s",
                        (admin['id'],)
                    )
                    conn.commit()
                    close_db_connection(conn, cursor)
                
                flash('Welcome back, {}!'.format(admin['username']), 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred during login. Please try again.', 'danger')
        
        return render_template('admin/login.html')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """
    Logout admin user and clear session.
    """
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))

# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route('/admin')
@login_required
def admin_dashboard():
    """
    Admin dashboard displaying key metrics.
    """
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return render_template('admin/dashboard.html', 
                             total_destinations=0,
                             total_packages=0,
                             featured_destinations=0,
                             featured_packages=0)
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM destinations")
        total_destinations = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM packages")
        total_packages = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM destinations WHERE featured = true")
        featured_destinations = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM packages WHERE featured = true")
        featured_packages = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT id, country, location, category, featured, created_at 
            FROM destinations 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent_destinations = cursor.fetchall()
        
        cursor.execute("""
            SELECT id, title, badge, price, featured, created_at 
            FROM packages 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent_packages = cursor.fetchall()
        
        close_db_connection(conn, cursor)
        
        return render_template('admin/dashboard.html',
                             total_destinations=total_destinations,
                             total_packages=total_packages,
                             featured_destinations=featured_destinations,
                             featured_packages=featured_packages,
                             recent_destinations=recent_destinations,
                             recent_packages=recent_packages)
    except Exception as e:
        print(f"Dashboard error: {e}")
        close_db_connection(conn)
        flash('Error loading dashboard data.', 'danger')
        return render_template('admin/dashboard.html',
                             total_destinations=0,
                             total_packages=0,
                             featured_destinations=0,
                             featured_packages=0)

# ============================================================
# ADMIN - DESTINATIONS CRUD
# ============================================================

@app.route('/admin/destinations')
@login_required
def admin_destinations():
    """
    List all destinations with filtering options.
    """
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return render_template('admin/destinations.html', destinations=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, country, location, category, price_per_day, 
                   minimum_days, cover_image, featured, status, created_at 
            FROM destinations 
            ORDER BY created_at DESC
        """)
        destinations = cursor.fetchall()
        close_db_connection(conn, cursor)
        return render_template('admin/destinations.html', destinations=destinations)
    except Exception as e:
        print(f"Destinations list error: {e}")
        close_db_connection(conn)
        flash('Error loading destinations.', 'danger')
        return render_template('admin/destinations.html', destinations=[])

@app.route('/admin/destinations/create', methods=['GET', 'POST'])
@login_required
def admin_destination_create():
    """
    Create a new destination with image upload.
    """
    if request.method == 'POST':
        country = request.form.get('country', '').strip()
        location = request.form.get('location', '').strip()
        category = request.form.get('category', '').strip()
        price_per_day = request.form.get('price_per_day', 0)
        minimum_days = request.form.get('minimum_days', 1)
        description = request.form.get('description', '').strip()
        featured = request.form.get('featured') == 'on'
        status = request.form.get('status', 'active')
        
        if not country or not location or not category:
            flash('Country, location, and category are required.', 'danger')
            return render_template('admin/destination_form.html')
        
        try:
            price_per_day = float(price_per_day) if price_per_day else 0
            minimum_days = int(minimum_days) if minimum_days else 1
        except ValueError:
            flash('Invalid price or days value.', 'danger')
            return render_template('admin/destination_form.html')
        
        # Handle image upload
        cover_image = None
        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and file.filename:
                cover_image = upload_image(file, 'destinations')
                if not cover_image:
                    flash('Failed to upload image. Please try again.', 'danger')
                    return render_template('admin/destination_form.html')
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error.', 'danger')
            return render_template('admin/destination_form.html')
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO destinations 
                (country, location, category, price_per_day, minimum_days, 
                 description, cover_image, featured, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (country, location, category, price_per_day, minimum_days, 
                  description, cover_image, featured, status))
            
            destination_id = cursor.fetchone()['id']
            conn.commit()
            close_db_connection(conn, cursor)
            
            flash('Destination created successfully!', 'success')
            return redirect(url_for('admin_destinations'))
        except Exception as e:
            print(f"Create destination error: {e}")
            close_db_connection(conn)
            flash('Error creating destination. Please try again.', 'danger')
    
    return render_template('admin/destination_form.html')

@app.route('/admin/destinations/edit/<int:destination_id>', methods=['GET', 'POST'])
@login_required
def admin_destination_edit(destination_id):
    """
    Edit an existing destination with image upload.
    """
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_destinations'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM destinations WHERE id = %s", (destination_id,))
        destination = cursor.fetchone()
        
        if not destination:
            flash('Destination not found.', 'danger')
            close_db_connection(conn, cursor)
            return redirect(url_for('admin_destinations'))
        
        if request.method == 'POST':
            country = request.form.get('country', '').strip()
            location = request.form.get('location', '').strip()
            category = request.form.get('category', '').strip()
            price_per_day = request.form.get('price_per_day', 0)
            minimum_days = request.form.get('minimum_days', 1)
            description = request.form.get('description', '').strip()
            featured = request.form.get('featured') == 'on'
            status = request.form.get('status', 'active')
            
            if not country or not location or not category:
                flash('Country, location, and category are required.', 'danger')
                close_db_connection(conn, cursor)
                return render_template('admin/destination_form.html', destination=destination)
            
            try:
                price_per_day = float(price_per_day) if price_per_day else 0
                minimum_days = int(minimum_days) if minimum_days else 1
            except ValueError:
                flash('Invalid price or days value.', 'danger')
                close_db_connection(conn, cursor)
                return render_template('admin/destination_form.html', destination=destination)
            
            # Handle image upload
            cover_image = destination['cover_image']
            if 'cover_image' in request.files:
                file = request.files['cover_image']
                if file and file.filename:
                    cover_image = upload_image(file, 'destinations')
                    if not cover_image:
                        flash('Failed to upload image. Please try again.', 'danger')
                        close_db_connection(conn, cursor)
                        return render_template('admin/destination_form.html', destination=destination)
            
            cursor.execute("""
                UPDATE destinations SET
                    country = %s,
                    location = %s,
                    category = %s,
                    price_per_day = %s,
                    minimum_days = %s,
                    description = %s,
                    cover_image = %s,
                    featured = %s,
                    status = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (country, location, category, price_per_day, minimum_days, 
                  description, cover_image, featured, status, destination_id))
            
            conn.commit()
            close_db_connection(conn, cursor)
            flash('Destination updated successfully!', 'success')
            return redirect(url_for('admin_destinations'))
        
        close_db_connection(conn, cursor)
        return render_template('admin/destination_form.html', destination=destination)
    except Exception as e:
        print(f"Edit destination error: {e}")
        close_db_connection(conn)
        flash('Error loading destination.', 'danger')
        return redirect(url_for('admin_destinations'))

@app.route('/admin/destinations/delete/<int:destination_id>')
@login_required
def admin_destination_delete(destination_id):
    """
    Delete a destination.
    """
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_destinations'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM destinations WHERE id = %s", (destination_id,))
        conn.commit()
        close_db_connection(conn, cursor)
        flash('Destination deleted successfully.', 'success')
    except Exception as e:
        print(f"Delete destination error: {e}")
        close_db_connection(conn)
        flash('Error deleting destination.', 'danger')
    
    return redirect(url_for('admin_destinations'))

# ============================================================
# ADMIN - PACKAGES CRUD
# ============================================================

@app.route('/admin/packages')
@login_required
def admin_packages():
    """
    List all packages.
    """
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return render_template('admin/packages.html', packages=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, badge, duration, price, image, featured, status, created_at 
            FROM packages 
            ORDER BY created_at DESC
        """)
        packages = cursor.fetchall()
        close_db_connection(conn, cursor)
        return render_template('admin/packages.html', packages=packages)
    except Exception as e:
        print(f"Packages list error: {e}")
        close_db_connection(conn)
        flash('Error loading packages.', 'danger')
        return render_template('admin/packages.html', packages=[])

@app.route('/admin/packages/create', methods=['GET', 'POST'])
@login_required
def admin_package_create():
    """
    Create a new package with image upload.
    """
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        badge = request.form.get('badge', '').strip()
        duration = request.form.get('duration', '').strip()
        price = request.form.get('price', 0)
        description = request.form.get('description', '').strip()
        featured = request.form.get('featured') == 'on'
        status = request.form.get('status', 'active')
        
        if not title or not duration:
            flash('Title and duration are required.', 'danger')
            return render_template('admin/package_form.html')
        
        try:
            price = float(price) if price else 0
        except ValueError:
            flash('Invalid price value.', 'danger')
            return render_template('admin/package_form.html')
        
        # Handle image upload
        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                image = upload_image(file, 'packages')
                if not image:
                    flash('Failed to upload image. Please try again.', 'danger')
                    return render_template('admin/package_form.html')
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection error.', 'danger')
            return render_template('admin/package_form.html')
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO packages 
                (title, badge, duration, price, description, image, featured, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (title, badge, duration, price, description, image, featured, status))
            
            package_id = cursor.fetchone()['id']
            conn.commit()
            close_db_connection(conn, cursor)
            flash('Package created successfully!', 'success')
            return redirect(url_for('admin_packages'))
        except Exception as e:
            print(f"Create package error: {e}")
            close_db_connection(conn)
            flash('Error creating package.', 'danger')
    
    return render_template('admin/package_form.html')

@app.route('/admin/packages/edit/<int:package_id>', methods=['GET', 'POST'])
@login_required
def admin_package_edit(package_id):
    """
    Edit an existing package with image upload.
    """
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_packages'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM packages WHERE id = %s", (package_id,))
        package = cursor.fetchone()
        
        if not package:
            flash('Package not found.', 'danger')
            close_db_connection(conn, cursor)
            return redirect(url_for('admin_packages'))
        
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            badge = request.form.get('badge', '').strip()
            duration = request.form.get('duration', '').strip()
            price = request.form.get('price', 0)
            description = request.form.get('description', '').strip()
            featured = request.form.get('featured') == 'on'
            status = request.form.get('status', 'active')
            
            if not title or not duration:
                flash('Title and duration are required.', 'danger')
                close_db_connection(conn, cursor)
                return render_template('admin/package_form.html', package=package)
            
            try:
                price = float(price) if price else 0
            except ValueError:
                flash('Invalid price value.', 'danger')
                close_db_connection(conn, cursor)
                return render_template('admin/package_form.html', package=package)
            
            # Handle image upload
            image = package['image']
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    image = upload_image(file, 'packages')
                    if not image:
                        flash('Failed to upload image. Please try again.', 'danger')
                        close_db_connection(conn, cursor)
                        return render_template('admin/package_form.html', package=package)
            
            cursor.execute("""
                UPDATE packages SET
                    title = %s,
                    badge = %s,
                    duration = %s,
                    price = %s,
                    description = %s,
                    image = %s,
                    featured = %s,
                    status = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (title, badge, duration, price, description, image, featured, status, package_id))
            
            conn.commit()
            close_db_connection(conn, cursor)
            flash('Package updated successfully!', 'success')
            return redirect(url_for('admin_packages'))
        
        close_db_connection(conn, cursor)
        return render_template('admin/package_form.html', package=package)
    except Exception as e:
        print(f"Edit package error: {e}")
        close_db_connection(conn)
        flash('Error loading package.', 'danger')
        return redirect(url_for('admin_packages'))

@app.route('/admin/packages/delete/<int:package_id>')
@login_required
def admin_package_delete(package_id):
    """
    Delete a package.
    """
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_packages'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM packages WHERE id = %s", (package_id,))
        conn.commit()
        close_db_connection(conn, cursor)
        flash('Package deleted successfully.', 'success')
    except Exception as e:
        print(f"Delete package error: {e}")
        close_db_connection(conn)
        flash('Error deleting package.', 'danger')
    
    return redirect(url_for('admin_packages'))

# ============================================================
# ADMIN - PACKAGE ITINERARY
# ============================================================

@app.route('/admin/packages/<int:package_id>/itinerary', methods=['GET', 'POST'])
@login_required
def admin_package_itinerary(package_id):
    """
    Manage package itinerary (package_destinations).
    """
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_packages'))
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, title FROM packages WHERE id = %s", (package_id,))
        package = cursor.fetchone()
        
        if not package:
            flash('Package not found.', 'danger')
            close_db_connection(conn, cursor)
            return redirect(url_for('admin_packages'))
        
        cursor.execute("""
            SELECT pd.id, pd.package_id, pd.destination_id, pd.day_order,
                   d.country, d.location, d.cover_image
            FROM package_destinations pd
            JOIN destinations d ON pd.destination_id = d.id
            WHERE pd.package_id = %s
            ORDER BY pd.day_order
        """, (package_id,))
        itinerary = cursor.fetchall()
        
        cursor.execute("""
            SELECT id, country, location, category 
            FROM destinations 
            WHERE status = 'active'
            ORDER BY country, location
        """)
        available_destinations = cursor.fetchall()
        
        if request.method == 'POST':
            destination_ids = request.form.getlist('destinations[]')
            day_orders = request.form.getlist('day_orders[]')
            
            cursor.execute("DELETE FROM package_destinations WHERE package_id = %s", (package_id,))
            
            for dest_id, day_order in zip(destination_ids, day_orders):
                if dest_id and day_order:
                    cursor.execute("""
                        INSERT INTO package_destinations (package_id, destination_id, day_order)
                        VALUES (%s, %s, %s)
                    """, (package_id, int(dest_id), int(day_order)))
            
            conn.commit()
            close_db_connection(conn, cursor)
            flash('Itinerary updated successfully!', 'success')
            return redirect(url_for('admin_packages'))
        
        close_db_connection(conn, cursor)
        return render_template('admin/package_itinerary.html',
                             package=package,
                             itinerary=itinerary,
                             available_destinations=available_destinations)
    except Exception as e:
        print(f"Itinerary error: {e}")
        close_db_connection(conn)
        flash('Error loading itinerary data.', 'danger')
        return redirect(url_for('admin_packages'))

# ============================================================
# ADMIN - DESTINATION GALLERY
# ============================================================

@app.route('/admin/destinations/<int:destination_id>/gallery', methods=['GET', 'POST'])
@login_required
def admin_destination_gallery(destination_id):
    """
    Manage destination gallery images.
    """
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_destinations'))
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, country, location FROM destinations WHERE id = %s", (destination_id,))
        destination = cursor.fetchone()
        
        if not destination:
            flash('Destination not found.', 'danger')
            close_db_connection(conn, cursor)
            return redirect(url_for('admin_destinations'))
        
        cursor.execute("""
            SELECT id, destination_id, image, display_order 
            FROM destination_gallery 
            WHERE destination_id = %s
            ORDER BY display_order
        """, (destination_id,))
        gallery = cursor.fetchall()
        
        if request.method == 'POST':
            display_order = request.form.get('display_order', 0)
            
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    image_url = upload_image(file, f'gallery/{destination_id}')
                    if image_url:
                        cursor.execute("""
                            INSERT INTO destination_gallery (destination_id, image, display_order)
                            VALUES (%s, %s, %s)
                        """, (destination_id, image_url, int(display_order)))
                        conn.commit()
                        flash('Image uploaded successfully!', 'success')
                    else:
                        flash('Failed to upload image.', 'danger')
                else:
                    flash('Please select an image file.', 'warning')
            else:
                flash('No image file provided.', 'warning')
            
            close_db_connection(conn, cursor)
            return redirect(url_for('admin_destination_gallery', destination_id=destination_id))
        
        close_db_connection(conn, cursor)
        return render_template('admin/destination_gallery.html',
                             destination=destination,
                             gallery=gallery)
    except Exception as e:
        print(f"Gallery error: {e}")
        close_db_connection(conn)
        flash('Error loading gallery.', 'danger')
        return redirect(url_for('admin_destinations'))

@app.route('/admin/gallery/delete/<int:gallery_id>')
@login_required
def admin_gallery_delete(gallery_id):
    """
    Delete a gallery image.
    """
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return redirect(url_for('admin_destinations'))
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT destination_id FROM destination_gallery WHERE id = %s", (gallery_id,))
        result = cursor.fetchone()
        
        if result:
            destination_id = result['destination_id']
            cursor.execute("DELETE FROM destination_gallery WHERE id = %s", (gallery_id,))
            conn.commit()
            flash('Image deleted from gallery.', 'success')
            close_db_connection(conn, cursor)
            return redirect(url_for('admin_destination_gallery', destination_id=destination_id))
        else:
            close_db_connection(conn, cursor)
            flash('Image not found.', 'danger')
            return redirect(url_for('admin_destinations'))
    except Exception as e:
        print(f"Delete gallery error: {e}")
        close_db_connection(conn)
        flash('Error deleting image.', 'danger')
        return redirect(url_for('admin_destinations'))

# ============================================================
# PUBLIC ROUTES - LANDING PAGE
# ============================================================

@app.route('/')
def index():
    """
    Landing page displaying featured destinations and packages.
    """
    conn = get_db_connection()
    if not conn:
        return render_template('index.html', 
                             featured_destinations=[],
                             popular_destinations=[],
                             featured_packages=[])
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, country, location, category, price_per_day, 
                   minimum_days, description, cover_image 
            FROM destinations 
            WHERE status = 'active' AND featured = true
            ORDER BY created_at DESC
            LIMIT 6
        """)
        featured_destinations = cursor.fetchall()
        
        cursor.execute("""
            SELECT DISTINCT ON (country) 
                   id, country, location, category, cover_image,
                   (SELECT COUNT(*) FROM destinations WHERE d.country = destinations.country) as total
            FROM destinations d
            WHERE status = 'active'
            ORDER BY country, created_at DESC
            LIMIT 4
        """)
        popular_destinations = cursor.fetchall()
        
        cursor.execute("""
            SELECT id, title, badge, duration, price, description, image 
            FROM packages 
            WHERE status = 'active' AND featured = true
            ORDER BY created_at DESC
            LIMIT 3
        """)
        featured_packages = cursor.fetchall()
        
        close_db_connection(conn, cursor)
        return render_template('index.html',
                             featured_destinations=featured_destinations,
                             popular_destinations=popular_destinations,
                             featured_packages=featured_packages)
    except Exception as e:
        print(f"Index error: {e}")
        close_db_connection(conn)
        return render_template('index.html',
                             featured_destinations=[],
                             popular_destinations=[],
                             featured_packages=[])

# ============================================================
# PUBLIC ROUTES - DESTINATIONS
# ============================================================

@app.route('/destinations')
def destinations():
    """
    Destinations page grouped by category.
    """
    conn = get_db_connection()
    if not conn:
        return render_template('destinations.html', categories={})
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT category 
            FROM destinations 
            WHERE status = 'active' AND category IS NOT NULL
            ORDER BY category
        """)
        categories = cursor.fetchall()
        
        destinations_by_category = {}
        for cat in categories:
            category_name = cat['category']
            cursor.execute("""
                SELECT id, country, location, category, price_per_day, 
                       minimum_days, description, cover_image 
                FROM destinations 
                WHERE status = 'active' AND category = %s
                ORDER BY country, location
            """, (category_name,))
            destinations_by_category[category_name] = cursor.fetchall()
        
        close_db_connection(conn, cursor)
        return render_template('destinations.html', categories=destinations_by_category)
    except Exception as e:
        print(f"Destinations error: {e}")
        close_db_connection(conn)
        return render_template('destinations.html', categories={})

# ============================================================
# PUBLIC ROUTES - SINGLE DESTINATION
# ============================================================

@app.route('/destination/<int:destination_id>')
def single_destination(destination_id):
    """
    Single destination page with details, gallery, and related destinations.
    """
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return render_template('single_destination.html', destination=None, gallery=[], related=[])
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, country, location, category, price_per_day, 
                   minimum_days, description, cover_image, featured
            FROM destinations 
            WHERE id = %s AND status = 'active'
        """, (destination_id,))
        destination = cursor.fetchone()
        
        if not destination:
            close_db_connection(conn, cursor)
            flash('Destination not found.', 'danger')
            return redirect(url_for('destinations'))
        
        cursor.execute("""
            SELECT id, image, display_order 
            FROM destination_gallery 
            WHERE destination_id = %s
            ORDER BY display_order
        """, (destination_id,))
        gallery = cursor.fetchall()
        
        cursor.execute("""
            SELECT id, country, location, category, price_per_day, 
                   description, cover_image 
            FROM destinations 
            WHERE status = 'active' 
              AND category = %s 
              AND id != %s
            ORDER BY created_at DESC
            LIMIT 4
        """, (destination['category'], destination_id))
        related = cursor.fetchall()
        
        close_db_connection(conn, cursor)
        return render_template('single_destination.html',
                             destination=destination,
                             gallery=gallery,
                             related=related)
    except Exception as e:
        print(f"Single destination error: {e}")
        close_db_connection(conn)
        flash('Error loading destination.', 'danger')
        return redirect(url_for('destinations'))

# ============================================================
# PUBLIC ROUTES - SINGLE PACKAGE
# ============================================================

@app.route('/package/<int:package_id>')
def single_package(package_id):
    """
    Single package page with details and itinerary.
    """
    conn = get_db_connection()
    if not conn:
        flash('Database connection error.', 'danger')
        return render_template('single_package.html', package=None, itinerary=[])
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, badge, duration, price, description, image, featured
            FROM packages 
            WHERE id = %s AND status = 'active'
        """, (package_id,))
        package = cursor.fetchone()
        
        if not package:
            close_db_connection(conn, cursor)
            flash('Package not found.', 'danger')
            return redirect(url_for('index'))
        
        cursor.execute("""
            SELECT pd.id, pd.day_order,
                   d.id as destination_id, d.country, d.location, 
                   d.category, d.description as destination_description,
                   d.cover_image
            FROM package_destinations pd
            JOIN destinations d ON pd.destination_id = d.id
            WHERE pd.package_id = %s AND d.status = 'active'
            ORDER BY pd.day_order
        """, (package_id,))
        itinerary = cursor.fetchall()
        
        close_db_connection(conn, cursor)
        return render_template('single_package.html',
                             package=package,
                             itinerary=itinerary)
    except Exception as e:
        print(f"Single package error: {e}")
        close_db_connection(conn)
        flash('Error loading package.', 'danger')
        return redirect(url_for('index'))

# ============================================================
# HEALTH CHECK
# ============================================================

@app.route('/health')
def health_check():
    """
    Health check endpoint for Render.
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database_connected': get_db_connection() is not None
    })

# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# ============================================================
# CONTEXT PROCESSORS
# ============================================================

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
