# Prime Checker Workshop - Participant Instructions

## Prerequisites
- Docker Desktop installed and running
- Internet connection

## Setup Instructions

### Step 1: Create Docker Network
```bash
docker network create prime-net
```

### Step 2: Pull and Run Backend (Prime Checker API)
```bash
docker run -d --name prime-api --network prime-net robfatland/prime-checker:latest
```

### Step 3: Pull and Run Frontend (Web Interface)
```bash
docker run -d --name prime-web --network prime-net -p 8080:8080 robfatland/prime-frontend:latest
```

### Step 4: Verify Containers are Running
```bash
docker ps
```

You should see both `prime-api` and `prime-web` containers running.

### Step 5: Access the Application
Open your browser and go to:
```
http://localhost:8080
```

Enter a positive integer and check if it's prime!

## Testing
- Try `17` → should say "17 is PRIME"
- Try `20` → should say "20 is NOT prime"
- Try `hello` → should say "Please enter a positive integer"

## Cleanup (After Workshop)
```bash
docker rm -f prime-api prime-web
docker network rm prime-net
docker rmi robfatland/prime-checker:latest robfatland/prime-frontend:latest
```

## Troubleshooting

**Port 8080 already in use?**
```bash
docker run -d --name prime-web --network prime-net -p 9090:8080 robfatland/prime-frontend:latest
```
Then access at `http://localhost:9090`

**Containers not starting?**
```bash
docker logs prime-api
docker logs prime-web
```

## What's Happening Behind the Scenes?
- `prime-web` serves the HTML interface on port 8080
- When you enter a number, `prime-web` calls `prime-api` via Docker network
- `prime-api` checks if the number is prime and returns the result
- Result is displayed in your browser

This demonstrates Docker networking between containers!
