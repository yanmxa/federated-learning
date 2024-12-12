FROM flwr/superlink:1.13.1

WORKDIR /app
COPY pyproject.toml .
RUN sed -i 's/.*flwr\[simulation\].*//' pyproject.toml \
  && python -m pip install -U --no-cache-dir .

ENTRYPOINT ["flower-superlink"]