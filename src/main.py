#!/usr/bin/env python3
import asyncio
import logging
import signal
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import api_router
from src.core.config import Config
from src.core.database import init_db
from src.core.camera_manager import CameraManager
from src.core.recording_manager import RecordingManager
from src.core.detection_engine import DetectionEngine
from src.websocket.server import WebSocketManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NVRSystem:
    def __init__(self):
        self.config = Config()
        self.camera_manager = None
        self.recording_manager = None
        self.detection_engine = None
        self.websocket_manager = None
        self.app = None
        
    async def startup(self):
        """Initialize all system components"""
        logger.info("Starting NVR System...")
        
        # Initialize database
        await init_db()
        
        # Initialize managers
        self.camera_manager = CameraManager(self.config)
        self.recording_manager = RecordingManager(self.config)
        self.detection_engine = DetectionEngine(self.config)
        self.websocket_manager = WebSocketManager()
        
        # Start components
        await self.camera_manager.start()
        await self.recording_manager.start()
        await self.detection_engine.start()
        
        logger.info("NVR System started successfully")
        
    async def shutdown(self):
        """Gracefully shutdown all components"""
        logger.info("Shutting down NVR System...")
        
        if self.camera_manager:
            await self.camera_manager.stop()
        if self.recording_manager:
            await self.recording_manager.stop()
        if self.detection_engine:
            await self.detection_engine.stop()
            
        logger.info("NVR System stopped")
        
    def create_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title="OpenNVR",
            description="Open Source Network Video Recorder System",
            version="1.0.0"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Include API routes
        app.include_router(api_router, prefix="/api")
        
        # Mount static files for web interface
        web_dir = Path(__file__).parent.parent / "web" / "dist"
        if web_dir.exists():
            app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")
        
        @app.on_event("startup")
        async def startup_event():
            await self.startup()
            
        @app.on_event("shutdown")
        async def shutdown_event():
            await self.shutdown()
            
        @app.get("/")
        async def root():
            return {"message": "OpenNVR System is running"}
            
        return app

async def main():
    """Main entry point"""
    nvr = NVRSystem()
    app = nvr.create_app()
    
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(nvr.shutdown())
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
