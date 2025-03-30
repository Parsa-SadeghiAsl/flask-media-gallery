from flask import Flask, render_template, send_file, url_for, request, flash, redirect
from flask_caching import Cache
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from models import db, User, Media
from forms import LoginForm, RegistrationForm, UploadForm, MediaEditForm, ProfileEditForm
from utils import admin_required
import uuid

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///media_gallery.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DATA_FOLDER'] = os.getenv('DATA_FOLDER')
app.config['ITEMS_PER_PAGE'] = 9

# Admin credentials
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'superadmin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'securepassword123')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@yourdomain.com')

# Initialize extensions
db.init_app(app)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create database tables
with app.app_context():
    db.create_all()
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(username=ADMIN_USERNAME).first()
    if not admin:
        admin = User(username=ADMIN_USERNAME, email=ADMIN_EMAIL, is_admin=True)
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        print(f'Admin user created with username: {ADMIN_USERNAME} and password: {ADMIN_PASSWORD}')

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = app.config['ITEMS_PER_PAGE']
    
    # Get all media files
    query = Media.query
    
    # Get paginated files
    pagination = query.order_by(Media.uploaded_at.desc()).paginate(page=page, per_page=per_page)
    files = [{
        'name': media.original_filename,
        'title': media.title,
        'type': media.file_type,
        'path': url_for('serve_file', filename=media.filename),
        'download_path': url_for('download_file', filename=media.filename),
        'uploader': media.owner.username,
        'upload_date': media.uploaded_at.strftime('%Y-%m-%d %H:%M')
    } for media in pagination.items]
    
    return render_template('index.html',
                         files=files,
                         pagination=pagination,
                         show_auth_message=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        login_user(user)
        flash('Logged in successfully!', 'success')
        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if file and allowed_file(file.filename):
            # Generate a unique filename
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4()}.{ext}"
            
            # Save the file
            file.save(os.path.join(app.config['DATA_FOLDER'], filename))
            
            # Create media record
            file_type = 'video' if ext in {'mp4', 'webm', 'mov'} else 'image'
            media = Media(
                title=form.title.data,
                filename=filename,
                original_filename=file.filename,
                file_type=file_type,
                user_id=current_user.id
            )
            db.session.add(media)
            db.session.commit()
            
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid file type!', 'danger')
    
    return render_template('upload.html', form=form)

@app.route('/data/<filename>')
def download_file(filename):
    # Anyone can download files now
    media = Media.query.filter_by(filename=filename).first_or_404()
    return send_file(
        os.path.join(app.config['DATA_FOLDER'], filename),
        as_attachment=True,
        download_name=media.original_filename
    )

@app.route('/data/<filename>')
def serve_file(filename):
    # Anyone can view files now
    media = Media.query.filter_by(filename=filename).first_or_404()
    return send_file(os.path.join(app.config['DATA_FOLDER'], filename))

# Admin routes
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    # Get statistics for the dashboard
    user_count = User.query.count()
    media_count = Media.query.count()
    image_count = Media.query.filter_by(file_type='image').count()
    video_count = Media.query.filter_by(file_type='video').count()
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_count = User.query.filter(User.created_at >= week_ago).count()
    
    return render_template('admin/dashboard.html',
                          user_count=user_count,
                          media_count=media_count,
                          image_count=image_count,
                          video_count=video_count,
                          new_users_count=new_users_count)

@app.route('/admin/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_profile():
    form = ProfileEditForm(original_username=current_user.username, original_email=current_user.email)
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('admin_profile'))
        
        # Update user information
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        # Update password if provided
        if form.new_password.data:
            current_user.set_password(form.new_password.data)
            
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('admin_profile'))
    
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('admin/profile.html', form=form)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    per_page = 20  # More users per page in admin view
    
    pagination = User.query.order_by(User.username).paginate(page=page, per_page=per_page)
    
    return render_template('admin/users.html', 
                          users=pagination.items,
                          pagination=pagination)

@app.route('/admin/users/<int:user_id>/toggle-role')
@login_required
@admin_required
def admin_toggle_role(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from removing their own admin privileges
    if user.id == current_user.id and user.is_admin:
        flash('You cannot remove your own admin privileges.', 'danger')
        return redirect(url_for('admin_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    if user.is_admin:
        flash(f'User {user.username} is now an admin.', 'success')
    else:
        flash(f'User {user.username} is no longer an admin.', 'success')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/delete')
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin_users'))
    
    # Delete all media files
    for media in user.media_files:
        try:
            os.remove(os.path.join(app.config['DATA_FOLDER'], media.filename))
        except:
            pass
        db.session.delete(media)
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} and all their media have been deleted.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/media')
@login_required
@admin_required
def admin_media():
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Adjust for admin panel
    
    media_type = request.args.get('type', '')
    sort_by = request.args.get('sort', 'newest')
    
    # Base query
    query = Media.query
    
    # Apply filters
    if media_type in ['image', 'video']:
        query = query.filter_by(file_type=media_type)
    
    # Apply sorting
    if sort_by == 'oldest':
        query = query.order_by(Media.uploaded_at.asc())
    elif sort_by == 'title_asc':
        query = query.order_by(Media.title.asc())
    elif sort_by == 'title_desc':
        query = query.order_by(Media.title.desc())
    else:  # newest
        query = query.order_by(Media.uploaded_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    media_files = [{
        'id': media.id,
        'title': media.title,
        'file_type': media.file_type,
        'url': url_for('serve_file', filename=media.filename),
        'uploader': media.owner.username,
        'upload_date': media.uploaded_at.strftime('%Y-%m-%d %H:%M')
    } for media in pagination.items]
    
    return render_template('admin/media.html', 
                          media_files=media_files,
                          pagination=pagination)

@app.route('/admin/media/<int:media_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_media(media_id):
    media = Media.query.get_or_404(media_id)
    form = MediaEditForm()
    
    if form.validate_on_submit():
        media.title = form.title.data
        db.session.commit()
        flash('Media title has been updated.', 'success')
        return redirect(url_for('admin_media'))
    
    if request.method == 'GET':
        form.title.data = media.title
    
    url = url_for('serve_file', filename=media.filename)
    
    return render_template('admin/edit_media.html',
                          media=media,
                          form=form,
                          url=url)

@app.route('/admin/media/<int:media_id>/delete')
@login_required
@admin_required
def admin_delete_media(media_id):
    media = Media.query.get_or_404(media_id)
    
    # Delete the physical file
    try:
        os.remove(os.path.join(app.config['DATA_FOLDER'], media.filename))
    except:
        pass
    
    # Delete the database record
    db.session.delete(media)
    db.session.commit()
    
    flash('Media has been deleted.', 'success')
    return redirect(url_for('admin_media'))

@app.route('/admin/users/<int:user_id>/media')
@login_required
@admin_required
def admin_user_media(user_id):
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    pagination = Media.query.filter_by(user_id=user.id).order_by(Media.uploaded_at.desc()).paginate(page=page, per_page=per_page)
    
    media_files = [{
        'id': media.id,
        'title': media.title,
        'file_type': media.file_type,
        'url': url_for('serve_file', filename=media.filename),
        'uploader': user.username,
        'upload_date': media.uploaded_at.strftime('%Y-%m-%d %H:%M')
    } for media in pagination.items]
    
    return render_template('admin/media.html',
                          media_files=media_files,
                          pagination=pagination,
                          user=user)

if __name__ == '__main__':
    app.run(debug=True) 