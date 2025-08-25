import numpy as np

def map_color(val, clip=10):
	BLUE = np.expand_dims(np.expand_dims(np.array([255, 0, 0]), 0), 0)
	RED = np.expand_dims(np.expand_dims(np.array([0, 0, 255]), 0), 0)
	WHITE = np.expand_dims(np.expand_dims(np.array([255, 255, 255]), 0), 0)
	val = np.clip(val, -clip, clip)
	val = np.expand_dims(val, -1)
	red_side = (1 - val / clip) * WHITE + (val / clip) * RED
	blue_side = (1 + val / clip) * WHITE + (-val / clip) * BLUE
	return np.where(val > 0, red_side, blue_side).astype(np.uint8)

def make_voxel(evs, H, W, num_bins=5):
	voxel = np.zeros((num_bins, H, W))
	ts, xs, ys, ps = evs
	if ts.shape[0] == 0:
		return voxel
	
	# ps of hqf h5 file are in {0, 1}.
	ps = ps.astype(np.int8) * 2 - 1
	ts = ((ts - ts[0]) * 1e6).astype(np.int64)

	t_per_bin = (ts[-1] + 0.001) / num_bins
	bin_idx = np.floor(ts / t_per_bin).astype(np.uint8)
	np.add.at(voxel, (bin_idx, ys, xs), ps)
			
	return voxel

def events_to_video(events, output_file, width=1280, height=720, fps=30, clip=10):
	import ffmpeg
	"""
	将事件数据转换为视频文件
	
	Args:
		events: 事件数据数组，包含字段 't', 'x', 'y', 'p'
		output_file: 输出视频文件路径
		width: 传感器宽度
		height: 传感器高度
		fps: 视频帧率
		num_bins: 每帧包含的时间窗口数量
		clip: 用于颜色映射的裁剪值
	"""
	print(f"正在生成视频: {output_file}")
	
	if len(events) == 0:
		print("没有事件数据，无法生成视频。")
		return
	
	start_time = events['t'][0]
	end_time = events['t'][-1]
	duration_s = (end_time - start_time) * 1e-6
	total_frames = int(np.ceil(duration_s * fps))
	frame_duration_us = 1e6 / fps
	
	process = (
		ffmpeg
		.input('pipe:', format='rawvideo', pix_fmt='rgb24', s=f'{width}x{height}', framerate=fps)
		.output(output_file, pix_fmt='yuv420p', vcodec='libx264', r=fps)
		.overwrite_output()
		.run_async(pipe_stdin=True)
	)
	
	for frame_idx in range(total_frames):
		frame_start_us = start_time + frame_idx * frame_duration_us
		frame_end_us = frame_start_us + frame_duration_us
		
		mask = (events['t'] >= frame_start_us) & (events['t'] < frame_end_us)
		frame_events = events[mask]
		
		voxel = make_voxel((frame_events['t'], frame_events['x'], frame_events['y'], frame_events['p']), height, width, 1)
		
		frame = np.sum(voxel, axis=0)
		
		color_frame = map_color(frame, clip)
		
		process.stdin.write(color_frame.tobytes())
	
	process.stdin.close()
	process.wait()
	
	print(f"视频生成完成: {output_file}")