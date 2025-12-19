#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Infinite Runner Game Pipeline.

Complete pipeline for generating an infinite runner game:
1. Generate obstacle images with random positions
2. Detect and extract obstacle coordinates
3. Convert to 3D models using Image-to-3D
4. Run the game engine

Usage:
    python pipeline.py generate    - Generate obstacle frames
    python pipeline.py detect      - Detect obstacles in frames
    python pipeline.py convert3d   - Convert sprites to 3D models
    python pipeline.py demo        - Run game demo
    python pipeline.py full        - Run complete pipeline
"""

import os
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from obstacles.generator import ObstacleGenerator, generate_game_frames
from obstacles.detector import ObstacleDetector, process_game_frame
from models_3d.image_to_3d import ImageTo3DPipeline, ProceduralMeshGenerator
from game.engine import InfiniteRunnerEngine, CameraMode


class GamePipeline:
    """Complete pipeline for infinite runner game generation."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.frames_dir = self.output_dir / "frames"
        self.detected_dir = self.output_dir / "detected"
        self.sprites_dir = self.output_dir / "sprites"
        self.models_dir = self.output_dir / "models_3d"
        self.game_dir = self.output_dir / "game_output"
    
    def step1_generate_frames(self, num_frames: int = 10):
        """Step 1: Generate obstacle frames with multiple perspectives."""
        print("\n" + "=" * 60)
        print("STEP 1: Generating Obstacle Frames")
        print("=" * 60)
        
        self.frames_dir.mkdir(exist_ok=True)
        
        generator = ObstacleGenerator(width=800, height=600)
        all_levels = []
        
        perspectives = ["behind", "top", "side", "isometric"]
        
        for i in range(num_frames):
            obstacles = generator.generate_wave(num_obstacles=5)
            
            for perspective in perspectives:
                frame = generator.render_frame(obstacles, perspective)
                
                import cv2
                filename = f"frame_{i:03d}_{perspective}.png"
                cv2.imwrite(str(self.frames_dir / filename), frame)
            
            level_file = self.frames_dir / f"level_{i:03d}.json"
            level_data = generator.export_level_data(obstacles, str(level_file))
            all_levels.append(level_data)
            
            print(f"  Generated frame {i+1}/{num_frames} with {len(obstacles)} obstacles")
        
        manifest = {
            "num_frames": num_frames,
            "perspectives": perspectives,
            "levels": [f"level_{i:03d}.json" for i in range(num_frames)]
        }
        
        with open(self.frames_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"\nFrames saved to: {self.frames_dir}")
        return all_levels
    
    def step2_detect_obstacles(self):
        """Step 2: Detect obstacles and extract coordinates."""
        print("\n" + "=" * 60)
        print("STEP 2: Detecting Obstacles")
        print("=" * 60)
        
        self.detected_dir.mkdir(exist_ok=True)
        self.sprites_dir.mkdir(exist_ok=True)
        
        import cv2
        
        frame_files = sorted(self.frames_dir.glob("frame_*_behind.png"))
        
        if not frame_files:
            print("  No frames found. Run step1 first.")
            return []
        
        detector = ObstacleDetector(min_area=500)
        all_detections = []
        
        for frame_path in frame_files:
            print(f"  Processing: {frame_path.name}")
            
            frame_id = frame_path.stem.split("_")[1]
            
            image = cv2.imread(str(frame_path))
            obstacles = detector.detect(image)
            
            frame_sprites_dir = self.sprites_dir / f"frame_{frame_id}"
            sprite_paths = detector.extract_obstacle_sprites(
                image, obstacles, str(frame_sprites_dir)
            )
            
            coords = detector.export_coordinates(obstacles, image.shape)
            coords_file = self.detected_dir / f"coords_{frame_id}.json"
            with open(coords_file, 'w') as f:
                json.dump(coords, f, indent=2)
            
            viz = detector.visualize_detections(image, obstacles)
            viz_path = self.detected_dir / f"detected_{frame_id}.png"
            cv2.imwrite(str(viz_path), viz)
            
            all_detections.append({
                "frame_id": frame_id,
                "num_obstacles": len(obstacles),
                "sprites": sprite_paths,
                "coordinates": str(coords_file)
            })
            
            print(f"    Found {len(obstacles)} obstacles")
        
        with open(self.detected_dir / "detections_manifest.json", 'w') as f:
            json.dump(all_detections, f, indent=2)
        
        print(f"\nDetections saved to: {self.detected_dir}")
        print(f"Sprites saved to: {self.sprites_dir}")
        
        return all_detections
    
    def step3_convert_to_3d(self):
        """Step 3: Convert obstacle sprites to 3D models."""
        print("\n" + "=" * 60)
        print("STEP 3: Converting to 3D Models")
        print("=" * 60)
        
        self.models_dir.mkdir(exist_ok=True)
        
        pipeline = ImageTo3DPipeline(preferred_model="procedural")
        
        sprite_dirs = sorted(self.sprites_dir.glob("frame_*"))
        
        if not sprite_dirs:
            print("  No sprites found. Run step2 first.")
            return []
        
        all_models = []
        
        for sprite_dir in sprite_dirs:
            print(f"  Processing: {sprite_dir.name}")
            
            frame_id = sprite_dir.name.split("_")[1]
            output_dir = self.models_dir / f"models_{frame_id}"
            
            coords_file = self.detected_dir / f"coords_{frame_id}.json"
            
            results = pipeline.convert_sprites(
                str(sprite_dir),
                str(output_dir),
                str(coords_file) if coords_file.exists() else None
            )
            
            all_models.extend(results)
        
        with open(self.models_dir / "models_manifest.json", 'w') as f:
            json.dump(all_models, f, indent=2)
        
        print(f"\n3D models saved to: {self.models_dir}")
        
        return all_models
    
    def step4_run_game_demo(self, num_frames: int = 120):
        """Step 4: Run game engine demo."""
        print("\n" + "=" * 60)
        print("STEP 4: Running Game Demo")
        print("=" * 60)
        
        self.game_dir.mkdir(exist_ok=True)
        
        import cv2
        
        engine = InfiniteRunnerEngine(width=800, height=600)
        engine.start_game()
        
        camera_modes = [
            CameraMode.BEHIND,
            CameraMode.TOP_DOWN,
            CameraMode.SIDE,
            CameraMode.ISOMETRIC
        ]
        
        frames_per_mode = num_frames // len(camera_modes)
        
        for i in range(num_frames):
            mode_idx = i // frames_per_mode
            engine.set_camera_mode(camera_modes[mode_idx % len(camera_modes)])
            
            if i % 30 == 10:
                engine.handle_input("left")
            elif i % 30 == 20:
                engine.handle_input("right")
            elif i % 40 == 15:
                engine.handle_input("jump")
            
            engine.update(0.033)
            
            frame = engine.render_frame()
            cv2.imwrite(str(self.game_dir / f"game_{i:04d}.png"), frame)
            
            if i % 30 == 0:
                print(f"  Frame {i}/{num_frames} - Score: {engine.player.score}")
        
        state = engine.export_game_state()
        with open(self.game_dir / "final_state.json", 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"\nGame demo saved to: {self.game_dir}")
        print(f"Final score: {engine.player.score}")
        
        return state
    
    def run_full_pipeline(self, num_frames: int = 5):
        """Run the complete pipeline."""
        print("\n" + "=" * 60)
        print("INFINITE RUNNER GAME PIPELINE")
        print("=" * 60)
        
        self.step1_generate_frames(num_frames)
        self.step2_detect_obstacles()
        self.step3_convert_to_3d()
        self.step4_run_game_demo()
        
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        
        summary = {
            "output_directory": str(self.output_dir),
            "directories": {
                "frames": str(self.frames_dir),
                "detected": str(self.detected_dir),
                "sprites": str(self.sprites_dir),
                "models_3d": str(self.models_dir),
                "game": str(self.game_dir)
            }
        }
        
        with open(self.output_dir / "pipeline_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nAll outputs saved to: {self.output_dir}")
        
        return summary


def main():
    parser = argparse.ArgumentParser(description="Infinite Runner Game Pipeline")
    parser.add_argument("command", nargs="?", default="full",
                       choices=["generate", "detect", "convert3d", "demo", "full"],
                       help="Pipeline step to run")
    parser.add_argument("--frames", type=int, default=5,
                       help="Number of frames to generate")
    parser.add_argument("--output", type=str, default="output",
                       help="Output directory")
    
    args = parser.parse_args()
    
    pipeline = GamePipeline(args.output)
    
    if args.command == "generate":
        pipeline.step1_generate_frames(args.frames)
    elif args.command == "detect":
        pipeline.step2_detect_obstacles()
    elif args.command == "convert3d":
        pipeline.step3_convert_to_3d()
    elif args.command == "demo":
        pipeline.step4_run_game_demo()
    else:
        pipeline.run_full_pipeline(args.frames)


if __name__ == "__main__":
    main()
