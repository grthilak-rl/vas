# Dockerfile.janus
FROM ubuntu:18.04

# Set DEBIAN_FRONTEND to noninteractive to avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install dependencies, including python3-pip for the Meson install
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    build-essential \
    libmicrohttpd-dev \
    libjansson-dev \
    libssl-dev \
    libsrtp-dev \
    libsofia-sip-ua-dev \
    libglib2.0-dev \
    libopus-dev \
    libogg-dev \
    libcurl4-openssl-dev \
    liblua5.3-dev \
    libconfig-dev \
    pkg-config \
    gengetopt \
    libtool \
    automake \
    gtk-doc-tools \
    cmake \
    ca-certificates \
    python3-pip \
    ninja-build

# 1b. Use pip to install the latest version of Meson
RUN pip3 install --upgrade meson

# 2. Compile and install libnice
RUN git clone https://gitlab.freedesktop.org/libnice/libnice.git && \
    cd libnice && \
    meson setup builddir --prefix=/usr && \
    ninja -C builddir && \
    ninja -C builddir install

# 3. Compile and install libsrtp v2.2.0
RUN wget https://github.com/cisco/libsrtp/archive/v2.2.0.tar.gz && \
    tar xfv v2.2.0.tar.gz && \
    cd libsrtp-2.2.0 && \
    ./configure --prefix=/usr --enable-openssl && \
    make shared_library && make install

# 4. Compile and install usrsctp
RUN git clone https://github.com/sctplab/usrsctp.git && \
    cd usrsctp && \
    ./bootstrap && \
    ./configure --prefix=/usr && \
    make && make install

# 5. Compile and install a NEWER libwebsockets (v4.3-stable)
RUN git clone https://github.com/warmcat/libwebsockets.git && \
    cd libwebsockets && \
    git checkout v4.3-stable && \
    mkdir build && cd build && \
    cmake -DLWS_MAX_SMP=1 -DCMAKE_INSTALL_PREFIX:PATH=/usr -DCMAKE_C_FLAGS="-fpic" .. && \
    make && make install

# Remove system libcurl to avoid conflicts, then install a modern version from source
RUN apt-get remove -y libcurl4 && \
    wget https://curl.se/download/curl-7.87.0.tar.gz && \
    tar -xvf curl-7.87.0.tar.gz && \
    cd curl-7.87.0 && \
    ./configure --prefix=/usr --with-openssl && \
    make && make install && \
    ldconfig

# Install Janus
RUN git clone https://github.com/meetecho/janus-gateway.git && \
    cd janus-gateway && \
    sh autogen.sh && \
    ./configure --prefix=/opt/janus && \
    make && \
    make install && \
    make configs && \
    mkdir -p /opt/janus/lib/janus/loggers

# Remove the default sample configs
RUN rm /opt/janus/etc/janus/janus.plugin.streaming.jcfg
RUN rm /opt/janus/etc/janus/janus.transport.websockets.jcfg
RUN rm /opt/janus/etc/janus/janus.transport.http.jcfg

# Copy our custom configurations
COPY config/ /opt/janus/etc/janus/

# Set the working directory
WORKDIR /opt/janus

# Expose the necessary ports
EXPOSE 8188 10000-10200/udp

# Define the default command to start Janus
CMD ["/opt/janus/bin/janus"]