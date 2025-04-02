import heapq
import json
from dataclasses import dataclass, field
from typing import List, Dict

# 常量定义
LOCAL_BANDWIDTH = 200  # 假设本地带宽足够大

@dataclass(order=True)
class Event:
    """事件类，包含跨数据中心和本地事件的处理逻辑"""
    time: float  # 事件触发时间
    stream_id: int = field(compare=False)
    event_type: str = field(compare=False)  # compute/comm_start/comm_end
    data_size: float = field(compare=False)  # 通信数据量
    duration: float = field(compare=False)   # 计算持续时间
    is_cross: bool = field(compare=False)    # 是否跨数据中心
    position: int = field(compare=False)     # 在事件流中的位置

    def is_comm(self):
        return self.event_type.startswith('comm')

class EventStream:
    """事件流类，管理事件序列和状态"""
    def __init__(self, stream_id: int, events: List[Dict], start_time: float):
        self.stream_id = stream_id
        self.events = self._parse_events(events)
        self.start_time = start_time
        self.current_pos = 0
        self.completion_time = None

    def _parse_events(self, raw_events):
        """从原始事件数据解析事件对象"""
        parsed = []
        for idx, e in enumerate(raw_events):
            parsed.append(Event(
                time=0,
                stream_id=self.stream_id,
                event_type=e['type'],
                data_size=e.get('data_size', 0),
                duration=e.get('duration', 0),
                is_cross=e['is_cross'],
                position=idx
            ))
        return parsed

    def schedule_next(self, current_time, event_heap):
        """安排下一个事件"""
        if self.current_pos >= len(self.events):
            return

        next_event = self.events[self.current_pos]
        next_event.time = current_time
        heapq.heappush(event_heap, (next_event.time, next_event))

class LinkManagerBase:
    """链路管理基类"""
    def __init__(self, bandwidth: float):
        self.bandwidth = bandwidth

    def handle_comm_start(self, event: Event, event_heap: list):
        raise NotImplementedError

    def handle_comm_end(self, event: Event, event_heap: list):
        raise NotImplementedError

class PriorityLinkManager(LinkManagerBase):
    """抢占式优先级链路管理"""
    def __init__(self, bandwidth: float):
        super().__init__(bandwidth)
        self.available_time = 0.0
        self.wait_queue = []

    def handle_comm_start(self, event: Event, event_heap: list):
        if event.time >= self.available_time:
            # 直接分配链路
            transmission_time = event.data_size / self.bandwidth
            end_time = event.time + transmission_time
            self.available_time = end_time
            heapq.heappush(event_heap, (end_time, Event(
                end_time, event.stream_id, 'comm_end', 0, 0, False, event.position
            )))
        else:
            # 加入优先队列（按流启动时间排序）
            heapq.heappush(self.wait_queue, (event.stream.start_time, event))

    def handle_comm_end(self, event: Event, event_heap: list):
        # 处理等待队列
        while self.wait_queue:
            stream_start_time, waiting_event = heapq.heappop(self.wait_queue)
            if waiting_event.time >= self.available_time:
                transmission_time = waiting_event.data_size / self.bandwidth
                end_time = waiting_event.time + transmission_time
                self.available_time = end_time
                heapq.heappush(event_heap, (end_time, Event(
                    end_time, waiting_event.stream_id, 'comm_end', 0, 0, False, waiting_event.position
                )))
                break

class FairShareLinkManager(LinkManagerBase):
    """带宽均分链路管理"""
    def __init__(self, bandwidth: float):
        super().__init__(bandwidth)
        self.active_transmissions = []  # (end_time, remaining_data)
        self.wait_queue = []

    def handle_comm_start(self, event: Event, event_heap: list):
        heapq.heappush(self.wait_queue, event)
        self._update_allocations(event.time, event_heap)

    def _update_allocations(self, current_time: float, event_heap: list):
        # 移除已完成事件
        self.active_transmissions = [
            (end, data) for end, data in self.active_transmissions
            if end > current_time
        ]

        # 重新计算所有传输的剩余时间
        while self.wait_queue:
            event = self.wait_queue.pop(0)
            active_count = len(self.active_transmissions) + 1
            share = self.bandwidth / active_count
            
            # 计算传输时间并更新所有活动的传输
            new_active = []
            for end, data in self.active_transmissions:
                elapsed = current_time - (end - data/(share*(active_count-1)/self.bandwidth))
                remaining = data - elapsed * share*(active_count-1)/self.bandwidth
                new_end = current_time + remaining / share
                new_active.append((new_end, remaining))
            
            # 添加新传输
            transmission_time = event.data_size / share
            new_active.append((current_time + transmission_time, event.data_size))
            self.active_transmissions = new_active
            
            # 添加结束事件
            heapq.heappush(event_heap, (
                current_time + transmission_time,
                Event(current_time + transmission_time, event.stream_id, 'comm_end', 0, 0, False, event.position)
            ))

def load_config(streams_file: str, events_file: str, total_ranks: int) -> List[EventStream]:
    """加载配置文件和事件参数"""
    with open(streams_file, "r") as f:
        # 从第二行开始读取
        streams_data = [json.loads(line.strip()) for line in f.readlines()[1:]]
    
    with open(events_file, "r") as f: # 读取changed_data.json文件，获取每个事件的大小和持续时间
        events_params_file = json.load(f)

    def is_cross(src: int, dst: int) -> bool:
        half = total_ranks // 2
        return (src < half) != (dst < half)
    def search_params(events_params_file, event_name): # 查找事件参数
        for rank in events_params_file:
            for item in rank['ops']:
                if item['op_name'] == event_name:
                    return item

    streams = []
    for stream in streams_data:
        events = []  # 提取事件流到events里
        for event_name in stream['path']:  # 遍历依赖路径上的所有事件，解析出事件流
            # 如果连续有两个计算事件，那么从第二个计算事件开始才算events（移除所有前向事件）
            params = search_params(events_params_file, event_name)  # 查找事件参数
            
            # 判断事件名称的开头
            if event_name.startswith(("F", "B")): # 如果是F或B开头，说明是计算事件
                # 计算事件
                events.append({
                    'type': 'compute',
                    'duration': params['duration'],
                    'is_cross': False
                })
            elif event_name.startswith("DATA_"):
                # 通信事件
                parts = event_name.split('_')
                src = int(parts[-2][4:])
                dst = int(parts[-1][4:])
                events.append({
                    'type': 'comm_start',
                    'data_size': params['data_size'],
                    'is_cross': is_cross(src, dst)
                })
            else:
                # DP事件，直接跳出当前循环，我们不分析DP事件
                break
        streams.append(EventStream(sid, events, 0))
    
    # 设置事件流启动时间依赖
    for i in range(1, len(streams)):
        streams[i].start_time = streams[i-1].events[0]['duration']
    
    return streams

def simulate(streams: List[EventStream], link_manager: LinkManagerBase) -> float:
    """运行模拟并返回总完成时间"""
    event_heap = []
    # 初始化所有事件流
    for s in streams:
        s.schedule_next(s.start_time, event_heap)

    while event_heap:
        current_time, event = heapq.heappop(event_heap)
        
        if event.event_type == 'compute':
            # 处理计算事件
            end_time = current_time + event.duration
            streams[event.stream_id].current_pos += 1
            streams[event.stream_id].schedule_next(end_time, event_heap)
        
        elif event.event_type == 'comm_start':
            # 处理通信开始事件
            link_manager.handle_comm_start(event, event_heap)
        
        elif event.event_type == 'comm_end':
            # 处理通信结束事件
            streams[event.stream_id].current_pos += 1
            streams[event.stream_id].schedule_next(current_time, event_heap)
            link_manager.handle_comm_end(event, event_heap)

    # 返回最大完成时间
    return max(s.completion_time for s in streams if s.completion_time is not None)

# 示例使用
if __name__ == "__main__":
    # 加载配置（示例文件路径）
    streams = load_config("streams.json", "events.json", total_ranks=16)
    
    # 运行抢占式策略
    priority_time = simulate([s for s in streams], PriorityLinkManager(bandwidth=10))
    
    # 运行均分策略
    fair_time = simulate([s for s in streams], FairShareLinkManager(bandwidth=10))
    
    print(f"Priority Strategy Time: {priority_time}")
    print(f"Fair Share Strategy Time: {fair_time}")
    print(f"Speedup Ratio: {fair_time / priority_time:.2f}x")