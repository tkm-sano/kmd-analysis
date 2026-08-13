FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /workspace

RUN apt-get update \
    && apt-get install --no-install-recommends --yes git osmium-tool \
    && rm -rf /var/lib/apt/lists/*

COPY docker/analysis/requirements.txt /tmp/traffic-analysis-requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r /tmp/traffic-analysis-requirements.txt

CMD ["bash"]
