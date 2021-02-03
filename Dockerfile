FROM python:3.8
ENV PORT 8080
EXPOSE 8080

WORKDIR /usr/src/workflows_engine
COPY workflows_engine ./
RUN pip install -r pip-requirements.txt; \
    pip install .

WORKDIR /usr/src/app

COPY app.py requirements.txt ./

RUN ls; pip install -r ./requirements.txt
ENV FLASK_APP app.py
ENV FLASK_RUN_PORT 8080

ENTRYPOINT ["flask"]
CMD ["run"]