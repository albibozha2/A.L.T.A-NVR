from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json
import cv2
import io
import os
from datetime import datetime

from src.core.database import get_db, Camera, Recording, Event

router = APIRouter()

# Pydantic models
class CameraCreate(BaseModel):
    name: str
    url: str
    settings: Optional[dict] = {}

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    enabled: Optional[bool] = None
    settings: Optional[dict] = None

# Camera endpoints
@router.get("/cameras", response_model=List[dict])
async def get_cameras(db: Session = Depends(get_db)):
    """Get all cameras"""
    cameras = db.query(Camera).all()
    return [{
        'id': c.id,
        'name': c.name,
        'url': c.url,
        'enabled': c.enabled,
        'created_at': c.created_at.isoformat(),
        'updated_at': c.updated_at.isoformat()
    } for c in cameras]

@router.post("/cameras", response_model=dict)
async def create_camera(camera: CameraCreate, db: Session = Depends(get_db)):
    """Add a new camera"""
    db_camera = Camera(
        name=camera.name,
        url=camera.url,
        enabled=True,
        settings=json.dumps(camera.settings or {})
    )
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    
    return {
        'id': db_camera.id,
        'name': db_camera.name,
        'url': db_camera.url,
        'enabled': db_camera.enabled
    }

@router.get("/cameras/{camera_id}", response_model=dict)
async def get_camera(camera_id: int, db: Session = Depends(get_db)):
    """Get specific camera"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    return {
        'id': camera.id,
        'name': camera.name,
        'url': camera.url,
        'enabled': camera.enabled,
        'settings': json.loads(camera.settings) if camera.settings else {},
        'created_at': camera.created_at.isoformat(),
        'updated_at': camera.updated_at.isoformat()
    }

@router.put("/cameras/{camera_id}", response_model=dict)
async def update_camera(camera_id: int, camera: CameraUpdate, db: Session = Depends(get_db)):
    """Update camera settings"""
    db_camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    if camera.name is not None:
        db_camera.name = camera.name
    if camera.url is not None:
        db_camera.url = camera.url
    if camera.enabled is not None:
        db_camera.enabled = camera.enabled
    if camera.settings is not None:
        db_camera.settings = json.dumps(camera.settings)
        
    db.commit()
    db.refresh(db_camera)
    
    return {
        'id': db_camera.id,
        'name': db_camera.name,
        'url': db_camera.url,
        'enabled': db_camera.enabled
    }

@router.delete("/cameras/{camera_id}")
async def delete_camera(camera_id: int, db: Session = Depends(get_db)):
    """Delete a camera"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    db.delete(camera)
    db.commit()
    
    return {"message": "Camera deleted successfully"}

# Recording endpoints
@router.get("/recordings", response_model=List[dict])
async def get_recordings(limit: int = 100, db: Session = Depends(get_db)):
    """Get recordings"""
    recordings = db.query(Recording).order_by(Recording.created_at.desc()).limit(limit).all()
    
    return [{
        'id': r.id,
        'camera_id': r.camera_id,
        'start_time': r.start_time.isoformat(),
        'end_time': r.end_time.isoformat(),
        'file_path': r.file_path,
        'file_size': r.file_size,
        'duration': r.duration,
        'event_based': r.event_based,
        'motion_score': r.motion_score
    } for r in recordings]

@router.get("/recordings/{recording_id}/download")
async def download_recording(recording_id: int, db: Session = Depends(get_db)):
    """Download a recording file"""
    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
        
    file_path = recording.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Recording file not found")
    
    def iterfile():
        with open(file_path, mode="rb") as file_like:
            yield from file_like
            
    return StreamingResponse(
        iterfile(),
        media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename=recording_{recording_id}.mp4"}
    )

# Event endpoints
@router.get("/events", response_model=List[dict])
async def get_events(limit: int = 100, db: Session = Depends(get_db)):
    """Get events"""
    events = db.query(Event).order_by(Event.created_at.desc()).limit(limit).all()
    
    return [{
        'id': e.id,
        'camera_id': e.camera_id,
        'recording_id': e.recording_id,
        'event_type': e.event_type,
        'label': e.label,
        'confidence': e.confidence,
        'start_time': e.start_time.isoformat(),
        'end_time': e.end_time.isoformat(),
        'thumbnail_path': e.thumbnail_path,
        'data': json.loads(e.data) if e.data else None
    } for e in events]

# System status endpoints
@router.get("/status")
async def get_system_status():
    """Get system status"""
    return {
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    }

# Live streaming endpoints
@router.get("/cameras/{camera_id}/snapshot")
async def get_camera_snapshot(camera_id: int):
    """Get a snapshot from a camera"""
    # This would need camera_manager integration
    return {"message": "Snapshot endpoint - requires camera manager integration"}

# WebSocket endpoints for real-time updates
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send periodic status updates
            await websocket.send_json({
                'status': 'running',
                'timestamp': datetime.now().isoformat()
            })
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
    finally:
        await websocket.close()
