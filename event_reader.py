#!/usr/bin/env python3

import struct
import numpy as np
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
import argparse
from src.visualize_events import events_to_video
from src.read_raw import read_evt3_events
from src.read_aedat import read_aedat3_events
from src.write_formats import save_events_to_csv, save_trigger_events_to_csv, save_events_to_npz, save_events_to_h5

def print_event_statistics(events: np.ndarray, trigger_events: np.ndarray, header: Dict[str, str]):
	"""打印事件统计信息"""
	print("\n=== 事件统计信息 ===")
	print(f"总事件数: {len(events)}")
	print(f"总触发事件数: {len(trigger_events)}")
	
	if len(events) > 0:
		print(f"时间范围: {events['t'].min() * 1e-6} - {events['t'].max() * 1e-6} 秒")
		print(f"持续时间: {(events['t'].max() - events['t'].min()) / 1000000:.2f} 秒")
		print(f"X坐标范围: {events['x'].min()} - {events['x'].max()}")
		print(f"Y坐标范围: {events['y'].min()} - {events['y'].max()}")
		print(f"正极性事件: {np.sum(events['p'] == 1)}")
		print(f"负极性事件: {np.sum(events['p'] == 0)}")
		
		# 计算事件率
		if len(events) > 1:
			duration_sec = (events['t'].max() - events['t'].min()) / 1000000
			if duration_sec > 0:
				event_rate = len(events) / duration_sec
				print(f"平均事件率: {event_rate:.0f} 事件/秒")
	
	if len(trigger_events) > 0:
		print(f"\n=== 触发事件统计 ===")
		print(f"触发时间范围: {trigger_events['t'].min()} - {trigger_events['t'].max()} 微秒")
		
		# 统计不同触发通道
		unique_ids = np.unique(trigger_events['id'])
		for trigger_id in unique_ids:
			mask = trigger_events['id'] == trigger_id
			count = np.sum(mask)
			rising_edges = np.sum((trigger_events['id'] == trigger_id) & (trigger_events['value'] == 1))
			falling_edges = np.sum((trigger_events['id'] == trigger_id) & (trigger_events['value'] == 0))
			
			if trigger_id == 0:
				channel_name = "EXTTRIG"
			elif trigger_id == 1:
				channel_name = "TDRSTN/PXRSTN"
			else:
				channel_name = f"未知通道{trigger_id}"
				
			print(f"通道 {trigger_id} ({channel_name}): {count} 个事件 (上升沿: {rising_edges}, 下降沿: {falling_edges})")
	
	print("\n=== 头部信息 ===")
	print(header["header_text"])

def main():
	"""主函数"""
	parser = argparse.ArgumentParser(description='Event Data Reader for RAW and AEDAT3 formats')
	parser.add_argument('input_file', help='输入文件路径 (支持 .raw 和 .aedat 格式)')
	parser.add_argument('--max-events', type=int, help='最大读取事件数量')
	parser.add_argument('--output-csv', help='输出CSV文件路径')
	parser.add_argument('--output-trigger-csv', help='输出触发事件CSV文件路径')
	parser.add_argument('--output-npz', help='输出NPZ文件路径')
	parser.add_argument('--output-video', help='输出视频文件路径 (MP4格式)')
	parser.add_argument('--output-h5', help='输出H5文件路径')
	parser.add_argument('--stats-only', action='store_true', help='只显示统计信息，不保存数据')
	
	args = parser.parse_args()
	
	try:
		# 根据文件扩展名选择读取函数
		file_ext = args.input_file.lower().split('.')[-1]
		print(f"正在读取文件: {args.input_file}")
		print(f"检测到文件格式: {file_ext.upper()}")
		
		if file_ext == 'raw':
			events, trigger_events, header = read_evt3_events(args.input_file, args.max_events)
		elif file_ext == 'aedat':
			events, trigger_events, header = read_aedat3_events(args.input_file, args.max_events)
		else:
			raise ValueError(f"不支持的文件格式: .{file_ext}。支持的格式: .raw, .aedat")
		
		# 打印统计信息
		print_event_statistics(events, trigger_events, header)
		
		# 保存数据
		if not args.stats_only:
			if args.output_csv:
				save_events_to_csv(events, args.output_csv)
			
			if args.output_trigger_csv:
				save_trigger_events_to_csv(trigger_events, args.output_trigger_csv)
			
			if args.output_npz:
				save_events_to_npz(events, trigger_events, header, args.output_npz)
			
			if args.output_h5:
				save_events_to_h5(events, trigger_events, header, args.output_h5)

			if args.output_video:
				video_file = args.output_video
				# 默认分辨率和帧率
				width = int(header.get('width', 1280))
				height = int(header.get('height', 720))
				events_to_video(events, video_file, width, height, fps=10)
				print(f"视频已保存到: {video_file}")
			
			# 默认保存为NPZ格式
			if not args.output_csv and not args.output_npz:
				if file_ext == 'raw':
					default_output = args.input_file.replace('.raw', '_events.npz')
				elif file_ext == 'aedat':
					default_output = args.input_file.replace('.aedat', '_events.npz')
				else:
					default_output = args.input_file + '_events.npz'
				save_events_to_npz(events, trigger_events, header, default_output)
		
	except Exception as e:
		print(f"错误: {e}")
		return 1
	
	return 0


if __name__ == "__main__":
	exit(main())
