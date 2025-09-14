# Multi-stage build for Kali MCP Server
FROM kalilinux/kali-rolling AS base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd -r kalimcp && useradd -r -g kalimcp -d /opt/kalimcp -s /bin/bash kalimcp

# Install system dependencies and security tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
        curl \
        wget \
        gnupg \
        lsb-release \
        # Core security tools
        nmap \
        sqlmap \
        hydra \
        john \
        nikto \
        aircrack-ng \
        metasploit-framework \
        # Additional useful tools
        gobuster \
        dirb \
        wfuzz \
        cewl \
        hashcat \
        crunch \
        medusa \
        ncrack \
        enum4linux \
        samba-common-bin \
        rpcbind \
        ldap-utils \
        dnsutils \
        whois \
        traceroute \
        iputils-ping \
        net-tools \
        iproute2 \
        # Development tools (minimal)
        git \
        vim-tiny \
        # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Create application directory
WORKDIR /opt/kalimcp

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install Python dependencies
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .
COPY tests/ tests/

# Create necessary directories
RUN mkdir -p /tmp/kali-mcp /opt/logs && \
    chown -R kalimcp:kalimcp /opt/kalimcp /tmp/kali-mcp /opt/logs

# Security hardening
RUN chmod 755 /opt/kalimcp && \
    chmod 644 /opt/kalimcp/server.py && \
    chmod 755 /opt/kalimcp/tests

# Switch to non-root user
USER kalimcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expose ports
EXPOSE 5000 8000

# Set working directory
WORKDIR /opt/kalimcp

# Default command
CMD ["python3", "server.py"]

# Labels for metadata
LABEL maintainer="Kali MCP Server Team"
LABEL version="1.0.0"
LABEL description="Model Context Protocol server for Kali Linux security tools"
LABEL org.opencontainers.image.source="https://github.com/your-org/kali-mcp-server"
LABEL org.opencontainers.image.licenses="MIT"