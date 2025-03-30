from flask import Flask, render_template, send_file, url_for, request, flash, redirect
from flask_caching import Cache
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from models import db, User, Media
from forms import LoginForm, RegistrationForm, UploadForm
import uuid

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///media_gallery.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DATA_FOLDER'] = os.getenv('DATA_FOLDER')
app.config['ITEMS_PER_PAGE'] = 9

# Initialize extensions
db.init_app(app)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create database tables
with app.app_context():
    db.create_all()

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
        'name': media.filename,
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

if __name__ == '__main__':
    app.run(debug=True) 