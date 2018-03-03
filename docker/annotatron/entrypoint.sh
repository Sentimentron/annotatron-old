python3 manage.py collectstatic --noinput

gunicorn --workers 15 \
         --timeout 15 \
         --bind 0.0.0.0:4420 \
         annotatron.wsgi:application

