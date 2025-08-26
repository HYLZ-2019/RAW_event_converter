import numpy as np
from typing import Dict

def save_events_to_csv(events: np.ndarray, filename: str):
	"""将事件保存为CSV格式"""
	import csv
	
	with open(filename, 'w', newline='') as f:
		writer = csv.writer(f)
		writer.writerow(['t', 'x', 'y', 'p'])  # 头部
		
		for event in events:
			writer.writerow([event['t'], event['x'], event['y'], event['p']])
	
	print(f"事件已保存到: {filename}")


def save_trigger_events_to_csv(trigger_events: np.ndarray, filename: str):
	"""将触发事件保存为CSV格式"""
	import csv
	
	with open(filename, 'w', newline='') as f:
		writer = csv.writer(f)
		writer.writerow(['t', 'id', 'value'])  # 头部
		
		for trigger in trigger_events:
			writer.writerow([trigger['t'], trigger['id'], trigger['value']])
	
	print(f"触发事件已保存到: {filename}")


def save_events_to_npz(events: np.ndarray, trigger_events: np.ndarray, header: Dict[str, str], filename: str):
	"""将事件和触发事件保存为NPZ格式"""
	np.savez(filename, events=events, trigger_events=trigger_events, header=header)
	print(f"事件已保存到: {filename}")

def save_events_to_h5(events: np.ndarray, trigger_events: np.ndarray, header: Dict[str, str], filename: str):
	'''
	h5 格式要求：
	f.attrs["sensor_resolution"] = (H, W)
	f.attrs["num_events"] = num_events # int
	f.attrs["num_imgs"] = num_imgs # int, 没有图像的话，就为0
	f.attrs["duration"] = duration # float, 单位为秒
	f.attrs["camera_type"] = camera_type # 相机型号, string
	f.attrs["base_time"] = base_time # float, 是绝对时间epoch time（也就是从1970年1月1日开始的秒数）。如果原数据集的timestamp给的是epoch time，那么让base_time = ts[0]，然后ts -= base_time，使得ts[0] == 0. 如果原来给的就是相对时间，那么直接设置 base_time = 0.0.

	events:
	* events/xs: np.uint16
	* events/ys: np.uint16
	* events/ts: np.uint64, ts[0] == 0. 
	* events/ps: np.uint8, 值是0或1.
	
	trigger_events:
	* trigger_events/ts: np.uint64。减去了base_time。
	* trigger_events/ids: np.uint8 # 4 bits。
	* trigger_events/values: np.uint8。 # 0 or 1。
	'''
	import h5py
	
	with h5py.File(filename, 'w') as f:
		# 保存头部信息
		if 'height' in header and 'width' in header:
			f.attrs['sensor_resolution'] = (int(header['height']), int(header['width']))
		else:
			f.attrs['sensor_resolution'] = (0, 0)
		f.attrs["header_text"] = header.get("header_text", "")
		
		f.attrs['num_events'] = len(events)
		f.attrs['num_trigger_events'] = len(trigger_events)
		
		if len(events) > 0:
			duration = (events['t'].max() - events['t'].min()) * 1e-6
		else:
			duration = 0.0
		f.attrs['duration'] = duration
		
		f.attrs['camera_type'] = header.get('camera', 'Unknown')
		
		if len(events) > 0:
			base_time = events['t'].min() * 1e-6
		else:
			base_time = 0.0
		f.attrs['base_time'] = base_time
		
		# Compression rate
		cpr = 1

		if len(events) > 0:
			events_group = f.create_group('events')
			events_group.create_dataset('xs', data=events['x'].astype(np.uint16), compression="gzip", compression_opts=cpr)
			events_group.create_dataset('ys', data=events['y'].astype(np.uint16), compression="gzip", compression_opts=cpr)
			ts_relative = events['t'] - events['t'].min()
			events_group.create_dataset('ts', data=ts_relative.astype(np.uint64), compression="gzip", compression_opts=cpr)
			events_group.create_dataset('ps', data=events['p'].astype(np.uint8), compression="gzip", compression_opts=cpr)
		
		if len(trigger_events) > 0:
			trigger_group = f.create_group('trigger_events')
			ts_trigger_relative = trigger_events['t'] - (events['t'].min() if len(events) > 0 else 0)
			trigger_group.create_dataset('ts', data=ts_trigger_relative.astype(np.uint64), compression="gzip", compression_opts=cpr)
			trigger_group.create_dataset('ids', data=trigger_events['id'].astype(np.uint8), compression="gzip", compression_opts=cpr)
			trigger_group.create_dataset('values', data=trigger_events['value'].astype(np.uint8), compression="gzip", compression_opts=cpr)

	print(f"事件已保存到: {filename}")