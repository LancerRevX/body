FROM ubuntu@sha256:b7f48194d4d8b763a478a621cdc81c27be222ba2206ca3ca6bc42b49685f3d9e

RUN apt update
RUN apt install python3 python3-venv -y
RUN apt install apache2 libapache2-mod-wsgi-py3 -y

# for psycopg2
RUN apt install gcc libpq-dev python3-dev -y

# for django-tailwind
RUN apt install nodejs npm -y

WORKDIR /var/www/html/
RUN python3 -m venv .venv
ENV PATH="/var/www/html/.venv/bin/:$PATH"

RUN a2dissite 000-default

COPY <<EOF /etc/apache2/sites-available/django.conf
Alias /robots.txt /var/www/html/static/robots.txt
Alias /favicon.ico /var/www/html/static/favicon.ico

Alias /static/ /var/www/html/static/

<Directory /var/www/html/static>
Require all granted
</Directory>

WSGIScriptAlias / /var/www/html/nikitakirenkov_ru/wsgi.py
WSGIPythonHome /var/www/html/.venv
WSGIPythonPath /var/www/html/

<Directory /var/www/html/nikitakirenkov_ru>
<Files wsgi.py>
Require all granted
</Files>
</Directory>
EOF

RUN a2ensite django

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
ENV NPM_BIN_PATH=/usr/bin/npm
ENV STATIC_ROOT=/var/www/html/static/
RUN python manage.py tailwind install
RUN python manage.py tailwind build
RUN python manage.py collectstatic

COPY <<EOF start.sh
python manage.py migrate
apachectl -DFOREGROUND
EOF

RUN chmod +x start.sh
CMD bash -c ./start.sh