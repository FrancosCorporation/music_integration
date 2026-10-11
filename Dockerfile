FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 app \
    && mkdir -p /data /sessions \
    && chown -R app:app /data /sessions

COPY --chown=app:app . /app
USER app
EXPOSE 8501

CMD ["streamlit", "run", "social_automation/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
