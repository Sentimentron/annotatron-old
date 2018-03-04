python3 manage.py collectstatic --noinput
python3 manage.py migrate

gunicorn --workers 2 \
         --timeout 15 \
         --bind 0.0.0.0:4420 \
         annotatron.wsgi:application

