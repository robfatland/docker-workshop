# Docker Workshop Reference Guide

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [Essential Commands](#essential-commands)
3. [Building Your First Container](#building-your-first-container)
4. [Docker Networking](#docker-networking)
5. [Volumes and Data Persistence](#volumes-and-data-persistence)
6. [Docker Hub](#docker-hub)
7. [Troubleshooting](#troubleshooting)

---

## Core Concepts

### The Three Central Nouns

**Dockerfile** → **Image** → **Container**

- **Dockerfile**: Text file with instructions (the recipe)
- **Image**: Snapshot/template with everything needed (frozen meal)
- **Container**: Running instance that executes code (hot meal on your plate)

### Key Insight
- Build the Image once (slow)
- Run many Containers from it (fast)
- Images are reusable templates

---

## Essential Commands

### Checking Docker Status
```bash
# Check Docker version
docker --version

# See Docker system info
docker info

# Check disk usage
docker system df
```

### Working with Images
```bash
# List all images
docker images

# Pull an image from Docker Hub
docker pull ubuntu

# Remove an image
docker rmi <image_name>

# Remove all unused images
docker image prune
```

### Working with Containers
```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Run a container
docker run <image_name>

# Run container in background (detached)
docker run -d <image_name>

# Run container with port mapping
docker run -p 8080:80 <image_name>

# Run container with name
docker run --name mycontainer <image_name>

# Stop a container
docker stop <container_id_or_name>

# Start a stopped container
docker start <container_id_or_name>

# Remove a container
docker rm <container_id_or_name>

# Force remove a running container
docker rm -f <container_id_or_name>

# Remove all stopped containers
docker container prune
```

### Inspecting Containers
```bash
# View container logs
docker logs <container_name>

# Execute command inside running container
docker exec <container_name> <command>

# Get interactive shell in container
docker exec -it <container_name> bash

# Inspect container details
docker inspect <container_name>
```

---

## Building Your First Container

### Project Structure
```
my-project/
├── Dockerfile
├── app.py
└── requirements.txt
```

### Example: Python k-Means Classifier

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

CMD ["python", "app.py"]
```

**requirements.txt:**
```
scikit-learn==1.3.0
numpy==1.24.3
```

**Build and Run:**
```bash
# Build the image
docker build -t kmeans-classifier .

# Run the container
docker run kmeans-classifier
```

### Understanding Layers

Images are built in layers. Each Dockerfile instruction creates a layer:
- If a layer hasn't changed, Docker reuses the cached version
- Put frequently changing files (like app.py) near the end
- Put rarely changing dependencies (requirements.txt) near the beginning

---

## Docker Networking

### Network Types
- **bridge**: Default, containers on same bridge can communicate
- **host**: Container uses host's network directly
- **none**: No network access

### Network Commands
```bash
# Create a network
docker network create my-network

# List networks
docker network ls

# Inspect a network
docker network inspect my-network

# Remove a network
docker network rm my-network
```

### Multi-Container Communication

**Example: Web App + API**

```bash
# Create network
docker network create app-net

# Run backend API (not exposed to host)
docker run -d --name api --network app-net backend-image

# Run frontend (exposed on port 8080)
docker run -d --name web --network app-net -p 8080:8080 frontend-image
```

**Key Point:** Containers on the same network can reach each other by container name:
- From `web` container: `http://api:5000` works!
- Docker's internal DNS resolves container names to IPs

### Port Mapping

Format: `-p HOST_PORT:CONTAINER_PORT`

```bash
# Map host port 8080 to container port 80
docker run -p 8080:80 nginx

# Map host port 3000 to container port 8080
docker run -p 3000:8080 myapp
```

---

## Volumes and Data Persistence

### Two Types of Volumes

**1. Named Volumes (Docker-managed)**
```bash
# Create a volume
docker volume create mydata

# Use the volume
docker run -v mydata:/app/data myapp

# List volumes
docker volume ls

# Inspect volume
docker volume inspect mydata

# Remove volume
docker volume rm mydata
```

**2. Bind Mounts (Host directory)**
```bash
# Mount host directory into container
docker run -v /home/user/data:/app/data myapp

# On Windows/WSL
docker run -v /mnt/c/Users/user/data:/app/data myapp
```

### When to Use Each

- **Named volumes**: Database data, persistent app state
- **Bind mounts**: Development (edit code on host, run in container), large datasets

---

## Docker Hub

### Pushing Images to Docker Hub

```bash
# Login to Docker Hub
docker login

# Tag your image with your username
docker tag my-image username/my-image:latest

# Push to Docker Hub
docker push username/my-image:latest
```

### Pulling and Running from Docker Hub

```bash
# Pull an image
docker pull username/my-image:latest

# Run it
docker run username/my-image:latest
```

### Workshop Example: Prime Checker

```bash
# Create network
docker network create prime-net

# Run backend
docker run -d --name prime-api --network prime-net robfatland/prime-checker:latest

# Run frontend
docker run -d --name prime-web --network prime-net -p 8080:8080 robfatland/prime-frontend:latest

# Access at http://localhost:8080
```

---

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Use a different host port
docker run -p 9090:8080 myapp
```

**Container exits immediately:**
```bash
# Check logs
docker logs <container_name>

# Run interactively to debug
docker run -it myapp bash
```

**Can't connect to Docker daemon:**
```bash
# Make sure Docker Desktop is running
# Check: docker ps
```

**Out of disk space:**
```bash
# Clean up unused resources
docker system prune

# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune
```

**Container name already in use:**
```bash
# Remove the old container
docker rm -f <container_name>
```

### Debugging Commands

```bash
# View real-time container stats
docker stats

# See what's running inside container
docker exec <container> ps aux

# Copy file from container to host
docker cp <container>:/path/to/file ./local-file

# View container's environment variables
docker exec <container> env
```

---

## Quick Reference: Common Workflows

### Development Workflow
```bash
# 1. Write code and Dockerfile
# 2. Build image
docker build -t myapp .

# 3. Run and test
docker run -p 8080:8080 myapp

# 4. Make changes to code
# 5. Rebuild (only changed layers rebuild)
docker build -t myapp .

# 6. Stop old container and run new one
docker rm -f myapp-container
docker run -d --name myapp-container -p 8080:8080 myapp
```

### Production Deployment
```bash
# 1. Build with version tag
docker build -t myapp:v1.0 .

# 2. Tag for Docker Hub
docker tag myapp:v1.0 username/myapp:v1.0

# 3. Push to registry
docker push username/myapp:v1.0

# 4. On production server, pull and run
docker pull username/myapp:v1.0
docker run -d -p 80:8080 --name myapp username/myapp:v1.0
```

### Multi-Container App
```bash
# 1. Create network
docker network create myapp-net

# 2. Start database
docker run -d --name db --network myapp-net -v dbdata:/var/lib/postgresql/data postgres

# 3. Start backend API
docker run -d --name api --network myapp-net backend-image

# 4. Start frontend
docker run -d --name web --network myapp-net -p 80:80 frontend-image
```

---

## Best Practices

### Dockerfile Best Practices
1. Use specific base image versions: `FROM python:3.9-slim` not `FROM python`
2. Minimize layers by combining RUN commands
3. Put frequently changing files last (leverage cache)
4. Use `.dockerignore` to exclude unnecessary files
5. Don't run as root in production

### Security
- Don't include secrets in images
- Use environment variables for configuration
- Scan images for vulnerabilities: `docker scan <image>`
- Keep base images updated

### Performance
- Use smaller base images (`alpine`, `slim` variants)
- Multi-stage builds for compiled languages
- Clean up in the same layer: `RUN apt-get update && apt-get install -y pkg && rm -rf /var/lib/apt/lists/*`

---

## Additional Resources

- Docker Documentation: https://docs.docker.com
- Docker Hub: https://hub.docker.com
- Best Practices: https://docs.docker.com/develop/dev-best-practices/

---

## Workshop Projects

### 1. Prime Number Checker
Two-container app demonstrating Docker networking.

### 2. ResNet Image Classifier
ML model serving with HuggingFace, demonstrating:
- Large dependencies (PyTorch)
- Model downloads
- Web interface for ML inference

---

*End of Reference Guide*
