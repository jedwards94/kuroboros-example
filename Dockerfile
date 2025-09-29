FROM python:3.13-slim

RUN addgroup --gid 1001 app && \
    adduser \
    --disabled-password \
    --gecos "" \
    --home /home/app \
    --ingroup app \
    --uid 1001 \
    app

WORKDIR /home/app/operator
RUN chown -R app:app /home/app
ADD . .
RUN pip install .
WORKDIR /home/app/operator
USER 1001

ENTRYPOINT [ "kuroboros" ]

