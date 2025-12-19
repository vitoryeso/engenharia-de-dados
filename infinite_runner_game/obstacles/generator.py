#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procedural Obstacle Generator for Infinite Runner Game.

Generates obstacle images with random positions that can be:
1. Used directly as 2D sprites
2. Converted to 3D models via Image-to-3D
3. Exported as coordinate data for game engine
"""

import os
import random
import json
import numpy as np
import cv2
from dataclasses import dataclass, asdict
from typing import List, Tuple
from pathlib import Path


@dataclass
class Obstacle:
    """Represents a game obstacle."""
    id: int
    type: str
    x: int
    y: int
    width: int
    height: int
    depth: int
    color: Tuple[int, int, int]
    lane: int  # 0=left, 1=center, 2=right
    z_position: float  # Distance from player (0-100)
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "position": {"x": self.x, "y": self.y, "z": self.z_position},
            "size": {"width": self.width, "height": self.height, "depth": self.depth},
            "lane": self.lane,
            "color_rgb": list(self.color)
        }


class ObstacleGenerator:
    """Generates procedural obstacle layouts for infinite runner game."""
    
    OBSTACLE_TYPES = {
        "barrier": {"min_size": (60, 80), "max_size": (120, 150), "depth": 30},
        "cube": {"min_size": (50, 50), "max_size": (80, 80), "depth": 50},
        "tall_block": {"min_size": (40, 100), "max_size": (70, 200), "depth": 40},
        "wide_block": {"min_size": (100, 40), "max_size": (180, 70), "depth": 35},
        "ramp": {"min_size": (80, 60), "max_size": (140, 100), "depth": 80},
    }
    
    NEON_COLORS = [
        (255, 0, 128),    # Hot pink
        (0, 255, 255),    # Cyan
        (255, 0, 255),    # Magenta
        (128, 0, 255),    # Purple
        (0, 255, 128),    # Spring green
        (255, 128, 0),    # Orange
        (0, 128, 255),    # Sky blue
        (255, 255, 0),    # Yellow
    ]
    
    def __init__(self, width: int = 800, height: int = 600, num_lanes: int = 3):
        self.width = width
        self.height = height
        self.num_lanes = num_lanes
        self.lane_width = width // num_lanes
        self.obstacle_id = 0
    
    def generate_obstacle(self, lane: int = None, z_pos: float = None) -> Obstacle:
        """Generate a single random obstacle."""
        self.obstacle_id += 1
        
        obs_type = random.choice(list(self.OBSTACLE_TYPES.keys()))
        config = self.OBSTACLE_TYPES[obs_type]
        
        w = random.randint(config["min_size"][0], config["max_size"][0])
        h = random.randint(config["min_size"][1], config["max_size"][1])
        depth = config["depth"]
        
        if lane is None:
            lane = random.randint(0, self.num_lanes - 1)
        
        lane_center = (lane * self.lane_width) + (self.lane_width // 2)
        x = lane_center - (w // 2)
        
        ground_y = self.height - 100
        y = ground_y - h
        
        if z_pos is None:
            z_pos = random.uniform(10, 90)
        
        color = random.choice(self.NEON_COLORS)
        
        return Obstacle(
            id=self.obstacle_id,
            type=obs_type,
            x=x, y=y,
            width=w, height=h, depth=depth,
            color=color,
            lane=lane,
            z_position=z_pos
        )
    
    def generate_wave(self, num_obstacles: int = 5, min_z: float = 20, max_z: float = 100) -> List[Obstacle]:
        """Generate a wave of obstacles at different depths."""
        obstacles = []
        z_positions = sorted([random.uniform(min_z, max_z) for _ in range(num_obstacles)])
        
        for z_pos in z_positions:
            available_lanes = list(range(self.num_lanes))
            lane = random.choice(available_lanes)
            obstacles.append(self.generate_obstacle(lane=lane, z_pos=z_pos))
        
        return obstacles
    
    def render_frame(self, obstacles: List[Obstacle], perspective: str = "behind") -> np.ndarray:
        """
        Render obstacles as a game frame.
        
        perspective options:
        - "behind": Camera behind player (classic runner view)
        - "top": Top-down view
        - "side": Side-scrolling view
        - "isometric": Isometric 3D view
        """
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        self._draw_background(img, perspective)
        
        sorted_obstacles = sorted(obstacles, key=lambda o: -o.z_position)
        
        for obs in sorted_obstacles:
            self._draw_obstacle(img, obs, perspective)
        
        return img
    
    def _draw_background(self, img: np.ndarray, perspective: str):
        """Draw game background with grid."""
        if perspective == "behind":
            horizon_y = self.height // 3
            cv2.rectangle(img, (0, 0), (self.width, horizon_y), (20, 10, 30), -1)
            
            pts = np.array([
                [0, self.height],
                [self.width, self.height],
                [self.width, horizon_y],
                [0, horizon_y]
            ], np.int32)
            cv2.fillPoly(img, [pts], (40, 20, 50))
            
            for i in range(self.num_lanes + 1):
                x_bottom = i * self.lane_width
                x_top = self.width // 2 + (i - self.num_lanes // 2) * (self.lane_width // 3)
                cv2.line(img, (x_bottom, self.height), (x_top, horizon_y), (80, 40, 100), 2)
            
            for i in range(10):
                y = horizon_y + (self.height - horizon_y) * i // 10
                cv2.line(img, (0, y), (self.width, y), (60, 30, 80), 1)
                
        elif perspective == "top":
            img[:] = (30, 15, 40)
            for i in range(self.num_lanes + 1):
                x = i * self.lane_width
                cv2.line(img, (x, 0), (x, self.height), (80, 40, 100), 2)
                
        elif perspective == "side":
            img[:] = (25, 12, 35)
            ground_y = self.height - 100
            cv2.line(img, (0, ground_y), (self.width, ground_y), (100, 50, 120), 3)
            
        elif perspective == "isometric":
            img[:] = (20, 10, 30)
    
    def _draw_obstacle(self, img: np.ndarray, obs: Obstacle, perspective: str):
        """Draw a single obstacle with perspective."""
        scale = 1.0 - (obs.z_position / 150)
        scale = max(0.3, min(1.0, scale))
        
        w = int(obs.width * scale)
        h = int(obs.height * scale)
        
        if perspective == "behind":
            horizon_y = self.height // 3
            y_range = self.height - horizon_y
            
            center_x = self.width // 2
            lane_offset = (obs.lane - 1) * self.lane_width * scale
            x = int(center_x + lane_offset - w // 2)
            
            y = int(horizon_y + y_range * (1 - obs.z_position / 100) - h)
            
        elif perspective == "top":
            x = obs.x
            y = int(obs.z_position * self.height / 100)
            h = obs.depth
            
        elif perspective == "side":
            x = int(obs.z_position * self.width / 100)
            y = obs.y
            
        else:
            x, y = obs.x, obs.y
        
        color_bgr = obs.color[::-1]
        
        if perspective == "behind" and obs.z_position < 80:
            depth_offset = int(obs.depth * scale * 0.3)
            dark_color = tuple(max(0, c - 60) for c in color_bgr)
            
            top_pts = np.array([
                [x, y],
                [x + w, y],
                [x + w - depth_offset, y - depth_offset],
                [x - depth_offset, y - depth_offset]
            ], np.int32)
            cv2.fillPoly(img, [top_pts], dark_color)
            
            cv2.rectangle(img, (x, y), (x + w, y + h), color_bgr, -1)
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), 2)
        else:
            cv2.rectangle(img, (x, y), (x + w, y + h), color_bgr, -1)
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), 1)
    
    def export_level_data(self, obstacles: List[Obstacle], filepath: str):
        """Export obstacle data as JSON for game engine."""
        level_data = {
            "level_info": {
                "width": self.width,
                "height": self.height,
                "num_lanes": self.num_lanes
            },
            "obstacles": [obs.to_dict() for obs in obstacles]
        }
        
        with open(filepath, 'w') as f:
            json.dump(level_data, f, indent=2)
        
        return level_data


def generate_game_frames(output_dir: str, num_frames: int = 10):
    """Generate multiple game frames with obstacles."""
    os.makedirs(output_dir, exist_ok=True)
    
    generator = ObstacleGenerator(width=800, height=600)
    all_level_data = []
    
    perspectives = ["behind", "top", "side", "isometric"]
    
    for i in range(num_frames):
        obstacles = generator.generate_wave(num_obstacles=random.randint(3, 7))
        
        for perspective in perspectives:
            frame = generator.render_frame(obstacles, perspective)
            
            filename = f"frame_{i:03d}_{perspective}.png"
            cv2.imwrite(os.path.join(output_dir, filename), frame)
        
        level_file = os.path.join(output_dir, f"level_{i:03d}.json")
        level_data = generator.export_level_data(obstacles, level_file)
        all_level_data.append(level_data)
        
        print(f"Generated frame {i+1}/{num_frames} with {len(obstacles)} obstacles")
    
    return all_level_data


if __name__ == "__main__":
    output_dir = "../output/generated_frames"
    generate_game_frames(output_dir, num_frames=5)
    print(f"\nFrames saved to: {output_dir}")
