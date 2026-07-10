FROM ubuntu:24.04

RUN apt update
RUN apt install python3 python3-venv -y
RUN apt install apache2 libapache2-mod-wsgi-py3 -y

# for psycopg2
RUN apt install gcc libpq-dev python3-dev -y

# for django-tailwind
RUN apt install nodejs npm -y

RUN apt install pipenv -y

COPY <<EOF /etc/apache2/sites-available/django.conf
Alias /robots.txt /var/www/html/static/robots.txt
Alias /favicon.ico /var/www/html/static/favicon.ico

Alias /static/ /var/www/html/static/

<Directory /var/www/html/static>
    Require all granted
</Directory>

WSGIScriptAlias / /var/www/html/body/nikitakirenkov_ru/wsgi.py
WSGIPythonHome /var/www/html/body/.venv
WSGIPythonPath /var/www/html/body/

<Directory /var/www/html/body/nikitakirenkov_ru>
    <Files wsgi.py>
        Require all granted
    </Files>
</Directory>
EOF

RUN a2dissite 000-default
RUN a2ensite django

WORKDIR /var/www/html/body
COPY Pipfile Pipfile.lock .
ENV PIPENV_VENV_IN_PROJECT=1
RUN pipenv install --python 3.12
ENV PATH="/var/www/html/body/.venv/bin/:$PATH"

COPY . .
ENV STATIC_ROOT=/var/www/html/static/
ENV DJANGO_LOG_PATH="/var/www/html/django.log"
RUN python manage.py tailwind install
RUN python manage.py tailwind build
RUN python manage.py collectstatic

# COPY <<EOF start.sh
# python manage.py migrate
# CMD [ "python", "manage.py runserver" ]
RUN chown www-data:www-data /var/www/html/django.log
RUN a2enmod wsgi
CMD ["apachectl",  "-DFOREGROUND"]

# EOF

# RUN chmod +x start.sh
# CMD bash -c ./start.sh