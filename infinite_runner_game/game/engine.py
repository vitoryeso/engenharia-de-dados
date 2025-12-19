#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Infinite Runner Game Engine.

A simple game engine for an infinite runner game like Subway Surfers.
Supports multiple camera perspectives and procedural obstacle generation.
"""

import os
import json
import time
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import numpy as np

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"


class CameraMode(Enum):
    BEHIND = "behind"
    TOP_DOWN = "top_down"
    SIDE = "side"
    ISOMETRIC = "isometric"
    FIRST_PERSON = "first_person"


@dataclass
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __mul__(self, scalar):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def to_dict(self):
        return {"x": self.x, "y": self.y, "z": self.z}


@dataclass
class Transform:
    position: Vector3 = field(default_factory=Vector3)
    rotation: Vector3 = field(default_factory=Vector3)
    scale: Vector3 = field(default_factory=lambda: Vector3(1, 1, 1))


@dataclass
class GameObject:
    id: int
    name: str
    transform: Transform
    mesh_path: Optional[str] = None
    color: Tuple[int, int, int] = (255, 255, 255)
    is_active: bool = True
    tags: List[str] = field(default_factory=list)


@dataclass
class Player(GameObject):
    lane: int = 1
    is_jumping: bool = False
    is_sliding: bool = False
    jump_velocity: float = 0.0
    health: int = 3
    score: int = 0
    speed: float = 10.0
    
    def move_left(self):
        if self.lane > 0:
            self.lane -= 1
            self.transform.position.x = (self.lane - 1) * 3.0
    
    def move_right(self):
        if self.lane < 2:
            self.lane += 1
            self.transform.position.x = (self.lane - 1) * 3.0
    
    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.jump_velocity = 15.0
    
    def slide(self):
        if not self.is_jumping:
            self.is_sliding = True
    
    def update(self, delta_time: float):
        if self.is_jumping:
            self.transform.position.y += self.jump_velocity * delta_time
            self.jump_velocity -= 50.0 * delta_time
            
            if self.transform.position.y <= 0:
                self.transform.position.y = 0
                self.is_jumping = False
                self.jump_velocity = 0
        
        self.score += int(self.speed * delta_time * 10)


@dataclass 
class Obstacle(GameObject):
    lane: int = 1
    obstacle_type: str = "barrier"
    passed: bool = False


class InfiniteRunnerEngine:
    """Main game engine for infinite runner."""
    
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.state = GameState.MENU
        self.camera_mode = CameraMode.BEHIND
        
        self.player = Player(
            id=0,
            name="Player",
            transform=Transform(position=Vector3(0, 0, 0)),
            lane=1
        )
        
        self.obstacles: List[Obstacle] = []
        self.obstacle_id = 0
        self.spawn_distance = 50.0
        self.despawn_distance = -10.0
        
        self.world_speed = 15.0
        self.lane_width = 3.0
        self.num_lanes = 3
        
        self.last_spawn_z = 30.0
        self.min_spawn_gap = 10.0
        
        self.delta_time = 0.016
        self.frame_count = 0
        
        self.obstacle_colors = [
            (255, 0, 128), (0, 255, 255), (255, 0, 255),
            (128, 0, 255), (0, 255, 128), (255, 128, 0)
        ]
    
    def start_game(self):
        """Start a new game."""
        self.state = GameState.PLAYING
        self.player.score = 0
        self.player.health = 3
        self.player.lane = 1
        self.player.transform.position = Vector3(0, 0, 0)
        self.obstacles.clear()
        self.last_spawn_z = 30.0
        self.frame_count = 0
        
        for i in range(5):
            self._spawn_obstacle_wave()
    
    def update(self, delta_time: float):
        """Update game state."""
        if self.state != GameState.PLAYING:
            return
        
        self.delta_time = delta_time
        self.frame_count += 1
        
        self.player.update(delta_time)
        
        for obs in self.obstacles:
            obs.transform.position.z -= self.world_speed * delta_time
        
        self._check_collisions()
        
        self.obstacles = [o for o in self.obstacles 
                         if o.transform.position.z > self.despawn_distance]
        
        if len(self.obstacles) < 10:
            self._spawn_obstacle_wave()
        
        if self.player.health <= 0:
            self.state = GameState.GAME_OVER
    
    def _spawn_obstacle_wave(self):
        """Spawn a wave of obstacles."""
        num_obstacles = random.randint(1, 2)
        used_lanes = []
        
        for _ in range(num_obstacles):
            available_lanes = [l for l in range(self.num_lanes) if l not in used_lanes]
            if not available_lanes:
                break
            
            lane = random.choice(available_lanes)
            used_lanes.append(lane)
            
            self._spawn_obstacle(lane, self.last_spawn_z)
        
        self.last_spawn_z += random.uniform(self.min_spawn_gap, self.min_spawn_gap * 2)
    
    def _spawn_obstacle(self, lane: int, z_pos: float):
        """Spawn a single obstacle."""
        self.obstacle_id += 1
        
        obstacle_types = ["barrier", "cube", "tall_block", "wide_block", "ramp"]
        obs_type = random.choice(obstacle_types)
        
        x_pos = (lane - 1) * self.lane_width
        
        obs = Obstacle(
            id=self.obstacle_id,
            name=f"obstacle_{self.obstacle_id}",
            transform=Transform(
                position=Vector3(x_pos, 0, z_pos),
                scale=Vector3(1.5, 2.0, 1.0)
            ),
            color=random.choice(self.obstacle_colors),
            lane=lane,
            obstacle_type=obs_type,
            tags=["obstacle"]
        )
        
        self.obstacles.append(obs)
    
    def _check_collisions(self):
        """Check for player-obstacle collisions."""
        player_pos = self.player.transform.position
        player_lane = self.player.lane
        
        for obs in self.obstacles:
            if obs.passed:
                continue
            
            if obs.transform.position.z < -2:
                obs.passed = True
                continue
            
            if obs.lane == player_lane:
                obs_z = obs.transform.position.z
                
                if -1 < obs_z < 2:
                    if self.player.is_jumping and player_pos.y > 1.5:
                        continue
                    if self.player.is_sliding and obs.obstacle_type == "tall_block":
                        continue
                    
                    self.player.health -= 1
                    obs.passed = True
    
    def handle_input(self, key: str):
        """Handle player input."""
        if self.state == GameState.PLAYING:
            if key == "left":
                self.player.move_left()
            elif key == "right":
                self.player.move_right()
            elif key == "up" or key == "jump":
                self.player.jump()
            elif key == "down" or key == "slide":
                self.player.slide()
            elif key == "pause":
                self.state = GameState.PAUSED
        elif self.state == GameState.PAUSED:
            if key == "pause":
                self.state = GameState.PLAYING
        elif self.state == GameState.MENU or self.state == GameState.GAME_OVER:
            if key == "start":
                self.start_game()
    
    def set_camera_mode(self, mode: CameraMode):
        """Change camera perspective."""
        self.camera_mode = mode
    
    def render_frame(self) -> np.ndarray:
        """Render current game frame."""
        if not HAS_CV2:
            return np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        if self.camera_mode == CameraMode.BEHIND:
            self._render_behind_view(frame)
        elif self.camera_mode == CameraMode.TOP_DOWN:
            self._render_top_view(frame)
        elif self.camera_mode == CameraMode.SIDE:
            self._render_side_view(frame)
        elif self.camera_mode == CameraMode.ISOMETRIC:
            self._render_isometric_view(frame)
        
        self._render_ui(frame)
        
        return frame
    
    def _render_behind_view(self, frame: np.ndarray):
        """Render from behind player (classic runner view)."""
        horizon_y = self.height // 3
        
        frame[:horizon_y] = (30, 15, 45)
        frame[horizon_y:] = (50, 25, 60)
        
        for i in range(self.num_lanes + 1):
            x_bottom = int(i * self.width / self.num_lanes)
            x_top = int(self.width / 2 + (i - self.num_lanes / 2) * (self.width / self.num_lanes / 3))
            cv2.line(frame, (x_bottom, self.height), (x_top, horizon_y), (100, 50, 120), 2)
        
        sorted_obstacles = sorted(self.obstacles, key=lambda o: -o.transform.position.z)
        
        for obs in sorted_obstacles:
            if obs.transform.position.z < 0 or obs.transform.position.z > 50:
                continue
            
            scale = 1.0 - (obs.transform.position.z / 60)
            scale = max(0.2, min(1.0, scale))
            
            center_x = self.width // 2
            lane_offset = (obs.lane - 1) * (self.width // 3) * scale
            
            w = int(60 * scale)
            h = int(100 * scale)
            x = int(center_x + lane_offset - w // 2)
            y = int(horizon_y + (self.height - horizon_y) * (1 - obs.transform.position.z / 50) - h)
            
            color_bgr = obs.color[::-1]
            cv2.rectangle(frame, (x, y), (x + w, y + h), color_bgr, -1)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)
        
        player_x = self.width // 2 + (self.player.lane - 1) * (self.width // 6)
        player_y = self.height - 150 - int(self.player.transform.position.y * 30)
        
        cv2.circle(frame, (player_x, player_y - 30), 20, (200, 100, 200), -1)
        cv2.line(frame, (player_x, player_y - 10), (player_x, player_y + 40), (180, 80, 180), 3)
        cv2.line(frame, (player_x - 25, player_y + 10), (player_x + 25, player_y + 10), (180, 80, 180), 3)
    
    def _render_top_view(self, frame: np.ndarray):
        """Render top-down view."""
        frame[:] = (40, 20, 50)
        
        for i in range(self.num_lanes + 1):
            x = int(i * self.width / self.num_lanes)
            cv2.line(frame, (x, 0), (x, self.height), (100, 50, 120), 2)
        
        for obs in self.obstacles:
            if obs.transform.position.z < 0 or obs.transform.position.z > 50:
                continue
            
            x = int((obs.lane + 0.5) * self.width / self.num_lanes)
            y = int((1 - obs.transform.position.z / 50) * self.height)
            
            color_bgr = obs.color[::-1]
            cv2.rectangle(frame, (x - 30, y - 20), (x + 30, y + 20), color_bgr, -1)
        
        player_x = int((self.player.lane + 0.5) * self.width / self.num_lanes)
        player_y = self.height - 50
        cv2.circle(frame, (player_x, player_y), 25, (200, 100, 200), -1)
    
    def _render_side_view(self, frame: np.ndarray):
        """Render side-scrolling view."""
        frame[:] = (35, 18, 45)
        
        ground_y = self.height - 80
        cv2.line(frame, (0, ground_y), (self.width, ground_y), (120, 60, 140), 3)
        
        for obs in self.obstacles:
            if obs.transform.position.z < 0 or obs.transform.position.z > 50:
                continue
            
            x = int(obs.transform.position.z * self.width / 50)
            h = 80
            w = 40
            y = ground_y - h
            
            color_bgr = obs.color[::-1]
            cv2.rectangle(frame, (x, y), (x + w, ground_y), color_bgr, -1)
        
        player_x = 100
        player_y = ground_y - int(self.player.transform.position.y * 30) - 60
        cv2.circle(frame, (player_x, player_y), 20, (200, 100, 200), -1)
        cv2.rectangle(frame, (player_x - 15, player_y + 20), 
                     (player_x + 15, ground_y), (180, 80, 180), -1)
    
    def _render_isometric_view(self, frame: np.ndarray):
        """Render isometric view."""
        frame[:] = (25, 12, 35)
        
        for obs in self.obstacles:
            if obs.transform.position.z < 0 or obs.transform.position.z > 50:
                continue
            
            iso_x = self.width // 2 + int((obs.lane - 1) * 50 - obs.transform.position.z * 3)
            iso_y = self.height // 2 + int((obs.lane - 1) * 25 + obs.transform.position.z * 2)
            
            w, h = 40, 60
            color_bgr = obs.color[::-1]
            
            pts = np.array([
                [iso_x, iso_y - h],
                [iso_x + w, iso_y - h + 15],
                [iso_x + w, iso_y + 15],
                [iso_x, iso_y]
            ], np.int32)
            cv2.fillPoly(frame, [pts], color_bgr)
        
        player_iso_x = self.width // 2 + int((self.player.lane - 1) * 50)
        player_iso_y = self.height - 150 - int(self.player.transform.position.y * 20)
        cv2.circle(frame, (player_iso_x, player_iso_y), 25, (200, 100, 200), -1)
    
    def _render_ui(self, frame: np.ndarray):
        """Render UI elements."""
        cv2.putText(frame, f"Score: {self.player.score}", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        cv2.putText(frame, f"Health: {'♥' * self.player.health}", (20, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 100, 100), 2)
        
        cv2.putText(frame, f"Camera: {self.camera_mode.value}", (self.width - 200, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        if self.state == GameState.GAME_OVER:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (self.width, self.height), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            
            cv2.putText(frame, "GAME OVER", (self.width // 2 - 150, self.height // 2),
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 100), 3)
            cv2.putText(frame, f"Final Score: {self.player.score}", 
                       (self.width // 2 - 120, self.height // 2 + 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    def export_game_state(self) -> Dict:
        """Export current game state as JSON."""
        return {
            "state": self.state.value,
            "camera_mode": self.camera_mode.value,
            "frame": self.frame_count,
            "player": {
                "position": self.player.transform.position.to_dict(),
                "lane": self.player.lane,
                "score": self.player.score,
                "health": self.player.health,
                "is_jumping": self.player.is_jumping
            },
            "obstacles": [
                {
                    "id": obs.id,
                    "position": obs.transform.position.to_dict(),
                    "lane": obs.lane,
                    "type": obs.obstacle_type,
                    "color": list(obs.color)
                }
                for obs in self.obstacles
            ]
        }


def run_demo():
    """Run a demo of the game engine."""
    if not HAS_CV2:
        print("OpenCV not available. Install with: pip install opencv-python")
        return
    
    engine = InfiniteRunnerEngine()
    engine.start_game()
    
    output_dir = "../output/game_demo"
    os.makedirs(output_dir, exist_ok=True)
    
    camera_modes = list(CameraMode)
    
    for i in range(60):
        engine.set_camera_mode(camera_modes[i // 15 % len(camera_modes)])
        
        if i % 20 == 5:
            engine.handle_input("left")
        elif i % 20 == 15:
            engine.handle_input("right")
        elif i % 30 == 10:
            engine.handle_input("jump")
        
        engine.update(0.033)
        
        frame = engine.render_frame()
        cv2.imwrite(os.path.join(output_dir, f"frame_{i:04d}.png"), frame)
    
    print(f"Demo frames saved to: {output_dir}")
    print(f"Final score: {engine.player.score}")
    
    state = engine.export_game_state()
    with open(os.path.join(output_dir, "game_state.json"), 'w') as f:
        json.dump(state, f, indent=2)


if __name__ == "__main__":
    run_demo()
