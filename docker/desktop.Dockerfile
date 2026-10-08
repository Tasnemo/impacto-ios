FROM ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55

ENV DEBIAN_FRONTEND=noninteractive
COPY .github/scripts/install-desktop-deps.sh /tmp/install-desktop-deps.sh
RUN bash /tmp/install-desktop-deps.sh \
    && python3 -m venv /opt/cmake \
    && /opt/cmake/bin/pip install cmake==3.31.10 \
    && rm -rf /var/lib/apt/lists/* /tmp/install-desktop-deps.sh
ENV PATH="/opt/cmake/bin:${PATH}"
WORKDIR /work
