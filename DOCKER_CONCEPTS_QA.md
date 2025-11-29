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

*This Q&A document captures the conceptual foundation of Docker from our workshop session.*
