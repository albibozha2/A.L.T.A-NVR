# OpenNVR Docker Setup Guide

## Overview
This guide provides step-by-step instructions for setting up the OpenNVR system using Docker with an optimized Dockerfile and Docker Compose configuration.

## Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+

## Quick Start

### 1. Build the Docker Image
```bash
./docker_build.sh
```

### 2. Run with Docker Compose
```bash
docker-compose up -d
```

### 3. Access the Application
- Web Interface: http://localhost:8080
- API: http://localhost:8080/api
- Health Check: http://localhost:8080/health

## Configuration

### Environment Variables
- `PYTHONPATH`: /app
- `PYTHONUNBUFFERED`: 1

### Volume Mounts
- `./data:/app/data`
- `./logs:/app/logs`
- `./recordings:/app/recordings`
- `./config:/app/config`

## Troubleshooting

### Common Issues
1. **Build Errors**: Ensure all dependencies are installed correctly
2. **Port Conflicts**: Check if port 8080 is already in use
3. **Permission Errors**: Ensure proper file permissions for volume mounts

## Maintenance
- Regular updates to dependencies
- Monitoring system health
- Backup of configuration files
