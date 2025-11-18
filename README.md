# HRMS - Human Resource Management System

A comprehensive Human Resource Management System built with Django REST Framework, MySQL database, and JWT authentication.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Environment Configuration](#environment-configuration)
- [Running the Development Server](#running-the-development-server)
- [API Endpoints](#api-endpoints)
- [Admin Panel](#admin-panel)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: 3.8 or higher
- **MySQL**: 8.0 or higher
- **pip**: Python package manager
- **Virtual Environment**: (recommended) venv or virtualenv

### Verify Prerequisites

```bash
# Check Python version
python --version  # Should be 3.8+

# Check MySQL version
mysql --version  # Should be 8.0+

# Check pip version
pip --version
```

## 📁 Project Structure

```
hrms/
├── hrms/                  # Django project settings
│   ├── __init__.py
│   ├── settings.py        # Main settings file
│   ├── urls.py            # Root URL configuration
│   ├── wsgi.py            # WSGI config for deployment
│   └── asgi.py            # ASGI config for async
├── core/                  # Core Django app
│   ├── migrations/        # Database migrations
│   ├── __init__.py
│   ├── admin.py           # Admin panel configuration
│   ├── apps.py            # App configuration
│   ├── models.py          # Database models
│   ├── views.py           # API views
│   ├── urls.py            # App URL routes
│   └── tests.py           # Unit tests
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## 🚀 Installation

### Step 1: Create and Activate Virtual Environment

**Windows:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

**Linux/Mac:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

After activation, you should see `(venv)` in your terminal prompt.

### Step 2: Install Dependencies

```bash
# Upgrade pip (recommended)
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

**Note:** If you encounter issues installing `mysqlclient` on Windows, you may need to:
1. Install MySQL Connector/C from [MySQL Downloads](https://dev.mysql.com/downloads/connector/c/)
2. Or use `pip install mysqlclient` with pre-built wheels
3. Alternative: Use `pip install pymysql` and configure it in settings.py (not recommended for production)

### Step 3: Create MySQL Database

Open MySQL command line or MySQL Workbench and run:

```sql
CREATE DATABASE hrms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Or using MySQL command line:
```bash
mysql -u root -p
# Enter your MySQL password when prompted
CREATE DATABASE hrms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

## 🔐 Environment Configuration

### Step 1: Create .env File

Copy the example environment file:
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### Step 2: Configure Environment Variables

Open `.env` file and update the following values:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=hrms_db
DB_USER=root
DB_PASSWORD=your_actual_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

**Important:**
- Generate a secure SECRET_KEY using:
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- Replace `your_actual_mysql_password` with your MySQL root password
- Never commit the `.env` file to version control

## 🗄️ Database Setup

### Step 1: Run Migrations

Create database tables:
```bash
python manage.py makemigrations
python manage.py migrate
```

This will create all necessary Django tables including:
- User authentication tables
- Session tables
- Admin tables
- Core app tables (when models are added)

### Step 2: Create Superuser

Create an admin user to access the Django admin panel:
```bash
python manage.py createsuperuser
```

You will be prompted to enter:
- Username
- Email address (optional)
- Password (twice for confirmation)

**Example:**
```
Username: admin
Email address: admin@hrms.com
Password: ********
Password (again): ********
Superuser created successfully.
```

## ▶️ Running the Development Server

Start the Django development server:
```bash
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/`

You should see output like:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

## 🌐 API Endpoints

### Authentication Endpoints

- **Obtain JWT Token**: `POST /api/token/`
  - Body: `{"username": "your_username", "password": "your_password"}`
  - Returns: `{"access": "token", "refresh": "token"}`

- **Refresh JWT Token**: `POST /api/token/refresh/`
  - Body: `{"refresh": "your_refresh_token"}`
  - Returns: `{"access": "new_access_token"}`

- **Verify JWT Token**: `POST /api/token/verify/`
  - Body: `{"token": "your_token"}`
  - Returns: `{}` if valid

### Core Endpoints

- **Health Check**: `GET /api/health/`
  - No authentication required
  - Returns: `{"status": "healthy", "message": "HRMS API is running successfully", "version": "1.0.0"}`

### Using JWT Tokens

Include the token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

## 👨‍💼 Admin Panel

Access the Django admin panel at:
```
http://127.0.0.1:8000/admin
```

Login with the superuser credentials you created earlier.

The admin panel allows you to:
- Manage users and permissions
- View and manage database records
- Access Django admin features

## ✅ Verification Checklist

After setup, verify the following:

- [ ] `python manage.py runserver` starts without errors
- [ ] Can access `http://127.0.0.1:8000/admin`
- [ ] Can login with superuser credentials
- [ ] Database shows Django default tables (check MySQL)
- [ ] Health check endpoint works: `http://127.0.0.1:8000/api/health/`
- [ ] JWT token endpoint works: `POST http://127.0.0.1:8000/api/token/`

## 🔍 Troubleshooting

### Issue: `mysqlclient` installation fails on Windows

**Solution:**
1. Download MySQL Connector/C from [MySQL Downloads](https://dev.mysql.com/downloads/connector/c/)
2. Install it
3. Add MySQL bin directory to PATH
4. Try installing again: `pip install mysqlclient`

Alternative: Use `pymysql` (not recommended for production):
```python
# In settings.py, add at the top:
import pymysql
pymysql.install_as_MySQLdb()
```

### Issue: Database connection error

**Check:**
1. MySQL service is running
2. Database `hrms_db` exists
3. `.env` file has correct credentials
4. User has proper permissions:
   ```sql
   GRANT ALL PRIVILEGES ON hrms_db.* TO 'root'@'localhost';
   FLUSH PRIVILEGES;
   ```

### Issue: `ModuleNotFoundError: No module named 'dotenv'`

**Solution:**
```bash
pip install python-dotenv
```

### Issue: `SECRET_KEY` error

**Solution:**
- Ensure `.env` file exists in project root
- Check that `SECRET_KEY` is set in `.env`
- Verify `python-dotenv` is installed

### Issue: Migration errors

**Solution:**
```bash
# Reset migrations (WARNING: This deletes data)
python manage.py migrate --run-syncdb

# Or check for specific errors
python manage.py makemigrations --dry-run
```

### Issue: Port 8000 already in use

**Solution:**
```bash
# Use a different port
python manage.py runserver 8001
```

## 📝 Next Steps

This is Phase 1 of the HRMS project. Future phases will include:
- Employee management models
- Department and organization structure
- Attendance tracking
- Leave management
- Payroll system
- Performance reviews
- And more...

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [JWT Authentication](https://django-rest-framework-simplejwt.readthedocs.io/)
- [MySQL Documentation](https://dev.mysql.com/doc/)

## 📄 License

This project is part of a university course project.

## 👥 Support

For issues or questions, please refer to the project documentation or contact the development team.

---

**Happy Coding! 🚀**

