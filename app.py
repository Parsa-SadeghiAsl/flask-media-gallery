from flask import Flask, render_template, send_file, url_for
from flask_caching import Cache
import os

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app) 
app.config['DATA_FOLDER'] = 'media'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    files = []
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
    
    return render_template('index.html', files=files)

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