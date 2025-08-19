import asyncio
import logging
import cv2
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import threading
import queue

from src.core.config import Config
from src.core.database import get_db, Camera

logger = logging.getLogger(__name__)

@dataclass
class CameraStream:
    camera_id: int
    url: str
    name: str
    enabled: bool
    settings: dict
    capture: Optional[cv2.VideoCapture] = None
    frame_queue: queue.Queue = None
    is_running: bool = False
    last_frame: Optional[any] = None
    last_frame_time: float = 0
    fps: float = 0
    frame_count: int = 0
    
    def __post_init__(self):
        if self.frame_queue is None:
            self.frame_queue = queue.Queue(maxsize=30)

class CameraManager:
    def __init__(self, config: Config):
        self.config = config
        self.cameras: Dict[int, CameraStream] = {}
        self.running = False
        self._threads: Dict[int, threading.Thread] = {}
        
    async def start(self):
        """Start the camera manager"""
        self.running = True
        await self.load_cameras()
        logger.info("Camera manager started")
        
    async def stop(self):
        """Stop the camera manager"""
        self.running = False
        for camera_id in list(self.cameras.keys()):
            await self.stop_camera(camera_id)
        logger.info("Camera manager stopped")
        
    async def load_cameras(self):
        """Load cameras from database"""
        db = next(get_db())
        try:
            cameras = db.query(Camera).filter(Camera.enabled == True).all()
            for camera in cameras:
                await self.add_camera(camera)
        finally:
            db.close()
            
    async def add_camera(self, camera: Camera):
        """Add a new camera"""
        settings = {}
        if camera.settings:
            import json
            settings = json.loads(camera.settings)
            
        stream = CameraStream(
            camera_id=camera.id,
            url=camera.url,
            name=camera.name,
            enabled=camera.enabled,
            settings=settings
        )
        
        self.cameras[camera.id] = stream
        
        if camera.enabled:
            await self.start_camera(camera.id)
            
    async def start_camera(self, camera_id: int) -> bool:
        """Start capturing from a specific camera"""
        if camera_id not in self.cameras:
            return False
            
        camera = self.cameras[camera_id]
        if camera.is_running:
            return True
            
        try:
            # Open video capture
            camera.capture = cv2.VideoCapture(camera.url)
            if not camera.capture.isOpened():
                logger.error(f"Failed to open camera {camera_id}: {camera.name}")
                return False
                
            # Set camera properties
            camera.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            camera.is_running = True
            
            # Start capture thread
            thread = threading.Thread(
                target=self._capture_thread,
                args=(camera_id,),
                daemon=True
            )
            thread.start()
            self._threads[camera_id] = thread
            
            logger.info(f"Started camera {camera_id}: {camera.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting camera {camera_id}: {e}")
            return False
            
    async def stop_camera(self, camera_id: int):
        """Stop capturing from a specific camera"""
        if camera_id not in self.cameras:
            return
            
        camera = self.cameras[camera_id]
        camera.is_running = False
        
        if camera.capture:
            camera.capture.release()
            camera.capture = None
            
        if camera_id in self._threads:
            self._threads[camera_id].join(timeout=5)
            del self._threads[camera_id]
            
        logger.info(f"Stopped camera {camera_id}")
        
    def _capture_thread(self, camera_id: int):
        """Thread function for capturing frames"""
        camera = self.cameras[camera_id]
        
        while camera.is_running and self.running:
            try:
                if camera.capture and camera.capture.isOpened():
                    ret, frame = camera.capture.read()
                    if ret:
                        # Update frame info
                        camera.last_frame = frame
                        camera.last_frame_time = time.time()
                        camera.frame_count += 1
                        
                        # Calculate FPS
                        if camera.frame_count % 30 == 0:
                            camera.fps = 30 / (time.time() - camera.last_frame_time)
                            
                        # Add to queue (non-blocking)
                        try:
                            if not camera.frame_queue.full():
                                camera.frame_queue.put_nowait(frame)
                        except queue.Full:
                            pass
                            
            except Exception as e:
                logger.error(f"Error capturing from camera {camera_id}: {e}")
                time.sleep(1)
                
    def get_frame(self, camera_id: int) -> Optional[any]:
        """Get the latest frame from a camera"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].last_frame
        return None
        
    def get_camera_info(self, camera_id: int) -> Optional[dict]:
        """Get camera information"""
        if camera_id not in self.cameras:
            return None
            
        camera = self.cameras[camera_id]
        return {
            'id': camera.camera_id,
            'name': camera.name,
            'url': camera.url,
            'enabled': camera.enabled,
            'is_running': camera.is_running,
            'fps': camera.fps,
            'frame_count': camera.frame_count
        }
        
    def get_all_cameras(self) -> List[dict]:
        """Get information for all cameras"""
        return [self.get_camera_info(cid) for cid in self.cameras.keys()]
        
    async def add_camera_from_url(self, name: str, url: str, settings: dict = None) -> int:
        """Add a new camera from URL"""
        db = next(get_db())
        try:
            camera = Camera(
                name=name,
                url=url,
                enabled=True,
                settings=json.dumps(settings or {})
            )
            db.add(camera)
            db.commit()
            
            await self.add_camera(camera)
            return camera.id
            
        finally:
            db.close()
            
    async def remove_camera(self, camera_id: int) -> bool:
        """Remove a camera"""
        if camera_id not in self.cameras:
            return False
            
        await self.stop_camera(camera_id)
        del self.cameras[camera_id]
        
        # Remove from database
        db = next(get_db())
        try:
            camera = db.query(Camera).filter(Camera.id == camera_id).first()
            if camera:
                db.delete(camera)
                db.commit()
            return True
        finally:
            db.close()
