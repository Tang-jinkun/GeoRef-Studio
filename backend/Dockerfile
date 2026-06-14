FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_INDEX_URL=http://mirrors.tencent.com/pypi/simple
ENV PIP_TRUSTED_HOST=mirrors.tencent.com
ENV PIP_DEFAULT_TIMEOUT=120

WORKDIR /app

RUN sed -i \
      -e 's|http://deb.debian.org/debian|http://mirrors.tencent.com/debian|g' \
      -e 's|http://deb.debian.org/debian-security|http://mirrors.tencent.com/debian-security|g' \
      /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Retries=5 update \
    && apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
      gdal-bin \
      libgdal-dev \
      libgl1 \
      libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
