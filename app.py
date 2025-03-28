from flask import Flask, render_template, send_file, url_for, request
from flask_caching import Cache
import os

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app) 
app.config['DATA_FOLDER'] = 'media'
app.config['ITEMS_PER_PAGE'] = 9  # Number of items per page

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = app.config['ITEMS_PER_PAGE']
    
    files = cache.get('files')
    if not files:
        if os.path.exists(app.config['DATA_FOLDER']):
            # Get all files and sort them by type (images first, then videos)
            all_files = []
            for filename in os.listdir(app.config['DATA_FOLDER']):
                if allowed_file(filename):
                    file_type = 'video' if filename.rsplit('.', 1)[1].lower() in {'mp4', 'webm', 'mov'} else 'image'
                    all_files.append({
                        'name': filename,
                        'type': file_type,
                        'path': url_for('serve_file', filename=filename),
                        'download_path': url_for('download_file', filename=filename)
                    })
        
        # Sort files: images first, then videos
        files = sorted(all_files, key=lambda x: (x['type'] == 'video', x['name']))
        cache.set('files', files)
    
    # Calculate pagination
    total_items = len(files)
    total_pages = (total_items + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    
    # Get items for current page
    paginated_files = files[start_idx:end_idx]
    
    return render_template('index.html', 
                         files=paginated_files,
                         current_page=page,
                         total_pages=total_pages,
                         total_items=total_items)

@app.route('/data/<filename>')
def download_file(filename):
    return send_file(
        os.path.join(app.config['DATA_FOLDER'], filename),
        as_attachment=True
    )

@app.route('/data/<filename>')
def serve_file(filename):
    return send_file(
        os.path.join(app.config['DATA_FOLDER'], filename)
    )

if __name__ == '__main__':
    app.run(debug=True) 