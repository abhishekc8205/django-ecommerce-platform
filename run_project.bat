echo.
echo Running database migrations...
python manage.py migrate

echo.
echo Creating admin superuser if it does not exist...
python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@gmail.com','12345')"

echo.
echo Starting Django server...
echo Open http://127.0.0.1:8000/
echo.
python manage.py runserver 0.0.0.0:8000