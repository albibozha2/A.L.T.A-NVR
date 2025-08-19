import asyncio
import logging
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import threading
import time

from ultralytics import YOLO
from src.core.config import Config
from src.core.database import get_db, Event, Recording

logger = logging.getLogger(__name__)

class DetectionEngine:
    def __init__(self, config: Config):
        self.config = config
        self.model = None
        self.running = False
        self.detection_threads: Dict[int, threading.Thread] = {}
        self.camera_manager = None
        
    async def start(self):
        """Start the detection engine"""
        self.running = True
        
        # Load AI model
        model_path = self.config.detection_model
        try:
            self.model = YOLO(model_path)
            logger.info(f"Loaded detection model: {model_path}")
        except Exception as e:
            logger.error(f"Failed to load detection model: {e}")
            return
            
        logger.info("Detection engine started")
        
    async def stop(self):
        """Stop the detection engine"""
        self.running = False
        
        # Stop all detection threads
        for thread in self.detection_threads.values():
            thread.join(timeout=5)
            
        logger.info("Detection engine stopped")
        
    def set_camera_manager(self, camera_manager):
        """Set reference to camera manager"""
        self.camera_manager = camera_manager
        
    def start_detection(self, camera_id: int):
        """Start detection for a specific camera"""
        if camera_id in self.detection_threads:
            return
            
        thread = threading.Thread(
            target=self._detection_thread,
            args=(camera_id,),
            daemon=True
        )
        thread.start()
        self.detection_threads[camera_id] = thread
        
    def stop_detection(self, camera_id: int):
        """Stop detection for a specific camera"""
        if camera_id in self.detection_threads:
            thread = self.detection_threads[camera_id]
            thread.join(timeout=5)
            del self.detection_threads[camera_id]
            
    def _detection_thread(self, camera_id: int):
        """Thread function for running detection on a camera"""
        detection_classes = self.config.detection_classes
        confidence_threshold = self.config.detection_confidence
        
        while self.running:
            try:
                if not self.camera_manager:
                    time.sleep(1)
                    continue
                    
                frame = self.camera_manager.get_frame(camera_id)
                if frame is None:
                    time.sleep(0.1)
                    continue
                    
                # Run detection
                results = self.model(frame, conf=confidence_threshold, classes=detection_classes)
                
                # Process detections
                detections = []
                for r in results:
                    boxes = r.boxes
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            conf = box.conf[0].item()
                            cls = int(box.cls[0])
                            label = self.model.names[cls]
                            
                            if label in detection_classes and conf >= confidence_threshold:
                                detections.append({
                                    'label': label,
                                    'confidence': conf,
                                    'bbox': [x1, y1, x2, y2],
                                    'area': (x2 - x1) * (y2 - y1)
                                })
                                
                # Save events if detections found
                if detections:
                    self._save_detection_event(camera_id, detections)
                    
                time.sleep(0.1)  # Limit processing rate
                
            except Exception as e:
                logger.error(f"Error in detection thread for camera {camera_id}: {e}")
                time.sleep(1)
                
    def _save_detection_event(self, camera_id: int, detections: List[Dict]):
        """Save detection event to database"""
        try:
            db = next(get_db())
            
            # Create event for each detection
            for detection in detections:
                event = Event(
                    camera_id=camera_id,
                    event_type='object_detection',
                    label=detection['label'],
                    confidence=detection['confidence'],
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                    data=str(detection)
                )
                db.add(event)
                
            db.commit()
            db.close()
            
            logger.info(f"Saved {len(detections)} detection events for camera {camera_id}")
            
        except Exception as e:
            logger.error(f"Error saving detection event: {e}")
            
    def detect_motion(self, frame1: np.ndarray, frame2: np.ndarray) -> Tuple[bool, float]:
        """Detect motion between two frames"""
        if frame1 is None or frame2 is None:
            return False, 0.0
            
        # Convert to grayscale
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # Calculate difference
        diff = cv2.absdiff(gray1, gray2)
        
        # Apply blur to reduce noise
        blur = cv2.GaussianBlur(diff, (21, 21), 0)
        
        # Apply threshold
        _, thresh = cv2.threshold(blur, 25, 255, cv2.THRESH_BINARY)
        
        # Dilate to fill holes
        dilated = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Calculate motion score
        motion_area = 0
        for contour in contours:
            if cv2.contourArea(contour) > self.config.get('motion.min_area', 500):
                motion_area += cv2.contourArea(contour)
                
        total_area = frame1.shape[0] * frame1.shape[1]
        motion_score = motion_area / total_area if total_area > 0 else 0
        
        # Check if motion exceeds threshold
        motion_detected = motion_score > self.config.get('motion.sensitivity', 0.02)
        
        return motion_detected, motion_score
        
    def get_detection_info(self) -> Dict:
        """Get current detection engine information"""
        return {
            'model_loaded': self.model is not None,
            'model_path': self.config.detection_model,
            'classes': self.config.detection_classes,
            'confidence_threshold': self.config.detection_confidence,
            'active_cameras': len(self.detection_threads)
        }
