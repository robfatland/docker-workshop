# Docker Workshop: Conceptual Q&A

This document captures fundamental questions and answers about Docker concepts, organized by topic.

---

## Docker Architecture & Components

### Q: What is the distinction between a socket and a port?

**UNIX Socket (like `/var/run/docker.sock`):**
- File-based communication on the same machine
- Lives in the filesystem (you can `ls` it!)
- Fast, local-only (no network involved)
- Used for inter-process communication (IPC)
- Example: Docker CLI talks to Docker daemon via socket

**Network Port (like port 80, 8080):**
- Number-based communication over network
- Can be local (localhost:8080) or remote (server.com:80)
- Uses TCP/IP protocol
- Used for network communication
- Example: Web browser talks to nginx via port 80

**Analogy:**
- Socket = internal phone line between offices
- Port = external phone number for customers

---

### Q: Does a Docker CLI command issued from bash invoke code that runs within the Docker Desktop VM?

**Yes!** The flow is:

```
WSL Bash
  ↓
docker CLI (client binary in WSL)
  ↓ (via socket: /var/run/docker.sock)
Docker Desktop VM
  ↓
dockerd (Docker daemon)
  ↓
Executes command (creates container, builds image, etc.)
```

The `docker` command in bash is just a **remote control** - all the real work happens inside Docker Desktop's VM.

**The Docker Engine API is EXPOSED BY the daemon:**
```
docker CLI
  ↓ (uses Docker Engine API)
dockerd (daemon)
  ↓ (exposes Docker Engine API)
  ↓ (uses lower-level APIs)
containerd
  ↓
runc (creates actual containers)
  ↓
Linux kernel (namespaces, cgroups)
```

---

### Q: Where do Docker images and containers actually exist?

**On Windows/Mac with Docker Desktop:**
- Images and containers exist **inside the Docker Desktop VM**
- Stored at `/var/lib/docker/` within the VM
- NOT on your Windows filesystem
- Managed by Docker

**What `docker system df` shows:**
- **Images:** Stored in VM (layered filesystem)
- **Containers:** Writable layer on top of images, in VM
- **Local Volumes:** Docker-managed, inside VM at `/var/lib/docker/volumes/`
- **Build Cache:** Inside VM at `/var/lib/docker/buildkit/`

**Exception:** Bind mounts directly link to host folders.

---

### Q: Is it accurate to say we don't think about "where" an image or container is located?

**Yes!** That's Docker's key design principle - **abstraction**.

**As CLI users, we think in terms of:**
- Image names: `ubuntu`, `nginx`, `python:3.9`
- Container names/IDs: `my-web-server`, `abc123def456`
- Logical concepts: ports, volumes, networks

**Docker handles the "where" for us** - same commands work on Windows, Mac, Linux.

**Exception:** When you mount volumes (`-v /host/path:/container/path`), you DO specify host locations.

---

## Images vs Containers

### Q: What is the point of the Docker Image?

The Image is an intermediate template between Dockerfile and Container:

- **Dockerfile** = Recipe (text instructions)
- **Image** = Frozen meal (ready to cook, but not cooking yet)
- **Container** = Hot meal on your plate (actively running)

**Key benefits:**
- Build the Image once (slow)
- Run many Containers from it (fast)
- Share the Image - everyone gets identical environments
- The Image remains unchanged when you run containers

---

### Q: An Image is "a layered filesystem" - what does this mean?

Each Dockerfile instruction creates a layer:

```dockerfile
FROM python:3.9        # Layer 1
RUN pip install flask  # Layer 2 (cached!)
COPY app.py .          # Layer 3
```

**If you change only app.py and rebuild:**
- Layers 1 and 2 are reused from cache
- Only Layer 3 is rebuilt
- **Result:** Much faster development!

---

## Containers vs VMs

### Q: Isn't a Container just like a very bare-bones VM?

**From user experience:** Yes, it feels like a VM.

**Technically:** No, fundamentally different.

**What makes it FEEL like a VM:**
- Own filesystem
- Own process tree
- Own network interface
- Can install packages, run commands

**What reveals it's NOT a VM:**

1. **Shared kernel:** Container and host use the same kernel
2. **No boot process:** Starts in milliseconds
3. **Can't load kernel modules:** VMs can, containers can't
4. **Resource sharing:** No hardware emulation layer

**The illusion:** Docker creates **namespaces** that make it appear isolated:
- PID namespace: Process 1 inside, but actually process 54321 on host
- Mount namespace: Own `/` filesystem view
- Network namespace: Own IP address

**Analogy:**
- **VM:** Separate computer running inside your computer
- **Container:** Clever trick making one process think it's alone

---

## Networking

### Q: How do we map ports from host to Docker VM network space?

**Port Mapping (forwarding):**
```bash
-p 8080:8080
```
**Host port 8080** → **Container port 8080**

Traffic is **forwarded/proxied** between two separate network spaces.

**The mapping chain:**
```
Browser (Windows)
    ↓
localhost:8080 (Windows)
    ↓ (Docker Desktop forwards)
Docker VM port 8080
    ↓ (Docker daemon routes)
Container port 8080
    ↓
Flask app listening on 0.0.0.0:8080
```

---

### Q: When prime-web makes outbound requests to port 5000 on prime-api, does it use its own port?

**Yes!** It uses an **ephemeral (temporary) port**.

**How it works:**
1. OS assigns a random high-numbered port (typically 32768-65535)
2. prime-web uses this as the source port
3. Connection: `prime-web:54321 → prime-api:5000` (54321 is example)
4. prime-api responds back to: `prime-api:5000 → prime-web:54321`
5. After response, ephemeral port is released

**Port Roles:**
- **Listening ports (servers):** Fixed (8080, 5000)
- **Ephemeral ports (clients):** Random, temporary

**Analogy:**
- Listening port = business phone number (fixed, published)
- Ephemeral port = your cell phone when you call them (temporary)

---

### Q: Where does the Docker network (like prime-net) actually exist?

The virtual network exists **in the Linux kernel's network namespace** managed by the Docker daemon.

**On Windows + WSL2:**
- Docker Desktop runs a hidden Linux VM
- The network exists **inside that VM's kernel**
- Managed by Linux kernel networking features (bridge, iptables, network namespaces)

**What it physically is:**
- A **software bridge** (like a virtual network switch)
- Network namespace isolation
- Routing rules in the kernel

**You can inspect it:**
```bash
docker network inspect prime-net
```

**Key point:** It's not a "place" you can navigate to - it's a **kernel data structure** that routes packets between containers.

---

### Q: Are there other types of networks besides bridge networks?

**Yes! Docker has 5 network types:**

1. **Bridge (default):** Containers on same bridge can talk, isolated from others
2. **Host:** Container uses host's network directly (no isolation)
3. **None:** No network at all (completely isolated)
4. **Overlay:** Spans multiple Docker hosts (for Swarm/Kubernetes)
5. **Macvlan:** Container gets its own MAC address (appears as physical device)

**Most common:** Bridge networks for 99% of use cases.

---

## Volumes and Data

### Q: Is a bind mount an alias for a host folder usable within the Container?

**Exactly right!** Perfect way to think about it.

**Bind mount:**
```bash
docker run -v /home/rob/mydata:/app/data ubuntu
```

- Host folder: `/home/rob/mydata`
- Container sees it as: `/app/data`
- **Same folder, two names** (alias)
- Write to `/app/data/file.txt` inside → appears at `/home/rob/mydata/file.txt` instantly

**It's like a symbolic link** - the container path is just another name for the host folder.

---

### Q: Do we perform an analogous operation in mapping volumes to volumes?

**Yes, very similar concept with an important distinction:**

**Port Mapping:** Data is **copied/forwarded**
- Packet arrives at host:8080
- Docker forwards it to container:8080
- Two separate network stacks

**Volume Mapping:** Data is **shared directly**
- File written in container at `/app/data/file.txt`
- Immediately visible on host at `/home/rob/data/file.txt`
- Same underlying filesystem

**Analogy:**
- Port mapping = Mail forwarding (copy and send)
- Volume mapping = Shared folder (same files, different doors)

---

## Building and Dependencies

### Q: What happens if you don't stipulate a version number in requirements.txt?

**Without version numbers:**
```txt
flask
torch
```
Gets the **latest version** available at build time.

**The Problem:**
- **Today:** Builds with `flask==3.1.0` - works!
- **6 months later:** Rebuilds with `flask==4.0.0` - breaking changes!
- "But it worked before!"

**Best Practice for Docker:**
```txt
flask==3.0.0  # Lock version, reproducible
```

**Trade-offs:**

| Approach | Pros | Cons |
|----------|------|------|
| No versions | Always latest | Breaks unexpectedly |
| Exact versions | Reproducible | Miss security updates |
| `pip freeze` | Fully reproducible | Very rigid |

**For Docker:** Exact versions are best - containers should be reproducible!

---

## Machine Learning with Docker

### Q: How many containers could run on a G4dn.xlarge?

**G4dn.xlarge specs:**
- 4 vCPUs, 16 GB RAM
- 1x NVIDIA T4 GPU (16 GB VRAM)

**Capacity by workload:**
- **Light containers** (APIs): 20-40 containers
- **Medium containers** (ML inference): 4-8 containers
- **GPU-accelerated ML:** 1-2 containers (GPU can't be easily shared)

**Calculation for ML:**
```
Available RAM: 16 GB - 2 GB (OS) = 14 GB
Per container: 2 GB
Max: 14 / 2 = 7 containers
```

**But GPU is the bottleneck** - only 1 container can use GPU at a time typically.

**Best practice:** Run 1 GPU container + 5-10 CPU-only support containers.

---

### Q: In ResNet-N, what does N indicate?

**N indicates the number of layers** in the network architecture, NOT categories.

- **ResNet-18:** 18 layers deep
- **ResNet-50:** 50 layers deep
- **ResNet-152:** 152 layers deep

**The number of categories is always 1000** (for ImageNet pre-trained models).

**The depth (N) affects:**
- Model capacity
- Accuracy (deeper usually = more accurate)
- Speed (deeper = slower)
- Parameters (deeper = more weights)

---

### Q: What are "Residual connections"? Is this where "Res" comes from?

**Yes! "Res" = Residual.**

**The Problem ResNet Solved:**
Before ResNet (2015), networks deeper than ~20 layers got worse, not better (vanishing gradients).

**Residual Connections - The Solution:**

**Traditional network:**
```
Input → Layer 1 → Layer 2 → Output
```
Each layer learns: `Output = F(Input)`

**ResNet with skip connection:**
```
Input ──────────────────┐
  │                     │
  └→ Layer 1 → Layer 2 ─┴→ Add → Output
```
Each block learns: `Output = F(Input) + Input`

The `+ Input` is the **skip connection** (or **residual connection**).

**Why This Works:**
- Learning the residual (difference) is easier
- Skip connection provides "highway" for gradients
- Even if F(x) learns poorly, you still have input passing through

**Analogy:**
- Traditional: "Describe this person completely"
- Residual: "Describe how this person differs from average" (easier!)

---

### Q: Is it correct to ask "how many neurons per layer" in ResNet?

**It's reasonable, but the answer varies wildly** - and "neurons" means something different in CNNs.

**Convolutional layers have:**
- **Filters (channels):** Number of feature maps
- **Spatial dimensions:** Height × Width

**ResNet-50 layer sizes (examples):**
- Input: 224×224×3 = ~150K pixels
- Early: 112×112×64 = ~800K activations
- Middle: 28×28×512 = ~400K activations
- Late: 7×7×2048 = ~100K activations
- Final: 2048 → 1000 (fully-connected layer)

**Better question:** "How many channels per layer?"
- ResNet-50: 64 → 256 → 512 → 1024 → 2048 channels as you go deeper

---

### Q: Is an input image resampled to a standard size? Is it RGB?

**Yes to both!**

**Standard preprocessing for ResNet:**

1. **Convert to RGB:** Grayscale → 3-channel RGB, RGBA → drop alpha
2. **Resize to 256×256:** Maintains aspect ratio
3. **Center crop to 224×224:** Standard ImageNet input size
4. **Normalize:** Using ImageNet dataset statistics

**Result:** Any input image → 224×224×3 RGB, normalized

This is why you can upload any size/format image and it works!

---

## Docker in Practice

### Q: How do I calculate how many containers I can run on a single host?

**Key Resource Constraints:**

**1. Memory (usually the bottleneck):**
```
Max containers = (Available RAM - OS overhead) / Memory per container
```

**Example:**
- Host: 16 GB RAM
- OS + Docker: 2 GB
- Each container: 512 MB
- **Max: (16 - 2) / 0.5 = 28 containers**

**2. CPU:**
```
Max containers = CPU cores × oversubscription / CPU per container
```

**Rule of Thumb:**
- Light containers (nginx, APIs): 50-100+ per host
- Medium containers (web apps): 10-30 per host
- Heavy containers (databases, ML): 5-10 per host

**Best practice:** Leave 20-30% headroom for spikes.

---

### Q: When do I need to know the Docker build number?

**When you need the build number:**
- **Troubleshooting:** Reporting bugs or asking for help
- **Compatibility:** Some features require specific versions
- **Production:** Ensure consistent environments across teams
- **Security:** Check if you have patched versions

**For learning Docker basics, you rarely need it.**

---

## Workshop Pedagogy

### Q: How should I explain Dockerfile → Image → Container to students?

**Excellent explanation structure:**

"There are three related, central nouns in the Docker ecosystem: Dockerfile, Image, and Container.

- **Dockerfile** is the starting point of a recipe for the Container
- **Image** is an intermediate template that does not execute code. It is a snapshot that includes everything needed to create and run the Container
- **Container** will execute a task when it runs

The Image is built using `docker build`. The subsequent command `docker run` creates a Container from the Image and then runs it. The image remains unchanged so the process can be repeated.

An Image is actually a layered filesystem. If we change only the Python code and do a new build: Docker will rebuild just that layer, not the entire Image: Faster development."

---

## Summary of Key Insights

1. **Abstraction is key:** Docker hides complexity (filesystem locations, networking details)
2. **Images are templates:** Build once, run many times
3. **Containers are isolated processes:** Not VMs, but feel like them
4. **Networks enable communication:** Container-to-container via names
5. **Volumes persist data:** Bind mounts for development, named volumes for production
6. **Layers enable caching:** Put stable dependencies first, changing code last
7. **Reproducibility matters:** Lock versions in requirements.txt

---

## Additional Concepts

### Q: What does `mkdir -p` do?

`-p` stands for "parents".

**What it does:**
- Creates parent directories as needed
- Doesn't error if directory already exists

```bash
mkdir -p ~/a/b/c/d    # Creates all intermediate directories
mkdir -p ~/dwdata     # Safe even if dwdata already exists
```

**Without `-p`:**
```bash
mkdir ~/a/b/c/d       # Fails if ~/a/b/c doesn't exist
mkdir ~/dwdata        # Errors if dwdata already exists
```

**For workshops:** `mkdir -p` is safer, but plain `mkdir` is simpler and teaches students to handle errors.

---

### Q: What's the difference between Flask and nginx?

**Flask** is a Python web application framework for building web apps.

**nginx** is a production web server for serving web traffic.

| Aspect | Flask | nginx |
|--------|-------|-------|
| **Purpose** | Build web apps | Serve web traffic |
| **Language** | Python | C |
| **Performance** | ~1000 req/sec | ~50,000+ req/sec |
| **Static files** | Slow | Fast |
| **Concurrency** | Limited | Excellent |
| **Use case** | Development, APIs | Production serving |

**In production:** nginx sits in front of Flask:
```
Browser → nginx:80 → Flask:5000
```

**For workshops:** Flask alone is perfect—students see the full stack in Python.

---

### Q: Why does prime-checker use Flask if only prime-frontend serves HTML?

**Both use Flask:**

- **prime-checker (backend API):** Flask exposes `/check/<number>` endpoint, returns JSON
- **prime-frontend (proxy + web):** Flask serves HTML page AND forwards requests to prime-checker

Flask is used for both HTTP servers—one serves an API, the other serves web pages and proxies requests.

---

### Q: Why did prime-checker have flask-cors installed?

**It's not needed** in the current setup.

CORS (Cross-Origin Resource Sharing) would be needed if the browser's JavaScript directly called prime-checker's API from a different origin. But since prime-frontend acts as a proxy, the browser only talks to prime-frontend (same origin). The backend call from prime-frontend to prime-checker is server-to-server, which doesn't trigger CORS restrictions.

**Result:** flask-cors was removed to reduce complexity.

---

### Q: What does EXPOSE do in a Dockerfile?

**EXPOSE is documentation only.** It tells users "this container listens on port X" but doesn't actually open or publish the port.

```dockerfile
EXPOSE 8080
```

The `-p 8080:8080` flag does the actual port mapping regardless of EXPOSE.

**EXPOSE is useful for:**
- Documentation (what ports does this app use?)
- `docker run -P` (publish all exposed ports to random host ports)

**For workshops:** You could remove all EXPOSE lines and everything would still work with `-p`.

---

### Q: Does EXPOSE refer to the Docker VM port or container port?

**Container port.** `EXPOSE 8080` means "the application inside this container listens on port 8080."

It's about the container's internal network namespace, not the Docker VM or host.

---

### Q: What does COPY do in a Dockerfile?

**COPY** copies files from the build context (host) to the image.

```dockerfile
WORKDIR /app
COPY app.py .
```

- **Source:** `app.py` in build context (the `.` from `docker build .`)
- **Destination:** Current WORKDIR in the image (`.` means `/app`)

**Result:** `app.py` ends up at `/app/app.py` in the image.

---

### Q: What's the difference between RUN and CMD in a Dockerfile?

**RUN:** Executes during `docker build`. Modifies the image. Creates a new layer.

**CMD:** Specifies what runs when container starts. Doesn't execute during build. Only one CMD per Dockerfile.

```dockerfile
RUN pip install flask          # Happens at build time
CMD ["python", "app.py"]       # Happens at container start
```

**Summary:**
- RUN = build the image
- CMD = run the container

---

### Q: What does `python -c` do?

**Execute the following string as Python code, then exit.**

```bash
python -c "print('hello')"
```

Runs the code without needing a .py file.

**Used in ResNet Dockerfile to download model during build:**
```dockerfile
RUN python -c "from transformers import AutoModelForImageClassification; AutoModelForImageClassification.from_pretrained('microsoft/resnet-50')"
```

---

### Q: What does the ResNet RUN command download?

The ~98MB download includes:
- Model architecture definition (small, KB range)
- Trained weights (the bulk, ~98MB)
- Configuration files (small)

**The weights ARE the model** for inference purposes. There's no separate "model" file—the weights contain the learned parameters from training on ImageNet.

---

### Q: Can I invoke Linux commands from Python REPL?

**Not with `!ls`** — that's IPython/Jupyter syntax, not standard Python REPL.

**From Python REPL, use:**
```python
import os
os.system('ls')
```

or

```python
import subprocess
subprocess.run(['ls'])
```

The `!` shortcut only works in IPython/Jupyter notebooks.

---

### Q: How do I exit the Python REPL in a container?

`exit()` or `quit()` or Ctrl+D will all exit the Python REPL and stop the container.

---

### Q: What happens if there's no CMD in the Dockerfile?

**The CMD from the base image is inherited.**

For example, `FROM python:3.11-slim` has `CMD ["python3"]` in its Dockerfile. So `docker run fu-image` (without specifying bash) would start a Python REPL.

**If there's no CMD anywhere in the chain:** The container starts and immediately exits with nothing to do.

---

### Q: What's the anatomy of the docker run command?

```
docker run [options] IMAGE [COMMAND]
```

**Two expected arguments:**
1. **Image name or identifier** (required)
2. **Command** (optional—uses CMD from Dockerfile if omitted)

**Example:**
```bash
docker run -it fu-image bash
```

- `-it`: Interactive terminal flags
- `fu-image`: Image name
- `bash`: Command to run (overrides CMD)

**The command is optional**—if omitted, Docker uses the CMD from the Dockerfile.

---

### Q: Does `bash` run "in perpetuity" when used as the command?

**Not quite.** `bash` doesn't run "in perpetuity"—it runs interactively because of the `-it` flags.

**Without `-it`:** bash would start and immediately exit (no stdin to read from).

**With `-it`:** bash stays alive by giving it a terminal to interact with.

**When you type `exit`:** bash terminates, and the container stops.

---

### Q: How does `-p 8080:8080` map ports?

```bash
docker run -p 8080:8080 prime-frontend
```

**Format:** `-p HOST_PORT:CONTAINER_PORT`

- **Left (8080):** Port on your host machine
- **Right (8080):** Port inside container where Flask is listening

**Traffic flow:**
1. Browser connects to `localhost:8080` (host)
2. Docker forwards to container port 8080
3. Flask app inside container receives request
4. Response flows back the same path

**If different:** `-p 9090:8080` means host port 9090 maps to container port 8080.

---

### Q: What are the default Docker networks?

**Docker creates three default networks:**

1. **bridge:** Default network. Containers can communicate by IP, but not by name. Used when you don't specify `--network`.

2. **host:** Container uses host's network directly. No isolation. Container ports are host ports (no `-p` mapping needed).

3. **none:** No networking. Completely isolated container.

**Custom networks** (like `prime-net`) provide DNS resolution—containers can reach each other by name.

---

### Q: Is the bridge network as fast as custom networks?

**Same speed**—both are bridge networks under the hood.

**To get IPs on default bridge:**
```bash
docker inspect prime-api | grep IPAddress
```

Then hardcode that IP: `http://172.17.0.2:5000`

**Bad idea because:**
- IPs change between runs
- Requires manual lookup
- Hardcoded IPs in code

**Custom network with DNS** (container names as hostnames) is simpler and more robust.

---

### Q: When would a container use the host network?

**Use cases:**
- Network performance critical (eliminates NAT overhead)
- Need to bind to specific host interfaces
- Network monitoring/scanning tools
- Legacy apps that can't handle port mapping

**Command:**
```bash
docker run --network host my-image
```

**Code inside container:**
```python
app.run(host='0.0.0.0', port=8080)
```

App binds to port 8080, immediately available on host at `localhost:8080`. No `-p` flag needed.

**Downside:** Port conflicts. If host already uses 8080, container fails.

---

### Q: What does `bash -c` mean?

**`-c` means "command"** (execute the following string as a command).

```bash
bash -c "echo hello"
```

It's not "clobber"—though the name does sound incongruously violent!

---

### Q: What is `/app` in containers?

**`/app` is a convention** for where you put application code in production containers.

**In Dockerfiles:**
```dockerfile
WORKDIR /app
COPY app.py .
```

`WORKDIR /app` creates the directory and sets it as the current working directory. When the container starts, you're in `/app` by default.

**It's not required**—just a widely-adopted convention. You could use `/code`, `/src`, or anything else, but `/app` is the de facto standard.

---

*This Q&A document captures the conceptual foundation of Docker from our workshop session.*
