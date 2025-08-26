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

			'''
			根据OpenEB的代码库（https://github.com/prophesee-ai/openeb）和Copilot的分析：
			
			在Prophesee的RAW格式中，OTHERS 类型事件和后面紧跟的三个 CONTINUED_12 类型 word 会被拼接成一个完整的28位值。其具体用途如下：
			1. 事件计数（Event Rate Control, ERC）
			28位值经常用来表示某个时间窗口内的事件数量，比如 “MASTER_IN_CD_EVENT_COUNT” 或 “MASTER_RATE_CONTROL_CD_EVENT_COUNT”。
			这类事件通常由传感器硬件或固件统计并编码在 RAW 数据流中，便于下游软件做带宽控制、速率分析、健康监控等。
			2. 监控/扩展事件的有效负载
			某些特殊的 OTHERS 类型事件（master_type）会用 28 位值承载自定义有效载荷，比如外部触发、状态标志或其它协议扩展。
			这些值可以被解码器或应用层用来做高级统计、性能分析或调试。
			3. 解码流程举例
			解码器检测到 OTHERS 类型 word，读取 master_type。
			如果属于计数类事件，则后续三个 CONTINUED_12 word合并成28位数值，作为计数器记录。
			这些计数随后用于事件速率调控（ERC）、流量分析或其它监控目的。
			
			看起来我们并不太需要这些信息。所以我们就不处理这些event了。
			'''
			
		elif event_type == self.OTHERS:
			# 其他事件类型 - 这里不处理
			pass
			
		elif event_type == self.CONTINUED_4 or event_type == self.CONTINUED_12:
			# 继续事件 - 这里不处理
			pass
		
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

	header_text = ""
	
	with open(filename, 'rb') as f:
		while True:
			line = f.readline()
			if not line:
				break
				
			# 将字节转换为字符串
			try:
				line_str = line.decode('ascii').strip()
				header_text += line_str + "\n"
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
	
	header["header_text"] = header_text.strip()

	return header, data_start


def parse_format_from_header(header: Dict) -> Tuple[str, int, int]:
	"""
	解析format字符串
	
	Args:
		一种header:
			format: "EVT3;height=720;width=1280"
		另一种header:
			format: EVT3
			geometry: 1280x720
	Returns:
		(encoding_format, height, width)
	"""
	if 'format' in header:
		format_str = header['format']
		parts = format_str.split(';')
		encoding_format = parts[0]
		if len(parts) > 1:
			height = width = 0
			for part in parts[1:]:
				if '=' in part:
					key, value = part.split('=')
					if key == 'height':
						height = int(value)
					elif key == 'width':
						width = int(value)
						
	if 'geometry' in header:
		format_str = header['geometry']
		parts = format_str.split('x')
		width = int(parts[0].strip())
		height = int(parts[1].strip())	
	
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
	
	encoding_format, height, width = parse_format_from_header(header)
	
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
