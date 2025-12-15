# Smart Home IoT Simulation

A comprehensive Smart Home IoT simulation system with modern GUI, MongoDB data warehousing, and support for multiple data transmission formats (JSON/XML/Mixed).

## 🚀 How to Run

### Prerequisites
- Python 3.9+
- Docker and Docker Compose

### Quick Start

1. **Start MongoDB**
   ```bash
   docker-compose up -d
   ```

2. **Run the Application**
   ```bash
   python main.py
   ```

3. **Access Services**
   - Application: GUI window opens automatically
   - MongoDB: `localhost:27017`
   - Mongo Express: http://localhost:8081 (login: admin/pass)

### Stop Services
```bash
docker-compose down
```