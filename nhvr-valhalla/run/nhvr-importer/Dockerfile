# Tools image for the NHVR pipeline: GDAL (ogr2ogr + Python bindings),
# pyosmium (PBF rewrite) and the PostgreSQL client (staging-table swaps).
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.12.4

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      python3-venv \
      postgresql-client \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/nhvr

# --system-site-packages keeps the GDAL Python bindings that ship with the
# base image; GDAL itself is deliberately not installed from PyPI.
COPY requirements.txt ./
RUN python3 -m venv --system-site-packages /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
ENV PATH="/opt/venv/bin:$PATH"

COPY import-nhvr.py load-nhvr.sh entrypoint.sh ./
RUN chmod +x entrypoint.sh load-nhvr.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["help"]
