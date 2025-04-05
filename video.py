import imageio.v2 as imageio

frame_files = []
for i in range(360*2):
    frame_files.append(f"frames/frame_{i:03d}.png")

images = [imageio.imread(fname) for fname in frame_files]
imageio.mimsave('output_video.mp4', images, fps=30)