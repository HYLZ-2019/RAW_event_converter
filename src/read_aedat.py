import struct
import numpy as np
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass

@dataclass
class Event:
	"""事件数据结构"""
	x: int
	y: int
	t: int  # 时间戳（微秒）
	p: int  # 极性 (0 or 1)

def read_aedat3_events(filename: str, max_events: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray, Dict[str, str]]:
	"""
	读取AEDAT3格式的事件数据
	
	Args:
		filename: AEDAT3文件路径
		max_events: 最大读取事件数量（None表示读取全部）
		
	Returns:
		(events_array, trigger_events_array, header_info)
		events_array: Nx4的numpy数组，列为[x, y, t, p]
		trigger_events_array: Nx3的numpy数组，列为[t, id, value] (目前为空数组，AEDAT3格式没有触发事件)
		header_info: 头部信息字典
	"""
	events = []
	header = {
		"format": "AEDAT3",
		"header_text": f"AEDAT3 format file: {filename}\n% Data format: Polarity Events\n% end"
	}
	
	with open(filename, 'rb') as f:
		# 首先跳过ASCII头部
		text_header = ""
		while True:
			line = f.readline()
			if not line:
				break
			try:
				line_str = line.decode('ascii').strip()
				text_header += line_str + "\n"
				# 检查是否到达二进制数据开始标记
				if line_str.startswith('#Start-Data'):
					break
			except UnicodeDecodeError:
				# 遇到非ASCII字符，可能是二进制数据开始了
				f.seek(f.tell() - len(line))  # 回退
				break
		
		header["header_text"] = text_header
		
		if "#Source 1: DVS128" in text_header:
			header["width"] = 128
			header["height"] = 128

		print(f"ASCII头部读取完成，二进制数据开始位置: {f.tell()}")
		
		event_count = 0
		
		while True:
			# 读取头部结构 (28 bytes: 2*uint16_t + 6*uint32_t)
			header_data = f.read(28)
			if len(header_data) < 28:
				break
				
			# 解析头部
			(event_type, event_source, event_size, event_ts_offset, 
			 event_ts_overflow, event_capacity, event_number, event_valid) = struct.unpack('<HHLLLLLL', header_data)
			
			print(f"事件块: type={event_type}, source={event_source}, size={event_size}, number={event_number}")
			
			# 读取事件数据
			events_data_size = event_number * 8  # 每个事件8字节 (4字节data + 4字节timestamp)
			if events_data_size > 0:
				events_data = f.read(events_data_size)
				if len(events_data) < events_data_size:
					break
				
				# 解析每个事件
				for i in range(event_number):
					offset = i * 8
					data, timestamp = struct.unpack('<LL', events_data[offset:offset+8])
					
					# 从data字段提取x, y, polarity
					x = (data >> 17) & 0x00001FFF
					y = (data >> 2) & 0x00001FFF
					polarity = (data >> 1) & 0x00000001
					
					# 创建事件
					event = Event(
						x=x,
						y=y,
						t=timestamp,  # AEDAT3中timestamp直接使用，单位为微秒
						p=polarity
					)
					events.append(event)
					event_count += 1
					
					# 检查是否达到最大事件数
					if max_events is not None and event_count >= max_events:
						break
				
				if max_events is not None and event_count >= max_events:
					break
			
			# 显示进度
			if event_count % 100000 == 0 and event_count > 0:
				print(f"已解码 {event_count} 个事件")
	
	print(f"总共解码 {len(events)} 个事件")
	
	# 转换为numpy数组
	if events:
		events_array = np.array([(e.x, e.y, e.t, e.p) for e in events], 
							   dtype=[('x', np.uint16), ('y', np.uint16), 
									 ('t', np.uint64), ('p', np.uint8)])
	else:
		events_array = np.array([], dtype=[('x', np.uint16), ('y', np.uint16), 
										  ('t', np.uint64), ('p', np.uint8)])
	
	# AEDAT3格式目前不包含触发事件，返回空数组
	trigger_events_array = np.array([], dtype=[('t', np.uint64), ('id', np.uint8), 
											   ('value', np.uint8)])
	
	return events_array, trigger_events_array, header
