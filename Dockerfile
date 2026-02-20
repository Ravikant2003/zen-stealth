FROM ghcr.io/stephanlensky/swayvnc-chrome:latest

USER root

# 1. Clean up and install dependencies for the Sid-based image
# We remove the google-chrome repo which has GPG issues in the base
# We use --force-overwrite to handle the Debian Sid t64 package transition (libgtk-3-0 conflict)
RUN rm -f /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends -o Dpkg::Options::="--force-overwrite" \
    wget \
    gnupg \
    bzip2 \
    xz-utils \
    libnss3 \
    libcups2t64 \
    libgbm1 \
    libasound2t64 \
    libpangocairo-1.0-0 \
    libgtk-3-0t64 \
    ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Install msttcorefonts (enable contrib/non-free for Sid)
RUN echo "deb http://deb.debian.org/debian sid contrib non-free" > /etc/apt/sources.list.d/contrib.list && \
    echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections && \
    apt-get update && apt-get install -y ttf-mscorefonts-installer && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. Install Zen Browser (x86_64 for amd64 platform)
# We use .tar.xz now as Zen stopped using .tar.bz2 for Linux
RUN ZEN_URL="https://github.com/zen-browser/desktop/releases/latest/download/zen.linux-x86_64.tar.xz" && \
    mkdir -p /opt/zen && \
    wget --no-check-certificate -O /tmp/zen.tar.xz $ZEN_URL && \
    tar -xJC /opt/zen --strip-components=1 -f /tmp/zen.tar.xz && \
    ln -s /opt/zen/zen /usr/local/bin/zen-browser && \
    rm /tmp/zen.tar.xz

# 4. User's Template Logic (XWayland, GPU, etc.)
ARG ENABLE_XWAYLAND=true
RUN if [ "$ENABLE_XWAYLAND" = "true" ]; then \
    apt-get update && apt-get -y install -o Dpkg::Options::="--force-overwrite" xwayland && \
    echo "Xwayland installed."; \
    fi

RUN if [ "$ENABLE_XWAYLAND" = "true" ]; then \
    sed -i '/^export XDG_RUNTIME_DIR/i \
    export DISPLAY=${DISPLAY:-:0}' \
    /entrypoint_user.sh; \
    fi

RUN if [ "$ENABLE_XWAYLAND" = "true" ]; then \
    sed -i 's/xwayland disable/xwayland enable/' \
    /home/$DOCKER_USER/.config/sway/config; \
    fi

ARG SWAY_UNSUPPORTED_GPU=true
RUN if [ "$SWAY_UNSUPPORTED_GPU" = "true" ]; then \
    sed -i 's/sway &/sway --unsupported-gpu \&/' /entrypoint_user.sh; \
    fi

# 5. Application Setup (UV)
ENV PYTHONUNBUFFERED=1
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app
RUN chown $DOCKER_USER:$DOCKER_USER /app

USER $DOCKER_USER
RUN uv python install 3.12

# Copy dependency files
COPY --chown=$DOCKER_USER:$DOCKER_USER pyproject.toml uv.lock* /app/
RUN uv sync --no-install-project

# Copy project source
COPY --chown=$DOCKER_USER:$DOCKER_USER . /app
ENV PATH="/app/.venv/bin:$PATH"
RUN uv sync

USER root
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/app/.venv/bin/python", "ghost_browser.py"]
