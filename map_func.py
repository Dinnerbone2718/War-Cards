import numpy as np
from perlin_noise import PerlinNoise
import random


def get_ground(grid_size=20, scale=5.0, height_variation=0.5, seed=100):
    noise = PerlinNoise(octaves=6, seed=seed)

    raw_vertices = []
    index_map = {}
    current_index = 0

    for z in range(grid_size):
        for x in range(grid_size):
            nx = x / grid_size
            nz = z / grid_size
            y = min(0,noise([nx, nz]) * height_variation - 1.5)
            raw_vertices.append([x * scale, y, z * scale])
            index_map[(x, z)] = current_index
            current_index += 1

    vertices = np.array(raw_vertices)
    edges = []

    for z in range(grid_size):
        for x in range(grid_size):
            if (x, z) in index_map:
                idx = index_map[(x, z)]
                if (x + 1, z) in index_map:
                    edges.append((idx, index_map[(x + 1, z)]))
                if (x, z + 1) in index_map:
                    edges.append((idx, index_map[(x, z + 1)]))

    return vertices, edges



def get_shoreline(grid_size=20, scale=5.0, height_variation=0.5, seed=100, shore_flatten_distance=0.4):
    noise = PerlinNoise(octaves=6, seed=seed)
    shoreline_noise = PerlinNoise(octaves=3, seed=seed + 1)
    detail_noise = PerlinNoise(octaves=8, seed=seed + 2)
   
    raw_vertices = []
    index_map = {}
    current_index = 0
   
    for z in range(grid_size):
        for x in range(grid_size):
            nx = x / grid_size
            nz = z / grid_size
           
            base_height = noise([nx, nz]) * height_variation - 1.5
           
            shoreline_major = shoreline_noise([nz * 2]) * 0.4  
            shoreline_detail = detail_noise([nz * 6]) * 0.1  
           
            shoreline_pos = 0.75 + shoreline_major + shoreline_detail
            shoreline_pos = max(0.3, min(0.9, shoreline_pos))  
           
            distance_from_right = (grid_size - 1 - x) / grid_size
           
            if distance_from_right < (1 - shoreline_pos):
                continue
           
            distance_from_shore = distance_from_right - (1 - shoreline_pos)
            
            if distance_from_shore <= shore_flatten_distance:
                flatten_factor = distance_from_shore / shore_flatten_distance
            else:
                flatten_factor = 1.0
           
            y = base_height * flatten_factor
            y = min(0, y)
           
            raw_vertices.append([x * scale, y, z * scale])
            index_map[(x, z)] = current_index
            current_index += 1
   
    vertices = np.array(raw_vertices)
    edges = []
   
    for z in range(grid_size):
        for x in range(grid_size):
            if (x, z) in index_map:
                idx = index_map[(x, z)]
                if (x + 1, z) in index_map:
                    edges.append((idx, index_map[(x + 1, z)]))
                if (x, z + 1) in index_map:
                    edges.append((idx, index_map[(x, z + 1)]))
   
    return vertices, edges

def get_water_surface(grid_size=20, scale=5.0, height_variation=0.5, seed=100, shore_flatten_distance=0.4):
    shoreline_noise = PerlinNoise(octaves=3, seed=seed + 1)
    detail_noise = PerlinNoise(octaves=8, seed=seed + 2)

    raw_vertices = []
    index_map = {}
    current_index = 0

    water_height = 0 

    for z in range(grid_size):
        for x in range(grid_size):
            nx = x / grid_size
            nz = z / grid_size

            shoreline_major = shoreline_noise([nz * 2]) * 0.4
            shoreline_detail = detail_noise([nz * 6]) * 0.1

            shoreline_pos = 0.75 + shoreline_major + shoreline_detail
            shoreline_pos = max(0.3, min(0.9, shoreline_pos))

            distance_from_right = (grid_size - 1 - x) / grid_size

            if distance_from_right >= (1 - shoreline_pos):
                continue

            raw_vertices.append([x * scale, water_height, z * scale])
            index_map[(x, z)] = current_index
            current_index += 1

    vertices = np.array(raw_vertices)
    edges = []

    for z in range(grid_size):
        for x in range(grid_size):
            if (x, z) in index_map:
                idx = index_map[(x, z)]
                if (x + 1, z) in index_map:
                    edges.append((idx, index_map[(x + 1, z)]))
                if (x, z + 1) in index_map:
                    edges.append((idx, index_map[(x, z + 1)]))

    return vertices, edges



def get_clouds(grid_size=20, scale=5.0, height_variation=0.5, seed=100, cloud_layers = 10):
    noise = PerlinNoise(octaves=3, seed=seed)

    raw_vertices = []
    index_map = {}
    current_index = 0

    cloud_layers = 4
    cloud_thickness = 4
    
    for y_layer in range(cloud_layers):
        for z in range(grid_size):
            for x in range(grid_size):
                nx = x / grid_size
                nz = z / grid_size
                ny = y_layer / cloud_layers
                density = noise([nx, ny, nz])
                if density > 0.15: 
                    y = -30 - (y_layer * cloud_thickness)
                    raw_vertices.append([x * scale, y, z * scale])
                    index_map[(x, y_layer, z)] = current_index
                    current_index += 1

    vertices = np.array(raw_vertices)
    edges = []

    for y_layer in range(cloud_layers):
        for z in range(grid_size):
            for x in range(grid_size):
                key = (x, y_layer, z)
                if key in index_map:
                    idx = index_map[key]
                    right = (x + 1, y_layer, z)
                    if right in index_map:
                        edges.append((idx, index_map[right]))
                    forward = (x, y_layer, z + 1)
                    if forward in index_map:
                        edges.append((idx, index_map[forward]))
                    up = (x, y_layer + 1, z)
                    if up in index_map:
                        edges.append((idx, index_map[up]))

    return vertices, edges


