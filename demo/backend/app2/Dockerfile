FROM php:apache


RUN apt update -y && apt install 7zip

COPY ./src /var/www/html

RUN chown -R www-data:www-data /var/www/html/storage

