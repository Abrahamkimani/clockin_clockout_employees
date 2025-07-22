#!/bin/bash

# Mental Health Wellness Center - Employee Tracking System
# Development startup script

echo "🏥 Mental Health Wellness Center - Employee Tracking System"
echo "=========================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please create one with your database credentials."
    echo "📄 See .env.example for reference"
    exit 1
fi

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if none exists (optional)
echo "👤 Checking for superuser..."
python manage.py shell -c "
from authentication.models import User
if not User.objects.filter(is_superuser=True).exists():
    print('No superuser found. Please create one:')
    exit(1)
else:
    print('✅ Superuser exists')
"

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create sample data (optional)
read -p "🔧 Create sample data for testing? (y/n): " create_sample
if [[ $create_sample == "y" || $create_sample == "Y" ]]; then
    echo "📝 Creating sample data..."
    python manage.py create_sample_data --users 3 --clients 5 --sessions 10
    echo "✅ Sample data created"
fi

echo ""
echo "🚀 Starting development server..."
echo "📱 API will be available at: http://localhost:8000/"
echo "🔧 Admin interface at: http://localhost:8000/admin/"
echo "📚 API docs at: http://localhost:8000/api/docs/"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the development server
python manage.py runserver
