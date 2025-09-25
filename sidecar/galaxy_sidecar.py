#!/usr/bin/env python3
"""
Galaxy Sidecar Service
Provides standardized Galaxy health and metadata endpoints for unmanaged infrastructure services
"""
import os
import json
import psutil
import socket
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import asyncio
import aiohttp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Galaxy Infrastructure Sidecar",
    description="Provides Galaxy-standard endpoints for unmanaged infrastructure services",
    version="1.0.0"
)

# Service configuration from environment variables
SERVICE_NAME = os.getenv('GALAXY_SERVICE_NAME', '{{SERVICE_NAME}}')
SERVICE_TIER = os.getenv('GALAXY_SERVICE_TIER', '{{TIER}}')
SERVICE_TEAM = os.getenv('GALAXY_SERVICE_TEAM', '{{TEAM}}')
SERVICE_DESCRIPTION = os.getenv('GALAXY_SERVICE_DESCRIPTION', '{{DESCRIPTION}}')

# Infrastructure service configuration
INFRA_SERVICE_HOST = os.getenv('INFRA_SERVICE_HOST', 'localhost')
INFRA_SERVICE_PORT = int(os.getenv('INFRA_SERVICE_PORT', '5432'))
INFRA_SERVICE_TYPE = os.getenv('INFRA_SERVICE_TYPE', 'postgres')

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    infrastructure_status: str
    checks: dict

class InfoResponse(BaseModel):
    name: str
    description: str
    tier: str
    team: str
    version: str
    infrastructure_type: str
    galaxy_managed: bool
    uptime_seconds: float

class DependencyResponse(BaseModel):
    service: str
    dependencies: list
    infrastructure_service: dict

# Startup time for uptime calculation
START_TIME = datetime.now()

async def check_postgres_health():
    """Check PostgreSQL health"""
    try:
        # Try to connect to PostgreSQL
        import asyncpg
        conn = await asyncpg.connect(
            host=INFRA_SERVICE_HOST,
            port=INFRA_SERVICE_PORT,
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', ''),
            database=os.getenv('POSTGRES_DB', 'postgres')
        )
        await conn.execute('SELECT 1')
        await conn.close()
        return {"status": "healthy", "details": "PostgreSQL connection successful"}
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return {"status": "unhealthy", "details": str(e)}

async def check_redis_health():
    """Check Redis health"""
    try:
        import aioredis
        redis = aioredis.from_url(f"redis://{INFRA_SERVICE_HOST}:{INFRA_SERVICE_PORT}")
        await redis.ping()
        await redis.close()
        return {"status": "healthy", "details": "Redis ping successful"}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "details": str(e)}

async def check_generic_tcp_health():
    """Check generic TCP service health"""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(INFRA_SERVICE_HOST, INFRA_SERVICE_PORT),
            timeout=5.0
        )
        writer.close()
        await writer.wait_closed()
        return {"status": "healthy", "details": f"TCP connection to {INFRA_SERVICE_HOST}:{INFRA_SERVICE_PORT} successful"}
    except Exception as e:
        logger.error(f"TCP health check failed: {e}")
        return {"status": "unhealthy", "details": str(e)}

async def check_infrastructure_health():
    """Check health of the underlying infrastructure service"""
    if INFRA_SERVICE_TYPE == 'postgres':
        return await check_postgres_health()
    elif INFRA_SERVICE_TYPE == 'redis':
        return await check_redis_health()
    else:
        return await check_generic_tcp_health()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Galaxy-standard health check endpoint"""
    infra_health = await check_infrastructure_health()
    
    # System health checks
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    overall_status = "healthy" if infra_health["status"] == "healthy" else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        service=SERVICE_NAME,
        infrastructure_status=infra_health["status"],
        checks={
            "infrastructure": infra_health,
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100
            }
        }
    )

@app.get("/galaxy/info", response_model=InfoResponse)
async def service_info():
    """Galaxy service information endpoint"""
    uptime = (datetime.now() - START_TIME).total_seconds()
    
    return InfoResponse(
        name=SERVICE_NAME,
        description=SERVICE_DESCRIPTION,
        tier=SERVICE_TIER,
        team=SERVICE_TEAM,
        version="1.0.0",
        infrastructure_type=INFRA_SERVICE_TYPE,
        galaxy_managed=True,
        uptime_seconds=uptime
    )

@app.get("/galaxy/root")
async def root():
    """Galaxy root endpoint"""
    return {
        "service": SERVICE_NAME,
        "message": f"Galaxy Infrastructure Sidecar for {INFRA_SERVICE_TYPE}",
        "tier": SERVICE_TIER,
        "team": SERVICE_TEAM,
        "infrastructure": {
            "type": INFRA_SERVICE_TYPE,
            "host": INFRA_SERVICE_HOST,
            "port": INFRA_SERVICE_PORT
        },
        "endpoints": ["/health", "/galaxy/info", "/galaxy/root", "/galaxy/dependencies"]
    }

@app.get("/galaxy/dependencies", response_model=DependencyResponse)
async def dependencies():
    """Galaxy dependencies endpoint"""
    return DependencyResponse(
        service=SERVICE_NAME,
        dependencies=[],  # Infrastructure services typically don't have dependencies
        infrastructure_service={
            "type": INFRA_SERVICE_TYPE,
            "host": INFRA_SERVICE_HOST,
            "port": INFRA_SERVICE_PORT,
            "galaxy_sidecar": True
        }
    )

if __name__ == "__main__":
    logger.info(f"Starting Galaxy sidecar for {SERVICE_NAME} ({INFRA_SERVICE_TYPE})")
    logger.info(f"Infrastructure service: {INFRA_SERVICE_HOST}:{INFRA_SERVICE_PORT}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3000,
        log_level="info"
    )