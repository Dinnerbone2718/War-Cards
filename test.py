import numpy as np
import math
import time
import pygame
import moderngl
from render import *

scale = 2
model = "models/campeign_board.obj"

def load_obj_for_wireframe(obj_file_path, save_centered=False):
    vertices = []
    faces = []
    
    with open(obj_file_path, 'r') as file:
        for line in file:
            if line.startswith('v '):
                values = line.split()[1:]
                vertex = [float(values[0])*scale, float(values[1])*scale, float(values[2])*scale]
                vertices.append(vertex)
            elif line.startswith('f '):
                values = line.split()[1:]
                face_vertices = []
                for value in values:
                    vertex_idx = int(value.split('/')[0]) - 1
                    face_vertices.append(vertex_idx)
                faces.append(face_vertices)
    
    edges = set()
    for face in faces:
        for i in range(len(face)):
            v1, v2 = face[i], face[(i + 1) % len(face)]
            edge = (min(v1, v2), max(v1, v2))
            edges.add(edge)
    
    edges_list = list(edges)
    vertices_array = np.array(vertices)
    
    center = (vertices_array.max(axis=0) + vertices_array.min(axis=0)) / 2
    vertices_array = vertices_array - center
    
    if save_centered:
        centered_vertex_data = create_vertex_data(vertices_array, edges_list)
        np.savetxt("vertexOutput.txt", centered_vertex_data, fmt="%.4f")
        print(f"Saved centered vertex data to vertexOutput.txt")
    
    return vertices_array, edges_list


def create_vertex_data(verts, edges):
    edge_verts = np.zeros((len(edges), 2, 3), dtype='f4')
    
    for i, (start_idx, end_idx) in enumerate(edges):
        edge_verts[i, 0] = verts[start_idx]
        edge_verts[i, 1] = verts[end_idx]
    
    return edge_verts.reshape(-1, 3)


class ModelViewer:
    def __init__(self, obj_file_path, save_centered=False):
        self.local_vertices, self.edges = load_obj_for_wireframe(obj_file_path, save_centered)
        self.start_time = time.time()
        self.rotation_speed = 20
        self.current_rotation = 0
        self.model_offset = np.array([0, 0, 0])
        self.preview_scale = 1200
        self.color = (0, 255, 0)
        
    def update_rotation(self):
        current_time = time.time()
        elapsed = current_time - self.start_time
        self.current_rotation = (elapsed * self.rotation_speed) % 360
        
    def _get_rotation_matrix(self, angle_degrees):
        angle_radians = math.radians(angle_degrees)
        cos_theta = math.cos(angle_radians)
        sin_theta = math.sin(angle_radians)
        return np.array([
            [cos_theta, 0, sin_theta],
            [0, -1, 0],
            [-sin_theta, 0, cos_theta]
        ])
    
    def _apply_offset_to_vertices(self, vertices):
        if len(vertices) == 0:
            return vertices
        return vertices + self.model_offset
    
    def _project_to_screen_space(self, vertices, center_x, center_y):
        if len(vertices) == 0:
            return np.array([])
        
        z_values = np.maximum(vertices[:, 2] + 3, 0.1)
        factor = self.preview_scale / z_values
        
        screen_x = center_x + vertices[:, 0] * factor * 0.4
        screen_y = center_y + vertices[:, 1] * factor * 0.4
        
        return np.column_stack((screen_x, screen_y))
    
    def _render_model_edges(self, ctx, line_prog, center_x, center_y):
        self.update_rotation()
        
        rotation_matrix = self._get_rotation_matrix(self.current_rotation)
        
        offset_vertices = self._apply_offset_to_vertices(self.local_vertices)
        rotated_vertices = np.dot(offset_vertices, rotation_matrix.T)
        
        projected_points = self._project_to_screen_space(rotated_vertices, center_x, center_y)
        
        if len(projected_points) == 0:
            return
        
        edge_vertices = []
        for start_idx, end_idx in self.edges:
            if start_idx < len(projected_points) and end_idx < len(projected_points):
                edge_vertices.extend([
                    projected_points[start_idx],
                    projected_points[end_idx]
                ])
        
        if not edge_vertices:
            return
        
        viewport_width, viewport_height = ctx.viewport[2:4]
        normalized_vertices = []
        for point in edge_vertices:
            norm_x = (point[0] / viewport_width) * 2 - 1
            norm_y = -((point[1] / viewport_height) * 2 - 1)
            normalized_vertices.extend([norm_x, norm_y])
        
        line_prog['color'].value = (self.color[0]/255.0, self.color[1]/255.0, self.color[2]/255.0)
        vertices_array = np.array(normalized_vertices, dtype='f4')
        vbo = ctx.buffer(vertices_array.tobytes())
        vao = ctx.vertex_array(line_prog, [(vbo, '2f', 'in_vert')])
        ctx.line_width = 2.0
        vao.render(moderngl.LINES)
        vao.release()
        vbo.release()
    
    def render_3d_model(self, ctx, line_prog, center_x, center_y):
        self._render_model_edges(ctx, line_prog, center_x, center_y)


def main():
    from pygame.locals import DOUBLEBUF, OPENGL, VIDEORESIZE
    global model
    
    width, height = 800, 600
    screen, ctx, line_prog = initialize_context(width, height)
    pygame.display.set_caption("3D Model Viewer - Menu Style")
    
    model_viewer = ModelViewer(model, save_centered=True)
    
    running = True
    clock = pygame.time.Clock()
    
    center_x = width // 2
    center_y = height // 2
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == VIDEORESIZE:
                width, height = event.size
                screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
                center_x = width // 2
                center_y = height // 2
        
        ctx.clear(0.1, 0.1, 0.1, 1.0)
        
        model_viewer.render_3d_model(ctx, line_prog, center_x, center_y)
        
        current_fps = clock.get_fps()
        pygame.display.set_caption(f"3D Model Viewer - Menu Style - FPS: {current_fps:.1f}")
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    main()