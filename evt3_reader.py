#!/usr/bin/env python3
"""
EVT3 Event Data Reader
纯Python实现的EVT3格式事件数据读取器（不依赖metavision库）

基于Prophesee EVT3.0格式文档实现
支持读取.raw文件中的事件数据并转换为结构化格式
"""

import struct
import numpy as np
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
import argparse
from visualize_events import events_to_video


@dataclass
class Event:
	"""事件数据结构"""
	x: int
	y: int
	t: int  # 时间戳（微秒）
	p: int  # 极性 (0 or 1)


@dataclass
class TriggerEvent:
	"""外部触发事件数据结构"""
	t: int      # 时间戳（微秒）
	id: int     # 触发通道ID (0: EXTTRIG, 1: TDRSTN/PXRSTN)
	value: int  # 触发值 (0: 下降沿, 1: 上升沿)


class EVT3Decoder:
	"""EVT3格式解码器"""
	
	# Event types (4 MSB)
	EVT_ADDR_Y = 0x0      # '0000'
	EVT_ADDR_X = 0x2      # '0010'
	VECT_BASE_X = 0x3     # '0011'
	VECT_12 = 0x4         # '0100'
	VECT_8 = 0x5          # '0101'
	EVT_TIME_LOW = 0x6    # '0110'
	CONTINUED_4 = 0x7     # '0111'
	EVT_TIME_HIGH = 0x8   # '1000'
	EXT_TRIGGER = 0xA     # '1010'
	OTHERS = 0xE          # '1110'
	CONTINUED_12 = 0xF    # '1111'
	
	def __init__(self, width: int = 1280, height: int = 720):
		"""
		初始化解码器
		
		Args:
			width: 传感器宽度
			height: 传感器高度
		"""
		self.width = width
		self.height = height
		self.reset_state()

		self.event_type_cnt = {}
	
	def reset_state(self):
		"""重置解码器状态"""
		self.time_high = 0
		self.time_low = 0
		self.current_y = 0
		self.current_polarity = 0
		self.vect_base_x = 0
		self.vect_base_polarity = 0
		
	def get_timestamp(self) -> int:
		"""获取当前完整时间戳（微秒）"""
		return (self.time_high << 12) | self.time_low
	
	def decode_word(self, word: int) -> Tuple[List[Event], List[TriggerEvent]]:
		"""
		解码单个16位EVT3字
		
		Args:
			word: 16位EVT3数据字
			
		Returns:
			(events_list, trigger_events_list): 解码得到的事件列表和触发事件列表
		"""
		events = []
		trigger_events = []
		
		# 提取事件类型（4个MSB）
		event_type = (word >> 12) & 0xF

		self.event_type_cnt[event_type] = self.event_type_cnt.get(event_type, 0) + 1
		
		if event_type == self.EVT_ADDR_Y:
			# Y坐标事件
			self.current_y = word & 0x7FF  # 11 bits
			# bit 11 是系统类型（master/slave），这里忽略
			
		elif event_type == self.EVT_ADDR_X:
			# X坐标事件 - 这是一个有效的单个事件
			x = word & 0x7FF  # 11 bits
			polarity = (word >> 11) & 0x1  # 1 bit
			
			event = Event(
				x=x,
				y=self.current_y,
				t=self.get_timestamp(),
				p=polarity
			)
			events.append(event)
			
		elif event_type == self.VECT_BASE_X:
			# 向量基础X坐标 - 设置向量事件的基础位置
			self.vect_base_x = word & 0x7FF  # 11 bits
			self.vect_base_polarity = (word >> 11) & 0x1  # 1 bit
			
		elif event_type == self.VECT_12:
			# 12位向量事件
			valid_bits = word & 0xFFF  # 12 bits
			
			for i in range(12):
				if (valid_bits >> i) & 0x1:
					event = Event(
						x=self.vect_base_x + i,
						y=self.current_y,
						t=self.get_timestamp(),
						p=self.vect_base_polarity
					)
					events.append(event)
			
			# 更新基础X坐标
			self.vect_base_x += 12
			
		elif event_type == self.VECT_8:
			# 8位向量事件
			valid_bits = word & 0xFF  # 8 bits (bits 7..0)
			
			for i in range(8):
				if (valid_bits >> i) & 0x1:
					event = Event(
						x=self.vect_base_x + i,
						y=self.current_y,
						t=self.get_timestamp(),
						p=self.vect_base_polarity
					)
					events.append(event)
			
			# 更新基础X坐标
			self.vect_base_x += 8
			
		elif event_type == self.EVT_TIME_LOW:
			# 时间戳低12位
			self.time_low = word & 0xFFF  # 12 bits
			
		elif event_type == self.EVT_TIME_HIGH:
			# 时间戳高12位
			self.time_high = word & 0xFFF  # 12 bits
			
		elif event_type == self.EXT_TRIGGER:
			# 外部触发事件
			trigger_id = (word >> 8) & 0xF    # 4 bits (11..8)
			trigger_value = word & 0x1        # 1 bit (0)
			
			trigger_event = TriggerEvent(
				t=self.get_timestamp(),
				id=trigger_id,
				value=trigger_value
			)
			trigger_events.append(trigger_event)
			
		elif event_type == self.OTHERS:
			# 其他事件类型 - 这里不处理
			pass
			#print("OTHERS event type encountered, ignoring.")
			#raise NotImplementedError("OTHERS event type not implemented")
			
		elif event_type == self.CONTINUED_4 or event_type == self.CONTINUED_12:
			# 继续事件 - 这里不处理
			pass
			#print("CONTINUED event type encountered, ignoring.")
			#raise NotImplementedError("CONTINUED event types not implemented")
		
		return events, trigger_events


def read_raw_header(filename: str) -> Tuple[Dict[str, str], int]:
	"""
	读取RAW文件的头部信息
	
	Args:
		filename: RAW文件路径
		
	Returns:
		(header_dict, data_start_position)
	"""
	header = {}
	
	with open(filename, 'rb') as f:
		while True:
			line = f.readline()
			if not line:
				break
				
			# 将字节转换为字符串
			try:
				line_str = line.decode('ascii').strip()
			except UnicodeDecodeError:
				# 如果不是ASCII，说明已到达二进制数据部分
				break
				
			# 检查是否是头部行
			if line_str.startswith('% '):
				# 解析键值对
				parts = line_str[2:].split(' ', 1)  # 去掉'% '并分割
				if len(parts) == 2:
					key, value = parts
					header[key] = value
				elif len(parts) == 1 and parts[0] == 'end':
					# 遇到end标记，头部结束
					break
			elif not line_str.startswith('%'):
				# 不以%开头，说明头部结束
				break
				
		# 记录数据开始位置
		data_start = f.tell() - len(line)
		
	return header, data_start


def parse_format_string(format_str: str) -> Tuple[str, int, int]:
	"""
	解析format字符串
	
	Args:
		format_str: 如 "EVT3;height=720;width=1280"
		
	Returns:
		(encoding_format, height, width)
	"""
	parts = format_str.split(';')
	encoding_format = parts[0]
	
	height = width = 0
	for part in parts[1:]:
		if '=' in part:
			key, value = part.split('=')
			if key == 'height':
				height = int(value)
			elif key == 'width':
				width = int(value)
	
	return encoding_format, height, width


def read_evt3_events(filename: str, max_events: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray, Dict[str, str]]:
	"""
	读取EVT3格式的事件数据
	
	Args:
		filename: RAW文件路径
		max_events: 最大读取事件数量（None表示读取全部）
		
	Returns:
		(events_array, trigger_events_array, header_info)
		events_array: Nx4的numpy数组，列为[x, y, t, p]
		trigger_events_array: Nx3的numpy数组，列为[t, id, value]
		header_info: 头部信息字典
	"""
	# 读取头部信息
	header, data_start = read_raw_header(filename)
	
	# 解析格式信息
	if 'format' not in header:
		raise ValueError("Header中缺少format信息")
	
	encoding_format, height, width = parse_format_string(header['format'])
	
	if not encoding_format.startswith('EVT3'):
		raise ValueError(f"不支持的编码格式: {encoding_format}")
	
	print(f"文件格式: {encoding_format}")
	print(f"分辨率: {width}x{height}")
	print(f"数据开始位置: {data_start}")
	
	# 创建解码器
	decoder = EVT3Decoder(width, height)
	
	# 读取并解码事件数据
	events = []
	trigger_events = []
	
	with open(filename, 'rb') as f:
		f.seek(data_start)
		
		event_count = 0
		trigger_count = 0
		while True:
			# 读取2字节的EVT3数据字
			data = f.read(2)
			if len(data) < 2:
				break
			
			# 解析为16位整数（小端序）
			word = struct.unpack('<H', data)[0]
			
			# 解码该字
			decoded_events, decoded_triggers = decoder.decode_word(word)
			
			# 添加解码得到的事件
			events.extend(decoded_events)
			trigger_events.extend(decoded_triggers)
			event_count += len(decoded_events)
			trigger_count += len(decoded_triggers)
			
			# 检查是否达到最大事件数
			if max_events is not None and event_count >= max_events:
				events = events[:max_events]
				break
			
			# 每100万字节显示进度
			if f.tell() % 1000000 == 0:
				print(f"已处理 {f.tell() // 1000000}MB, 解码 {len(events)} 个事件, {len(trigger_events)} 个触发事件")
	
	print(f"总共解码 {len(events)} 个事件, {len(trigger_events)} 个触发事件")
	print(f"事件类型计数: {decoder.event_type_cnt}")
	
	# 转换为numpy数组
	if events:
		events_array = np.array([(e.x, e.y, e.t, e.p) for e in events], 
							   dtype=[('x', np.uint16), ('y', np.uint16), 
									 ('t', np.uint64), ('p', np.uint8)])
	else:
		events_array = np.array([], dtype=[('x', np.uint16), ('y', np.uint16), 
										  ('t', np.uint64), ('p', np.uint8)])
	
	if trigger_events:
		trigger_events_array = np.array([(te.t, te.id, te.value) for te in trigger_events],
									   dtype=[('t', np.uint64), ('id', np.uint8), 
											 ('value', np.uint8)])
	else:
		trigger_events_array = np.array([], dtype=[('t', np.uint64), ('id', np.uint8), 
												  ('value', np.uint8)])
	
	return events_array, trigger_events_array, header


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


def print_event_statistics(events: np.ndarray, trigger_events: np.ndarray, header: Dict[str, str]):
	"""打印事件统计信息"""
	print("\n=== 事件统计信息 ===")
	print(f"总事件数: {len(events)}")
	print(f"总触发事件数: {len(trigger_events)}")
	
	if len(events) > 0:
		print(f"时间范围: {events['t'].min()} - {events['t'].max()} 微秒")
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
	for key, value in header.items():
		print(f"{key}: {value}")


def main():
	"""主函数"""
	parser = argparse.ArgumentParser(description='EVT3 Event Data Reader')
	parser.add_argument('input_file', help='输入的RAW文件路径')
	parser.add_argument('--max-events', type=int, help='最大读取事件数量')
	parser.add_argument('--output-csv', help='输出CSV文件路径')
	parser.add_argument('--output-npz', help='输出NPZ文件路径')
	parser.add_argument('--output-video', help='输出视频文件路径 (MP4格式)')
	parser.add_argument('--output-trigger-csv', help='输出触发事件CSV文件路径')
	parser.add_argument('--stats-only', action='store_true', help='只显示统计信息，不保存数据')
	
	args = parser.parse_args()
	
	try:
		# 读取事件数据
		print(f"正在读取文件: {args.input_file}")
		events, trigger_events, header = read_evt3_events(args.input_file, args.max_events)
		
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

			if args.output_video:
				video_file = args.output_video
				# 默认分辨率和帧率
				width = int(header.get('width', 1280))
				height = int(header.get('height', 720))
				events_to_video(events, video_file, width, height, fps=10)
				print(f"视频已保存到: {video_file}")
			
			# 默认保存为NPZ格式
			if not args.output_csv and not args.output_npz:
				default_output = args.input_file.replace('.raw', '_events.npz')
				save_events_to_npz(events, trigger_events, header, default_output)
		
	except Exception as e:
		print(f"错误: {e}")
		return 1
	
	return 0


if __name__ == "__main__":
	exit(main())
