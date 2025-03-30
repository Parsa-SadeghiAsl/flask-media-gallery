# Flask Media Gallery

A web application for sharing and managing media files with user authentication and admin controls.

## Features

- User authentication system (register, login, logout)
- Upload personal media files with custom titles
- View all media in a responsive gallery layout
- Download any media file
- Dark/light theme toggle
- Admin panel for user and media management
- Responsive design for all devices
- Pagination for both gallery and admin views
- Support for common image formats (PNG, JPG, JPEG, GIF) and video formats (MP4, WEBM, MOV)

## Setup

### Prerequisites
- Python 3.7+
- pip

### Installation

1. Clone the repository or download the source code

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following configuration:
```
SECRET_KEY=your-secure-secret-key
DATABASE_URL=sqlite:///media_gallery.db

# Admin credentials (used when creating the initial admin account)
ADMIN_USERNAME=youradmin
ADMIN_PASSWORD=your-secure-password
ADMIN_EMAIL=admin@yourdomain.com
```

5. Run the application:
```bash
python app.py
```

6. Open your web browser and navigate to `http://localhost:5000`

### First Login

On first startup, the application will automatically create an admin account using the credentials specified in your `.env` file. You can log in with these credentials and access the admin panel.

## Admin Panel

The admin panel allows you to:

- View statistics about users and media
- Manage users (create/delete users, toggle admin status)
- Manage all media files (edit titles, delete files)
- Change admin credentials

To access the admin panel, log in with admin credentials and click the "Admin" dropdown in the navigation bar.

## User Management

Regular users can:
- Register for an account
- Upload their own media files
- View all media files in the gallery
- Download any media file
