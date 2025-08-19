import asyncio
import logging
import cv2
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading
import time
import subprocess

from src.core.config import Config
from src.core.database import get_db, Recording, Camera, Event

logger = logging.getLogger(__name__)

class RecordingManager:
    def __init__(self, config: Config):
        self.config = config
        self.running = False
        self.recording_threads: Dict[int, threading.Thread] = {}
        self.camera_manager = None
        self.storage_path = Path(self.config.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    async def start(self):
        """Start the recording manager"""
        self.running = True
        
        # Start storage cleanup scheduler
        asyncio.create_task(self._storage_cleanup_loop())
        
        logger.info("Recording manager started")
        
    async def stop(self):
        """Stop the recording manager"""
        self.running = False
        
        # Stop all recording threads
        for thread in self.recording_threads.values():
            thread.join(timeout=5)
            
        logger.info("Recording manager stopped")
        
    def set_camera_manager(self, camera_manager):
        """Set reference to camera manager"""
        self.camera_manager = camera_manager
        
    def start_recording(self, camera_id: int, event_based: bool = False):
        """Start recording for a specific camera"""
        if camera_id in self.recording_threads:
            return
            
        thread = threading.Thread(
            target=self._recording_thread,
            args=(camera_id, event_based),
            daemon=True
        )
        thread.start()
        self.recording_threads[camera_id] = thread
        
    def stop_recording(self, camera_id: int):
        """Stop recording for a specific camera"""
        if camera_id in self.recording_threads:
            thread = self.recording_threads[camera_id]
            thread.join(timeout=5)
            del self.recording_threads[camera_id]
            
    def _recording_thread(self, camera_id: int, event_based: bool):
        """Thread function for recording a camera"""
        recording_settings = {
            'fps': self.config.get('cameras.default_settings.fps', 15),
            'resolution': self.config.get('cameras.default_settings.resolution', [1920, 1080]),
            'codec': self.config.get('cameras.default_settings.codec', 'h264'),
            'bitrate': self.config.get('cameras.default_settings.bitrate', 2000)
        }
        
        while self.running:
            try:
                if not self.camera_manager:
                    time.sleep(1)
                    continue
                    
                # Get camera info
                camera_info = self.camera_manager.get_camera_info(camera_id)
                if not camera_info or not camera_info['is_running']:
                    time.sleep(1)
                    continue
                    
                # Create recording directory
                date_str = datetime.now().strftime('%Y-%m-%d')
                camera_dir = self.storage_path / str(camera_id) / date_str
                camera_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate filename
                timestamp = datetime.now().strftime('%H-%M-%S')
                filename = f"{camera_id}_{timestamp}.mp4"
                filepath = camera_dir / filename
                
                # Start recording
                start_time = datetime.now()
                self._record_video(camera_id, str(filepath), recording_settings)
                
                # Save recording info to database
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                db = next(get_db())
                recording = Recording(
                    camera_id=camera_id,
                    start_time=start_time,
                    end_time=end_time,
                    file_path=str(filepath),
                    file_size=filepath.stat().st_size if filepath.exists() else 0,
                    duration=duration,
                    event_based=event_based
                )
                db.add(recording)
                db.commit()
                db.close()
                
                logger.info(f"Saved recording: {filepath}")
                
            except Exception as e:
                logger.error(f"Error in recording thread for camera {camera_id}: {e}")
                time.sleep(5)
                
    def _record_video(self, camera_id: int, output_path: str, settings: dict):
        """Record video from camera to file"""
        fps = settings['fps']
        width, height = settings['resolution']
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        max_frames = fps * 3600  # 1 hour max per file
        
        while self.running and frame_count < max_frames:
            frame = self.camera_manager.get_frame(camera_id)
            if frame is not None:
                # Resize frame if needed
                if frame.shape[:2] != (height, width):
                    frame = cv2.resize(frame, (width, height))
                    
                out.write(frame)
                frame_count += 1
                
            time.sleep(1 / fps)
            
        out.release()
        
    async def _storage_cleanup_loop(self):
        """Periodic storage cleanup"""
        while self.running:
            try:
                await self._cleanup_old_recordings()
                await self._enforce_storage_limit()
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Error in storage cleanup: {e}")
                await asyncio.sleep(3600)
                
    async def _cleanup_old_recordings(self):
        """Remove recordings older than retention period"""
        retention_days = self.config.retention_days
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        db = next(get_db())
        try:
            old_recordings = db.query(Recording).filter(
                Recording.created_at < cutoff_date
            ).all()
            
            for recording in old_recordings:
                filepath = Path(recording.file_path)
                if filepath.exists():
                    filepath.unlink()
                    
                db.delete(recording)
                
            if old_recordings:
                logger.info(f"Cleaned up {len(old_recordings)} old recordings")
                
            db.commit()
            
        finally:
            db.close()
            
    async def _enforce_storage_limit(self):
        """Enforce storage size limit"""
        max_size_gb = self.config.max_storage_gb
        max_size_bytes = max_size_gb * 1024 * 1024 * 1024
        
        # Calculate current storage usage
        total_size = 0
        for path in self.storage_path.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
                
        if total_size <= max_size_bytes:
            return
            
        # Remove oldest recordings until under limit
        db = next(get_db())
        try:
            recordings = db.query(Recording).order_by(Recording.created_at.asc()).all()
            
            removed_count = 0
            for recording in recordings:
                if total_size <= max_size_bytes:
                    break
                    
                filepath = Path(recording.file_path)
                if filepath.exists():
                    file_size = filepath.stat().st_size
                    filepath.unlink()
                    total_size -= file_size
                    
                db.delete(recording)
                removed_count += 1
                
            if removed_count > 0:
                logger.info(f"Removed {removed_count} recordings to enforce storage limit")
                
            db.commit()
            
        finally:
            db.close()
            
    def get_recordings(self, camera_id: int = None, limit: int = 100) -> List[dict]:
        """Get list of recordings"""
        db = next(get_db())
        try:
            query = db.query(Recording)
            
            if camera_id:
                query = query.filter(Recording.camera_id == camera_id)
                
            recordings = query.order_by(Recording.created_at.desc()).limit(limit).all()
            
            return [{
                'id': r.id,
                'camera_id': r.camera_id,
                'start_time': r.start_time.isoformat(),
                'end_time': r.end_time.isoformat(),
                'file_path': r.file_path,
                'file_size': r.file_size,
                'duration': r.duration,
                'event_based': r.event_based
            } for r in recordings]
            
        finally:
            db.close()
            
    def get_storage_info(self) -> dict:
        """Get storage usage information"""
        total_size = 0
        file_count = 0
        
        for path in self.storage_path.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
                file_count += 1
                
        return {
            'total_size_bytes': total_size,
            'total_size_gb': total_size / (1024**3),
            'file_count': file_count,
            'max_size_gb': self.config.max_storage_gb,
            'retention_days': self.config.retention_days
        }
