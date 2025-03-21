import bpy
import pickle
import numpy as np
import os

print("beginning script to visualize neural networks...")

# Clear the scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Path to the pickled file
pickle_file_path = "/Users/jacksonwalters/Documents/GitHub/blender/neural_network_viz/hidden_space_and_points.pkl"

# Load the pickled data
print("loading pickle file...")
with open(pickle_file_path, "rb") as f:
    data = pickle.load(f)
print("pickle file loaded.")

# Create materials
def create_material(name, base_color, opacity):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Add Principled BSDF
    output = nodes.new(type='ShaderNodeOutputMaterial')
    shader = nodes.new(type='ShaderNodeBsdfPrincipled')
    shader.location = (0, 0)
    output.location = (200, 0)
    links.new(shader.outputs['BSDF'], output.inputs['Surface'])

    # Configure opacity and blend mode
    shader.inputs['Alpha'].default_value = opacity
    mat.blend_method = 'BLEND' if opacity < 1.0 else 'OPAQUE'

    # Set base color
    shader.inputs['Base Color'].default_value = (*base_color, 1.0)

    return mat


# Extract the original points and hidden space trajectory
original_points = np.array(data["original_points"])  # Shape (n, 2)
labels = np.array(data["labels"])
hidden_space_trajectory = np.array(data["hidden_space_trajectory"])  

# Print information to verify
print(f"Loaded {original_points.shape[0]} original points with shape {original_points.shape}")
print(f"Loaded hidden space trajectory with shape {hidden_space_trajectory.shape}")


# Create materials for pass and fail
pass_material = create_material("Pass_Material", (0.0, 1.0, 0.0), 1.0)  # Green for pass
fail_material = create_material("Fail_Material", (1.0, 0.0, 0.0), 1.0)  # Red for fail

# Add points to the Blender scene and assign materials
objects = []  # Store references to the created objects
for i, point in enumerate(original_points):
    # Create a sphere for each point
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(point[0], point[1], 0))
    obj = bpy.context.object  # Reference to the newly created object

    # Assign material based on pass_fail
    if labels[i] == 1:
        obj.data.materials.append(pass_material)
    else:
        obj.data.materials.append(fail_material)

    # Set the original point as the first keyframe
    obj.location = (point[0], point[1], 0)
    obj.keyframe_insert(data_path="location", frame=1)

    objects.append(obj)

# Add keyframes for each epoch
start_frame = 10  # Start animating at frame 10
frame_step = 5  # Frames between each epoch
layer_gap = 20 

layer_2_start = layer_gap + start_frame + (len(hidden_space_trajectory) - 1) * frame_step

for epoch_index, hidden_layers in enumerate(hidden_space_trajectory):
    current_frame = start_frame + epoch_index * frame_step

    hidden_positions = hidden_layers["hidden_layer_1"]
    for i, obj in enumerate(objects):
        # Update object location based on hidden space position
        hidden_position = hidden_positions[i] * 5
        obj.location = (hidden_position[0], hidden_position[1], hidden_position[2] if hidden_position.shape[0] > 2 else 0)
        obj.keyframe_insert(data_path="location", frame=current_frame)


for epoch_index, hidden_layers in enumerate(hidden_space_trajectory):
    current_frame = layer_2_start + epoch_index * frame_step

    hidden_positions = hidden_layers["hidden_layer_2"]
    for i, obj in enumerate(objects):
        # Update object location based on hidden space position
        hidden_position = hidden_positions[i] * 5
        obj.location = (hidden_position[0], hidden_position[1], hidden_position[2] if hidden_position.shape[0] > 2 else 0)
        obj.keyframe_insert(data_path="location", frame=current_frame)

for obj in objects:
    if obj.animation_data and obj.animation_data.action:  # Ensure object has animation data
        for fcurve in obj.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = 'LINEAR'

print(f"Animation keyframes added for {len(hidden_space_trajectory)} epochs.")


# Add a camera (if not already present)
if "Camera" not in bpy.data.objects:
    bpy.ops.object.camera_add(location=(0, 0, 25))  # Position the camera
camera = bpy.context.object

# Set camera as the active camera
bpy.context.scene.camera = camera

# Add a light source
bpy.ops.object.light_add(type='POINT', location=(0, 0, 10))
light = bpy.context.object
light.data.energy = 1000  # Set the intensity of the light

# Rendering setup (add this part)
bpy.context.scene.render.resolution_x = 1920  # Set the resolution width
bpy.context.scene.render.resolution_y = 1080  # Set the resolution height
bpy.context.scene.render.fps = 24  # Set the frames per second

# Set the frame range (e.g., from frame 1 to the last frame)
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = layer_2_start + (len(hidden_space_trajectory) - 1) * frame_step
#bpy.context.scene.frame_end = 10
print("bpy.context.scene.frame_end = ", bpy.context.scene.frame_end)

# Set the output directory and file format (e.g., FFmpeg for video)
output_directory = "/Users/jacksonwalters/Documents/GitHub/blender/neural_network_viz/render_output/"
bpy.context.scene.render.filepath = os.path.join(output_directory, "animation_output.mp4")
bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
bpy.context.scene.render.ffmpeg.format = 'MPEG4'
bpy.context.scene.render.ffmpeg.codec = 'H264'

# Trigger the rendering process
print("Rendering animation...")
bpy.ops.render.render(animation=True, write_still=False)
print("Rendering completed!")
