@echo off
REM Mental Health Wellness Center - Employee Tracking System
REM Windows development startup script

echo 🏥 Mental Health Wellness Center - Employee Tracking System
echo ==========================================================

REM Check if virtual environment exists
if not exist "venv" (
    echo ⚠️  Virtual environment not found. Creating one...
    python -m venv venv
    echo ✅ Virtual environment created
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found. Please create one with your database credentials.
    echo 📄 See .env.example for reference
    pause
    exit /b 1
)

REM Run migrations
echo 🗄️  Running database migrations...
python manage.py makemigrations
python manage.py migrate

REM Collect static files
echo 📁 Collecting static files...
python manage.py collectstatic --noinput

REM Create sample data (optional)
set /p create_sample="🔧 Create sample data for testing? (y/n): "
if /i "%create_sample%"=="y" (
    echo 📝 Creating sample data...
    python manage.py create_sample_data --users 3 --clients 5 --sessions 10
    echo ✅ Sample data created
)

echo.
echo 🚀 Starting development server...
echo 📱 API will be available at: http://localhost:8000/
echo 🔧 Admin interface at: http://localhost:8000/admin/
echo 📚 API docs at: http://localhost:8000/api/docs/
echo.
echo 🛑 Press Ctrl+C to stop the server
echo.

REM Start the development server
python manage.py runserver

pause
