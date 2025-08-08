import pygame
import moderngl
import numpy as np
import math
import time
from render import draw_text  
import re

class EntityCard:
    def __init__(self, entity, price, card_width=220, card_height=280, model_offset=(0, 0, 0), scale=1.0):
        self.entity = entity
        self.price = price
        self.card_width = card_width
        self.card_height = card_height
        self.model_offset = np.array(model_offset)
        self.background_color = (0, 0, 0)  
        self.border_color = (0, 255, 0)   
        self.text_color = (0, 255, 0)     
        self.preview_size = min(card_width - 40, card_height - 100)  
        self.preview_scale = 800  
        self.rotation_speed = 30  
        self.start_time = time.time()
        self.current_rotation = 0
        self.scale = scale
        self.card_entity_vertices = entity.local_vertices.copy() * self.scale
        self.card_entity_edges = entity.edges.copy()
        
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
            [0, 1, 0],
            [-sin_theta, 0, cos_theta]
        ])
    
    def _apply_offset_to_vertices(self, vertices):
        if len(vertices) == 0:
            return vertices
        return vertices + self.model_offset
    
    def _project_to_card_space(self, vertices, card_x, card_y):
        if len(vertices) == 0:
            return np.array([])
        preview_center_x = card_x + self.card_width // 2
        preview_center_y = card_y + 60 + self.preview_size // 2
        z_values = np.maximum(vertices[:, 2] + 3, 0.1)
        factor = self.preview_scale / z_values
        screen_x = preview_center_x + vertices[:, 0] * factor * 0.3
        screen_y = preview_center_y + vertices[:, 1] * factor * 0.3 
        return np.column_stack((screen_x, screen_y))
    
    def _render_model_edges(self, ctx, line_prog, vertices, edges, color, card_x, card_y):
        rotation_matrix = self._get_rotation_matrix(self.current_rotation)
        offset_vertices = self._apply_offset_to_vertices(vertices)
        rotated_vertices = np.dot(offset_vertices, rotation_matrix.T)
        projected_points = self._project_to_card_space(rotated_vertices, card_x, card_y)
        if len(projected_points) == 0:
            return
        edge_vertices = []
        for start_idx, end_idx in edges:
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
        line_prog['color'].value = (color[0]/255.0, color[1]/255.0, color[2]/255.0)
        vertices_array = np.array(normalized_vertices, dtype='f4')
        vbo = ctx.buffer(vertices_array.tobytes())
        vao = ctx.vertex_array(line_prog, [(vbo, '2f', 'in_vert')])
        ctx.line_width = 2.0
        vao.render(moderngl.LINES)
        vao.release()
        vbo.release()
    
    def _render_3d_preview(self, ctx, line_prog, card_x, card_y):
        self.update_rotation()
        self._render_model_edges(ctx, line_prog, self.card_entity_vertices, 
                                self.card_entity_edges, self.entity.color, card_x, card_y)
    
    def _draw_card_background(self, ctx, line_prog, card_x, card_y):
        from render import draw_rect 
        draw_rect(ctx, (card_x, card_y, self.card_width, self.card_height), 
                 self.background_color, line_prog, filled=True)
        draw_rect(ctx, (card_x, card_y, self.card_width, self.card_height), 
                 self.border_color, line_prog, filled=False)

    
    def _draw_card_text(self, ctx, line_prog, card_x, card_y):
        from render import draw_rect
        entity_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', self.entity.__class__.__name__).capitalize()
        draw_text(ctx, entity_name, (card_x + 50, card_y + 10), self.text_color, font_size=30)
        stats_y = card_y + 30 + self.preview_size
        
        left_stats = [
            f"Health: {self.entity.max_health}",
            f"Range: {self.entity.range}",
            f"Speed: {self.entity.speed * 100:.1f}",
        ]
        
        right_stats = [
            f"Type: {self.entity.unit_type.capitalize()}",
            f"Damage: {self.entity.damage}",
            f"Visibility: {self.entity.visibility}",
        ]
        
        for i, line in enumerate(left_stats):
            draw_text(ctx, line, (card_x + 10, stats_y + i * 16), self.text_color, font_size=16)
        
        right_x = card_x + 130  
        for i, line in enumerate(right_stats):
            draw_text(ctx, line, (right_x, stats_y + i * 16), self.text_color, font_size=16)

        if len(str(self.price)) > 1:
            draw_text(ctx, f"${self.price}", (card_x + 3, card_y + 10), self.text_color, font_size=30)
        else:
            draw_text(ctx, f"${self.price}", (card_x + 8, card_y + 10), self.text_color, font_size=30)

        draw_rect(ctx, (card_x, card_y , 40, 40), (0, 255, 0), line_prog, filled=False)

    def draw(self, ctx, line_prog, card_x, card_y):
        self._draw_card_background(ctx, line_prog, card_x, card_y)
        self._render_3d_preview(ctx, line_prog, card_x, card_y)
        self._draw_card_text(ctx, line_prog, card_x, card_y)
    
    def is_point_inside(self, x, y, card_x, card_y):
        return (card_x <= x <= card_x + self.card_width and 
                card_y <= y <= card_y + self.card_height)
    
    def update_entity(self, new_entity):
        self.entity = new_entity
        self.card_entity_vertices = new_entity.local_vertices.copy() * self.scale
        self.card_entity_edges = new_entity.edges.copy()
    
    def set_model_offset(self, offset):
        self.model_offset = np.array(offset)
    
    def get_model_offset(self):
        return self.model_offset.copy()


class TankEntityCard(EntityCard):
    def __init__(self, entity, price, card_width=220, card_height=280, model_offset=(0, 0, 0), scale=1.0, y_off = 0):
        super().__init__(entity, price, card_width, card_height, model_offset, scale)
        self.turret_rotation_speed = 15
        self.y_off_cannon = y_off
        self._initialize_turret_data()
    
    def _initialize_turret_data(self):
        self.has_turret = hasattr(self.entity, 'tank_vertices') and hasattr(self.entity, 'tank_edges')
        if self.has_turret:
            self.turret_vertices = self.entity.tank_vertices.copy() * self.scale
            self.turret_edges = self.entity.tank_edges.copy()
            self.turret_rotation_offset = getattr(self.entity, 'turret_rotation', 0)
            self.turret_color = getattr(self.entity, 'turret_color', self.entity.color)
        else:
            self.turret_vertices = None
            self.turret_edges = None
            self.turret_rotation_offset = 0
            self.turret_color = self.entity.color
    
    def _render_model_edges_with_rotation(self, ctx, line_prog, vertices, edges, color, card_x, card_y, rotation_offset=0):
        total_rotation = self.current_rotation + rotation_offset
        rotation_matrix = self._get_rotation_matrix(total_rotation)
        offset_vertices = self._apply_offset_to_vertices(vertices)
        rotated_vertices = np.dot(offset_vertices, rotation_matrix.T)
        projected_points = self._project_to_card_space(rotated_vertices, card_x, card_y)
        if len(projected_points) == 0:
            return
        edge_vertices = []
        for start_idx, end_idx in edges:
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
        line_prog['color'].value = (color[0]/255.0, color[1]/255.0, color[2]/255.0)
        vertices_array = np.array(normalized_vertices, dtype='f4')
        vbo = ctx.buffer(vertices_array.tobytes())
        vao = ctx.vertex_array(line_prog, [(vbo, '2f', 'in_vert')])
        ctx.line_width = 2.0
        vao.render(moderngl.LINES)
        vao.release()
        vbo.release()
    
    def _render_3d_preview(self, ctx, line_prog, card_x, card_y):
        self.update_rotation()
        
        self._render_model_edges(ctx, line_prog, self.card_entity_vertices, 
                                self.card_entity_edges, self.entity.color, card_x, card_y)
        
        if self.has_turret:
            current_time = time.time()
            elapsed = current_time - self.start_time
            turret_rotation = (elapsed * self.rotation_speed) % 360
            turret_rotation += self.turret_rotation_offset
            
            rotation_matrix = self._get_rotation_matrix(turret_rotation)
            offset_vertices = self._apply_offset_to_vertices(self.turret_vertices)
            rotated_vertices = np.dot(offset_vertices, rotation_matrix.T)
            projected_points = self._project_to_card_space(rotated_vertices, card_x, card_y)
            
            if len(projected_points) > 0:
                edge_vertices = []
                for start_idx, end_idx in self.turret_edges:
                    if start_idx < len(projected_points) and end_idx < len(projected_points):
                        edge_vertices.extend([
                            projected_points[start_idx],
                            projected_points[end_idx]
                        ])
                
                if edge_vertices:
                    viewport_width, viewport_height = ctx.viewport[2:4]
                    normalized_vertices = []
                    for point in edge_vertices:
                        norm_x = (point[0] / viewport_width) * 2 - 1
                        norm_y = -((point[1] / viewport_height) * 2 - 1)
                        normalized_vertices.extend([norm_x, norm_y])
                    
                    line_prog['color'].value = (self.turret_color[0]/255.0, 
                                            self.turret_color[1]/255.0, 
                                            self.turret_color[2]/255.0)
                    vertices_array = np.array(normalized_vertices, dtype='f4')
                    vbo = ctx.buffer(vertices_array.tobytes())
                    vao = ctx.vertex_array(line_prog, [(vbo, '2f', 'in_vert')])
                    ctx.line_width = 2.0
                    vao.render(moderngl.LINES)
                    vao.release()
                    vbo.release()
    

    
    def update_entity(self, new_entity):
        super().update_entity(new_entity)
        self._initialize_turret_data()
    
    def set_turret_color(self, color):
        self.turret_color = color
    
    def get_turret_color(self):
        return self.turret_color
    
    def set_turret_rotation_speed(self, speed):
        self.turret_rotation_speed = speed
    
    def get_turret_rotation_speed(self):
        return self.turret_rotation_speed
    
    def set_turret_rotation_offset(self, offset):
        self.turret_rotation_offset = offset
    
    def get_turret_rotation_offset(self):
        return self.turret_rotation_offset
    
class ArtilleryEntityCard(EntityCard):
    def __init__(self, entity, price, card_width=220, card_height=280, model_offset=(0, 0, 0), scale=1.0, cannon_offset=(0.2, 0.0, 0.1)):
        super().__init__(entity, price, card_width, card_height, model_offset, scale)
        self.cannon_rotation_speed = 15
        self.cannon_display_offset = np.array(cannon_offset)
        self._initialize_cannon_data()
    
    def _initialize_cannon_data(self):
        self.has_cannon = hasattr(self.entity, 'cannon_vertices') and hasattr(self.entity, 'cannon_edges')
        if self.has_cannon:
            self.cannon_vertices = self.entity.cannon_vertices.copy() * self.scale
            self.cannon_edges = self.entity.cannon_edges.copy()
            self.cannon_rotation_offset = getattr(self.entity, 'cannon_rotation', 0)
            self.cannon_color = getattr(self.entity, 'cannon_color', self.entity.color)
            self.cannon_offset = getattr(self.entity, 'cannon_offset', 0.4)
        else:
            self.cannon_vertices = None
            self.cannon_edges = None
            self.cannon_rotation_offset = 0
            self.cannon_color = self.entity.color
            self.cannon_offset = 0.4
    
    def _render_cannon_edges(self, ctx, line_prog, vertices, edges, color, card_x, card_y, rotation_angle):

        offset_vertices = vertices + self.cannon_display_offset
        
        offset_vertices = offset_vertices + self.model_offset
        
        rotation_matrix = self._get_rotation_matrix(rotation_angle)
        rotated_vertices = np.dot(offset_vertices, rotation_matrix.T)
        
        projected_points = self._project_to_card_space(rotated_vertices, card_x, card_y)
        
        if len(projected_points) == 0:
            return
            
        edge_vertices = []
        for start_idx, end_idx in edges:
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
        
        line_prog['color'].value = (color[0]/255.0, color[1]/255.0, color[2]/255.0)
        vertices_array = np.array(normalized_vertices, dtype='f4')
        vbo = ctx.buffer(vertices_array.tobytes())
        vao = ctx.vertex_array(line_prog, [(vbo, '2f', 'in_vert')])
        ctx.line_width = 2.0
        vao.render(moderngl.LINES)
        vao.release()
        vbo.release()
    
    def _render_3d_preview(self, ctx, line_prog, card_x, card_y):
        self.update_rotation()
        
        current_time = time.time()
        elapsed = current_time - self.start_time
        total_rotation = (elapsed * self.rotation_speed) % 360
        total_rotation += self.cannon_rotation_offset
        
        rotation_matrix = self._get_rotation_matrix(total_rotation)
        offset_vertices = self._apply_offset_to_vertices(self.card_entity_vertices)
        rotated_vertices = np.dot(offset_vertices, rotation_matrix.T)
        projected_points = self._project_to_card_space(rotated_vertices, card_x, card_y)
        
        if len(projected_points) > 0:
            edge_vertices = []
            for start_idx, end_idx in self.card_entity_edges:
                if start_idx < len(projected_points) and end_idx < len(projected_points):
                    edge_vertices.extend([
                        projected_points[start_idx],
                        projected_points[end_idx]
                    ])
            
            if edge_vertices:
                viewport_width, viewport_height = ctx.viewport[2:4]
                normalized_vertices = []
                for point in edge_vertices:
                    norm_x = (point[0] / viewport_width) * 2 - 1
                    norm_y = -((point[1] / viewport_height) * 2 - 1)
                    normalized_vertices.extend([norm_x, norm_y])
                
                line_prog['color'].value = (self.entity.color[0]/255.0, 
                                          self.entity.color[1]/255.0, 
                                          self.entity.color[2]/255.0)
                vertices_array = np.array(normalized_vertices, dtype='f4')
                vbo = ctx.buffer(vertices_array.tobytes())
                vao = ctx.vertex_array(line_prog, [(vbo, '2f', 'in_vert')])
                ctx.line_width = 2.0
                vao.render(moderngl.LINES)
                vao.release()
                vbo.release()
        
        if self.has_cannon:
            self._render_cannon_edges(ctx, line_prog, self.cannon_vertices, 
                                    self.cannon_edges, self.cannon_color, 
                                    card_x, card_y, total_rotation)
    
    def update_entity(self, new_entity):
        super().update_entity(new_entity)
        self._initialize_cannon_data()
    
    def set_cannon_color(self, color):
        self.cannon_color = color
    
    def get_cannon_color(self):
        return self.cannon_color
    
    def set_cannon_rotation_speed(self, speed):
        self.cannon_rotation_speed = speed
    
    def get_cannon_rotation_speed(self):
        return self.cannon_rotation_speed
    
    def set_cannon_rotation_offset(self, offset):
        self.cannon_rotation_offset = offset
    
    def get_cannon_rotation_offset(self):
        return self.cannon_rotation_offset
    
    def set_cannon_offset(self, offset):
        self.cannon_display_offset = np.array(offset)
    
    def get_cannon_offset(self):
        return self.cannon_display_offset.copy()
    
    def set_entity_cannon_offset(self, offset):
        """Set the entity's original cannon_offset (different from display offset)"""
        self.cannon_offset = offset

    

class HelicopterEntityCard(EntityCard):
    def __init__(self, entity, price, card_width=220, card_height=280, model_offset=(0, 0, 0), scale=1.0, blades_offset=(0.0, 0.0, 0.3)):
        super().__init__(entity, price, card_width, card_height, model_offset, scale)
        self.blades_rotation_speed = 15
        self.blades_display_offset = np.array(blades_offset)  
        self._initialize_blades_data()
    
    def _initialize_blades_data(self):
        self.has_blades = hasattr(self.entity, 'blade_vertices') and hasattr(self.entity, 'blade_edges')
        if self.has_blades:
            self.blades_vertices = self.entity.blade_vertices.copy() * self.scale
            self.blades_edges = self.entity.blade_edges.copy()
            self.blades_rotation_offset = getattr(self.entity, 'blades_rotation', 0)
            self.blades_color = getattr(self.entity, 'blades_color', self.entity.color)
            self.blades_offset = getattr(self.entity, 'blades_offset', 0.4)
        else:
            self.blades_vertices = None
            self.blades_edges = None
            self.blades_rotation_offset = 0
            self.blades_color = self.entity.color
            self.blades_offset = 0.4
    
    def _render_blades_edges(self, ctx, line_prog, vertices, edges, color, card_x, card_y, rotation_angle):

        offset_vertices = vertices + self.blades_display_offset
        
        offset_vertices = offset_vertices + self.model_offset
        
        rotation_matrix = self._get_rotation_matrix(rotation_angle)
        rotated_vertices = np.dot(offset_vertices, rotation_matrix.T)
        
        projected_points = self._project_to_card_space(rotated_vertices, card_x, card_y)
        
        if len(projected_points) == 0:
            return
            
        edge_vertices = []
        for start_idx, end_idx in edges:
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
        
        line_prog['color'].value = (color[0]/255.0, color[1]/255.0, color[2]/255.0)
        vertices_array = np.array(normalized_vertices, dtype='f4')
        vbo = ctx.buffer(vertices_array.tobytes())
        vao = ctx.vertex_array(line_prog, [(vbo, '2f', 'in_vert')])
        ctx.line_width = 2.0
        vao.render(moderngl.LINES)
        vao.release()
        vbo.release()
    
    def _render_3d_preview(self, ctx, line_prog, card_x, card_y):
        self.update_rotation()
        
        current_time = time.time()
        elapsed = current_time - self.start_time
        total_rotation = (elapsed * self.rotation_speed) % 360
        total_rotation += self.blades_rotation_offset
        
        rotation_matrix = self._get_rotation_matrix(total_rotation)
        offset_vertices = self._apply_offset_to_vertices(self.card_entity_vertices)
        rotated_vertices = np.dot(offset_vertices, rotation_matrix.T)
        projected_points = self._project_to_card_space(rotated_vertices, card_x, card_y)
        
        if len(projected_points) > 0:
            edge_vertices = []
            for start_idx, end_idx in self.card_entity_edges:
                if start_idx < len(projected_points) and end_idx < len(projected_points):
                    edge_vertices.extend([
                        projected_points[start_idx],
                        projected_points[end_idx]
                    ])
            
            if edge_vertices:
                viewport_width, viewport_height = ctx.viewport[2:4]
                normalized_vertices = []
                for point in edge_vertices:
                    norm_x = (point[0] / viewport_width) * 2 - 1
                    norm_y = -((point[1] / viewport_height) * 2 - 1)
                    normalized_vertices.extend([norm_x, norm_y])
                
                line_prog['color'].value = (self.entity.color[0]/255.0, 
                                          self.entity.color[1]/255.0, 
                                          self.entity.color[2]/255.0)
                vertices_array = np.array(normalized_vertices, dtype='f4')
                vbo = ctx.buffer(vertices_array.tobytes())
                vao = ctx.vertex_array(line_prog, [(vbo, '2f', 'in_vert')])
                ctx.line_width = 2.0
                vao.render(moderngl.LINES)
                vao.release()
                vbo.release()
        
        if self.has_blades:
            self._render_blades_edges(ctx, line_prog, self.blades_vertices, 
                                    self.blades_edges, self.blades_color, 
                                    card_x, card_y, total_rotation)
    
    def update_entity(self, new_entity):
        super().update_entity(new_entity)
        self._initialize_blades_data()
    
    def set_blades_color(self, color):
        self.blades_color = color
    
    def get_blades_color(self):
        return self.blades_color
    
    def set_blades_rotation_speed(self, speed):
        self.blades_rotation_speed = speed
    
    def get_blades_rotation_speed(self):
        return self.blades_rotation_speed
    
    def set_blades_rotation_offset(self, offset):
        self.blades_rotation_offset = offset
    
    def get_blades_rotation_offset(self):
        return self.blades_rotation_offset
    
    def set_blades_offset(self, offset):
        self.blades_display_offset = np.array(offset)
    
    def get_blades_offset(self):
        return self.blades_display_offset.copy()
    
    def set_entity_blades_offset(self, offset):
        """Set the entity's original blades_offset (different from display offset)"""
        self.blades_offset = offset