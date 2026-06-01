FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN useradd -M app


COPY --chown=app:app  ./src/ /app/
COPY --chmod=755 ./entrypoint.sh /entrypoint.sh

WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

USER app

ENTRYPOINT [ "/entrypoint.sh" ]

CMD ["uwsgi", "uwsgi.ini"]

