FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    DEMO_MODE=1 \
    PORT=7860
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt
COPY . /app
# Ensure a valid port is set even if upstream envs are empty; prefer $PORT if provided by platform.
CMD bash -lc "PORT=${PORT:-7860}; export STREAMLIT_SERVER_PORT=$PORT; exec streamlit run app/streamlit_app.py --server.address=0.0.0.0 --server.port=$PORT"
