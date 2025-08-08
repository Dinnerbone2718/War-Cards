import pygame
from pygame.locals import *
import moderngl
import numpy as np
import math

#NGL this code is a shitshow of ai and youtube tutorials and dumb decisions on my end. Im sorry about this mess


def initialize_context(width, height):
    pygame.init()
    screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    ctx = moderngl.create_context()
    line_prog = ctx.program(
        vertex_shader='''
            #version 330
            in vec2 in_vert;
            void main() {
                gl_Position = vec4(in_vert, 0.0, 1.0);
            }
        ''',
        fragment_shader='''
            #version 330
            uniform vec3 color;
            out vec4 fragColor;
            void main() {
                vec3 shiftedColor = vec3(color.x, color.y, color.z);
                fragColor = vec4(shiftedColor, 1.0);
            }
        '''
    )
    return screen, ctx, line_prog

def project(vertices, scale, viewport_width, viewport_height):
    z_values = np.maximum(vertices[:, 2], 0.1)
    factor = scale / z_values
    screen_x = vertices[:, 0] * factor / (viewport_width / 2)
    screen_y = -vertices[:, 1] * factor / (viewport_height / 2)
    return np.column_stack((screen_x, screen_y)).reshape(-1)

def create_vertex_data(verts, edges):
    edge_verts = np.zeros((len(edges), 2, 3), dtype='f4')
    for i, (start_idx, end_idx) in enumerate(edges):
        edge_verts[i, 0] = verts[start_idx]
        edge_verts[i, 1] = verts[end_idx]
    return edge_verts.reshape(-1, 3)

def render(ctx, vertex_data, color, scale, line_prog):
    if len(vertex_data) == 0:
        return
    viewport_width, viewport_height = ctx.viewport[2:4]
    projected_vertices = project(vertex_data, scale, viewport_width, viewport_height)
    line_prog['color'].value = (color[0]/255.0, color[1]/255.0, color[2]/255.0)
    vbo = ctx.buffer(projected_vertices.astype('f4').tobytes())
    vao = ctx.vertex_array(line_prog, [(vbo, '2f', 'in_vert')])
    vao.render(moderngl.LINES)
    vao.release()
    vbo.release()

def batch_render(ctx, objects_data, line_prog):
    for obj in objects_data:
        render(ctx, obj['vertex_data'], obj['color'], obj['scale'], line_prog)
    
def draw_rect(ctx, rect, color, line_prog, filled=False):
    x, y, w, h = rect
    viewport_width, viewport_height = ctx.viewport[2:4]
    x1 = (x / viewport_width) * 2 - 1
    y1 = -((y / viewport_height) * 2 - 1) 
    x2 = ((x + w) / viewport_width) * 2 - 1
    y2 = -(((y + h) / viewport_height) * 2 - 1)
    if filled:
        vertices = np.array([
            x1, y1,
            x2, y1,
            x2, y2,
            x2, y2,
            x1, y2,
            x1, y1
        ], dtype='f4')
        line_prog['color'].value = (color[0]/255.0, color[1]/255.0, color[2]/255.0)
        vbo = ctx.buffer(vertices.tobytes())
        vao = ctx.vertex_array(line_prog, [(vbo, '2f', 'in_vert')])
        vao.render(moderngl.TRIANGLES)
    else:
        vertices = np.array([
            x1, y1,
            x2, y1,
            x2, y2,
            x1, y2,
            x1, y1
        ], dtype='f4')
        line_prog['color'].value = (color[0]/255.0, color[1]/255.0, color[2]/255.0)
        vbo = ctx.buffer(vertices.tobytes())
        vao = ctx.vertex_array(line_prog, [(vbo, '2f', 'in_vert')])
        vao.render(moderngl.LINE_STRIP)
    vao.release()
    vbo.release()

def is_entity_hovered(ctx, vertex_data, mouse_pos, scale):
    if len(vertex_data) == 0:
        return False
    viewport_width, viewport_height = ctx.viewport[2:4]
    projected_vertices = project(vertex_data, scale, viewport_width, viewport_height)
    screen_points = projected_vertices.reshape(-1, 2)
    norm_mouse_x = (mouse_pos[0] / viewport_width) * 2 - 1
    norm_mouse_y = -((mouse_pos[1] / viewport_height) * 2 - 1) 
    min_x = np.min(screen_points[:, 0])
    max_x = np.max(screen_points[:, 0])
    min_y = np.min(screen_points[:, 1])
    max_y = np.max(screen_points[:, 1])
    is_hovered = (min_x <= norm_mouse_x <= max_x and 
                min_y <= norm_mouse_y <= max_y)
    return is_hovered

def render_with_hover(ctx, vertex_data, color, scale, line_prog, mouse_pos):
    if len(vertex_data) == 0:
        return False
    hovered = is_entity_hovered(ctx, vertex_data, mouse_pos, scale)
    render(ctx, vertex_data, color, scale, line_prog)
    return hovered

def clear_text_cache():
    if hasattr(draw_text, '_shader'):
        draw_text._shader = None
    if hasattr(draw_text, '_font_cache'):
        draw_text._font_cache.clear()

def draw_text(ctx, text, position, color, font_size=24, line_spacing=1.2, line_prog=None, font_path=None):
    import os
    if font_path is not None:
        font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), font_path)
    if not hasattr(draw_text, '_font_cache'):
        draw_text._font_cache = {}
        draw_text._shader = None
        pygame.font.init()
    
    font_key = (font_path, font_size)
    if font_key not in draw_text._font_cache:
        try:
            if font_path is None:
                font = pygame.font.Font(None, font_size)
            elif os.path.isfile(font_path):
                font = pygame.font.Font(font_path, font_size)
            else:
                try:
                    font = pygame.font.SysFont(font_path, font_size)
                except:
                    font = pygame.font.Font(None, font_size)
            draw_text._font_cache[font_key] = font
        except Exception as e:
            font = pygame.font.Font(None, font_size)
            draw_text._font_cache[font_key] = font
    
    font = draw_text._font_cache[font_key]
    
    if draw_text._shader is None:
        draw_text._shader = ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_vert;
                in vec2 in_texcoord;
                out vec2 v_texcoord;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_texcoord = in_texcoord;
                }
            ''',
            fragment_shader='''
                #version 330
                uniform sampler2D texture0;
                in vec2 v_texcoord;
                out vec4 fragColor;
                void main() {
                    fragColor = texture(texture0, v_texcoord);
                }
            '''
        )
    
    try:
        draw_text._shader['texture0'] = 0
    except:
        draw_text._shader = ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_vert;
                in vec2 in_texcoord;
                out vec2 v_texcoord;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_texcoord = in_texcoord;
                }
            ''',
            fragment_shader='''
                #version 330
                uniform sampler2D texture0;
                in vec2 v_texcoord;
                out vec4 fragColor;
                void main() {
                    fragColor = texture(texture0, v_texcoord);
                }
            '''
        )

    viewport_width, viewport_height = ctx.viewport[2:4]
    lines = text.split('\n')
    ctx.enable(moderngl.BLEND)
    text_surfaces = [font.render(line, True, color) for line in lines]
    vbo = ctx.buffer(reserve=6 * 4 * 4)
    vao = ctx.vertex_array(draw_text._shader, [(vbo, '2f 2f', 'in_vert', 'in_texcoord')])
    draw_text._shader['texture0'] = 0
    
    for i, text_surface in enumerate(text_surfaces):
        y_offset = i * font_size * line_spacing
        line_pos = (position[0], position[1] + y_offset)
        if text_surface.get_width() == 0 or text_surface.get_height() == 0:
            continue
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        text_texture = ctx.texture((text_surface.get_width(), text_surface.get_height()), 4, text_data)
        x1 = (line_pos[0] / viewport_width) * 2 - 1
        y1 = -((line_pos[1] / viewport_height) * 2 - 1) 
        x2 = ((line_pos[0] + text_surface.get_width()) / viewport_width) * 2 - 1
        y2 = -(((line_pos[1] + text_surface.get_height()) / viewport_height) * 2 - 1)
        vertices = np.array([
            x1, y1, 0.0, 1.0,
            x2, y1, 1.0, 1.0,
            x2, y2, 1.0, 0.0,
            x2, y2, 1.0, 0.0,
            x1, y2, 0.0, 0.0,
            x1, y1, 0.0, 1.0,
        ], dtype='f4')
        vbo.write(vertices.tobytes())
        text_texture.use(0)
        vao.render(moderngl.TRIANGLES)
        text_texture.release()
    vao.release()
    vbo.release()

def get_available_fonts():
    pygame.font.init()
    return pygame.font.get_fonts()

def preload_font(font_path, font_sizes=[12, 16, 20, 24, 32, 48]):
    for size in font_sizes:
        draw_text._font_cache = getattr(draw_text, '_font_cache', {})
        font_key = (font_path, size)
        if font_key not in draw_text._font_cache:
            try:
                if font_path is None:
                    font = pygame.font.Font(None, size)
                else:
                    try:
                        font = pygame.font.SysFont(font_path, size)
                    except:
                        font = pygame.font.Font(None, size)
                draw_text._font_cache[font_key] = font
            except Exception as e:
                draw_text._font_cache[font_key] = pygame.font.Font(None, size)

def get_hovered_vertex(ctx, vertices, mouse_pos, scale, transform_func):
    if len(vertices) == 0:
        return None
    viewport_width, viewport_height = ctx.viewport[2:4]
    transformed_vertices = transform_func(vertices)
    if len(transformed_vertices) == 0:
        return None
    projected_vertices = project(transformed_vertices, scale, viewport_width, viewport_height)
    screen_points = projected_vertices.reshape(-1, 2)
    norm_mouse_x = (mouse_pos[0] / viewport_width) * 2 - 1
    norm_mouse_y = -((mouse_pos[1] / viewport_height) * 2 - 1)
    distances = np.sqrt((screen_points[:, 0] - norm_mouse_x)**2 + 
                        (screen_points[:, 1] - norm_mouse_y)**2)
    threshold = 0.05
    closest_idx = np.argmin(distances)
    if distances[closest_idx] < threshold:
        return {
            'index': closest_idx,
            'position': vertices[closest_idx],
            'screen_pos': screen_points[closest_idx]
        }
    return None


def draw_line(ctx, start_pos, end_pos, color, line_prog, line_width=1.0):
    """
    Draw a line between two points using the OpenGL context.
    
    Args:
        ctx: ModernGL context
        start_pos: (x, y) tuple for the starting point in screen coordinates
        end_pos: (x, y) tuple for the ending point in screen coordinates
        color: (r, g, b) tuple with values 0-255
        line_prog: The shader program to use for rendering
        line_width: Width of the line (default 1.0)
    """
    x1, y1 = start_pos
    x2, y2 = end_pos
    
    # Get viewport dimensions
    viewport_width, viewport_height = ctx.viewport[2:4]
    
    # Convert screen coordinates to normalized device coordinates (-1 to 1)
    norm_x1 = (x1 / viewport_width) * 2 - 1
    norm_y1 = -((y1 / viewport_height) * 2 - 1)  # Flip Y coordinate
    norm_x2 = (x2 / viewport_width) * 2 - 1
    norm_y2 = -((y2 / viewport_height) * 2 - 1)  # Flip Y coordinate
    
    # Create vertex data for the line
    vertices = np.array([
        norm_x1, norm_y1,
        norm_x2, norm_y2
    ], dtype='f4')
    
    # Set the color uniform (convert from 0-255 to 0-1 range)
    line_prog['color'].value = (color[0]/255.0, color[1]/255.0, color[2]/255.0)
    
    # Create vertex buffer and vertex array
    vbo = ctx.buffer(vertices.tobytes())
    vao = ctx.vertex_array(line_prog, [(vbo, '2f', 'in_vert')])
    
    # Set line width if supported
    if line_width > 1.0:
        ctx.line_width = line_width
    
    # Render the line
    vao.render(moderngl.LINES)
    
    # Clean up
    vao.release()
    vbo.release()


def render_filled(ctx, vertex_data, faces, color, scale, line_prog):
    """
    Render a filled 3D shape using triangular faces.
    
    Args:
        ctx: ModernGL context
        vertex_data: Array of 3D vertices (N x 3)
        faces: Array of face indices defining triangles (M x 3)
        color: (r, g, b) tuple with values 0-255
        scale: Scale factor for projection
        line_prog: The shader program to use for rendering
    """
    if len(vertex_data) == 0 or len(faces) == 0:
        return
    
    viewport_width, viewport_height = ctx.viewport[2:4]
    
    # Project all vertices to screen coordinates
    projected_vertices = project(vertex_data, scale, viewport_width, viewport_height)
    screen_points = projected_vertices.reshape(-1, 2)
    
    # Create triangle vertex data from faces
    triangle_vertices = []
    for face in faces:
        # Each face should have 3 vertices for a triangle
        if len(face) >= 3:
            # Add the first triangle
            triangle_vertices.extend([
                screen_points[face[0]][0], screen_points[face[0]][1],
                screen_points[face[1]][0], screen_points[face[1]][1],
                screen_points[face[2]][0], screen_points[face[2]][1]
            ])
            
            # If it's a quad (4 vertices), add the second triangle
            if len(face) == 4:
                triangle_vertices.extend([
                    screen_points[face[0]][0], screen_points[face[0]][1],
                    screen_points[face[2]][0], screen_points[face[2]][1],
                    screen_points[face[3]][0], screen_points[face[3]][1]
                ])
    
    if not triangle_vertices:
        return
    
    # Convert to numpy array
    vertices = np.array(triangle_vertices, dtype='f4')
    
    # Set the color uniform
    line_prog['color'].value = (color[0]/255.0, color[1]/255.0, color[2]/255.0)
    
    # Create vertex buffer and vertex array
    vbo = ctx.buffer(vertices.tobytes())
    vao = ctx.vertex_array(line_prog, [(vbo, '2f', 'in_vert')])
    
    # Enable depth testing for proper 3D rendering
    ctx.enable(moderngl.DEPTH_TEST)
    
    # Render as filled triangles
    vao.render(moderngl.TRIANGLES)
    
    # Clean up
    vao.release()
    vbo.release()