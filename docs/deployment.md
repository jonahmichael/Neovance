# Deployment Guide

This guide covers deployment options for the Neovance-AI system in production environments.

## Production Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Web Frontend  │    │   API Backend   │
│   (nginx/ALB)   │───▶│   (Next.js)     │───▶│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Static Files  │    │   Database      │
                       │   (S3/CDN)      │    │   (PostgreSQL)  │
                       └─────────────────┘    └─────────────────┘
```

## Deployment Options

### Option 1: Docker Compose (Recommended for Small-Medium Scale)

#### Prerequisites
- Docker and Docker Compose
- Domain name (for SSL)
- SSL certificate

#### Deployment Steps

1. **Clone and Configure**
   ```bash
   git clone https://github.com/jonahmichael/Neovance-AI.git
   cd Neovance-AI
   ```

2. **Environment Configuration**
   ```bash
   # Copy and configure environment files
   cp .env.example .env
   cp frontend/dashboard/.env.local.example frontend/dashboard/.env.local
   ```

3. **Build and Deploy**
   ```bash
   # Build production images
   docker-compose -f docker-compose.prod.yml build

   # Start services
   docker-compose -f docker-compose.prod.yml up -d
   ```

#### Production Docker Compose

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:latest-pg14
    environment:
      POSTGRES_DB: neovance_hil
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    networks:
      - neovance-network

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/neovance_hil
    depends_on:
      - postgres
    networks:
      - neovance-network

  frontend:
    build:
      context: frontend/dashboard
      dockerfile: Dockerfile
    environment:
      NODE_ENV: production
      NEXT_PUBLIC_API_URL: ${API_URL}
    depends_on:
      - backend
    networks:
      - neovance-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - frontend
      - backend
    networks:
      - neovance-network

volumes:
  postgres_data:

networks:
  neovance-network:
    driver: bridge
```

### Option 2: Kubernetes (Recommended for Large Scale)

#### Prerequisites
- Kubernetes cluster
- kubectl configured
- Helm (optional)

#### Deployment Manifests

**Namespace:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: neovance-ai
```

**Database:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: neovance-ai
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: timescale/timescaledb:latest-pg14
        env:
        - name: POSTGRES_DB
          value: "neovance_hil"
        - name: POSTGRES_USER
          value: "postgres"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
```

### Option 3: Cloud Managed Services

#### AWS Architecture
- **Frontend**: AWS Amplify or S3 + CloudFront
- **Backend**: AWS ECS or Lambda
- **Database**: AWS RDS PostgreSQL with TimescaleDB
- **Load Balancer**: Application Load Balancer (ALB)

#### Azure Architecture
- **Frontend**: Azure Static Web Apps
- **Backend**: Azure Container Instances or App Service
- **Database**: Azure Database for PostgreSQL
- **Load Balancer**: Azure Load Balancer

#### Google Cloud Architecture
- **Frontend**: Google Cloud Storage + CDN
- **Backend**: Google Cloud Run
- **Database**: Google Cloud SQL PostgreSQL
- **Load Balancer**: Google Cloud Load Balancer

## Environment Configuration

### Backend Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/neovance_hil

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]

# ML Model
MODEL_PATH=/app/trained_models/sepsis_model.pkl
```

### Frontend Environment Variables

```bash
# API URL
NEXT_PUBLIC_API_URL=https://api.yourdomain.com

# Environment
NODE_ENV=production

# Database (for build-time queries if needed)
DATABASE_URL=postgresql://postgres:password@localhost:5432/neovance_hil
```

## Security Considerations

### Authentication
- Implement proper OAuth2/OIDC for production
- Replace hardcoded credentials
- Use JWT tokens with proper expiration

### Database Security
- Enable SSL connections
- Use connection pooling
- Regular backups
- Access control lists

### Network Security
- Use HTTPS everywhere
- Implement proper CORS policies
- Network isolation between services
- Regular security updates

### Data Protection
- Encrypt sensitive data at rest
- Implement audit logging
- HIPAA compliance considerations
- Data retention policies

## Monitoring and Observability

### Application Metrics
- Response time monitoring
- Error rate tracking
- Database performance
- ML model accuracy metrics

### Infrastructure Metrics
- CPU and memory usage
- Disk space monitoring
- Network performance
- Container health checks

### Logging
- Structured logging (JSON)
- Log aggregation (ELK stack or similar)
- Error tracking (Sentry)
- Audit trail for clinical actions

## Backup and Recovery

### Database Backups
```bash
# Daily automated backups
pg_dump -h localhost -U postgres neovance_hil > backup_$(date +%Y%m%d).sql

# Point-in-time recovery setup
# Configure continuous archiving in PostgreSQL
```

### Application Backups
- Docker images in registry
- Configuration files in version control
- ML model files backup
- Static assets backup

## Scaling Strategies

### Horizontal Scaling
- Multiple backend API instances
- Load balancer configuration
- Database connection pooling
- Stateless application design

### Vertical Scaling
- Increase container resources
- Database performance tuning
- Cache implementation
- CDN for static assets

## Health Checks

### Application Health
```yaml
# Kubernetes health check example
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Database Health
```sql
-- Health check query
SELECT 1;

-- Performance check
SELECT count(*) FROM alerts WHERE created_at > NOW() - INTERVAL '1 hour';
```

## Disaster Recovery

### RTO/RPO Requirements
- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 1 hour

### Recovery Procedures
1. Restore database from latest backup
2. Deploy application from Docker registry
3. Verify health checks
4. Update DNS if needed
5. Notify stakeholders

## Compliance

### HIPAA Considerations
- Encrypt data in transit and at rest
- Implement proper access controls
- Audit logging for all data access
- Business Associate Agreement (BAA) with cloud provider

### Clinical Safety
- Regular ML model validation
- Alert fatigue monitoring
- Clinical workflow integration
- Staff training documentation