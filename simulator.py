import heapq
from collections import defaultdict
import random
import re
from collections import deque

class Link:
    def __init__(self, bandwidth, delay):
        self.bandwidth = bandwidth  # 带宽（Gbps）
        self.delay = delay          # 时延（ms）
        self.active_flows = set()   # 当前使用该链路的流

    def available_bandwidth(self):
        """可用带宽（Gbps）"""
        return self.bandwidth / len(self.active_flows) if self.active_flows else self.bandwidth

    def calculate_load(self):
        """链路负载（Gbps）"""
        return sum(flow.rate / 1000 for flow in self.active_flows)  # Mbps转Gbps

class Flow:
    def __init__(self, flow_id, size, paths, dependency=None):
        self.flow_id = flow_id
        self.size = size            # 数据量（MB）
        self.paths = paths            # 路径（Link列表）
        self.path = None            # 实际选择的路径（启动时确定）
        self.dependency = dependency if dependency is not None else []  # 改为列表
        self.start_time = None      # 开始时间
        self.end_time = None        # 结束时间
        self.rate = 0               # 当前速率（Mbps）
        self.remaining_size = size  # 剩余数据量（MB）
        self.current_event = None   # 当前关联的事件
        self.last_begin_time = 0    # 上一次速率改变的时间
        self.debug = True
        self.file_name = None

    def update_rate(self):
        """根据路径中的瓶颈链路更新速率"""
        min_rate = min(link.available_bandwidth() * 1000 for link in self.path)  # Gbps转Mbps
        self.rate = min_rate if min_rate != float('inf') else 0

    def transmission_time(self):
        """剩余传输时间（秒）"""
        if self.remaining_size < 0 or self.rate < 0:
            if (self.debug):
                with open(f"result/{self.file_name}/error.txt", "a") as file:
                    error_info = {
                        "error":"transmission_time or self.rate less than 0",
                        "flow_id": self.flow_id,
                        "remaining_size": self.remaining_size,
                        "rate": self.rate
                    }
                    file.write(f"{error_info}\n")
                return 0  # 剩余大小为0或速率为0时直接返回0
        return (self.remaining_size * 8) / self.rate if self.rate else float('inf')

    def propagation_time(self):
        """总传播时延（秒）"""
        return sum(link.delay for link in self.path) / 1000  # ms转秒

class Task:
    def __init__(self, task_id, compute_time, dependency=None):
        self.task_id = task_id
        self.compute_time = compute_time  # 计算时间（秒）
        self.dependency = dependency if dependency is not None else []  # 改为列表
        self.start_time = None
        self.end_time = None

class Event:
    def __init__(self, time, event_type, obj):
        self.time = time
        self.event_type = event_type  # 事件类型：flow_start, flow_end, task_start, task_end
        self.obj = obj                # 关联的Flow或Task对象

    def __lt__(self, other):
        return self.time < other.time

class Simulator:
    def __init__(self, file_name, path_selection_method='random'):
        self.links = {}                 # {link_id: Link}
        self.flows = {}                 # {flow_id: Flow}
        self.tasks = {}                 # {task_id: Task}
        self.event_queue = []           # 事件优先队列
        self.current_time = 0           # 当前仿真时间
        self.completed_events = set()   # 已完成的依赖事件集合
        self.event_dependencies = defaultdict(list)  # 事件到依赖者的映射
        self.path_selection_method = path_selection_method
        self.file_name = file_name
        self.debug = True
        self.object_dependencies = {}  # 对象到其依赖列表的映射
        self.completed_deps = defaultdict(set)  # 对象到已完成的依赖事件的集合
        self.rank_queues = defaultdict(deque)   # 各Rank的任务队列
        self.current_rank_tasks = {}            # 当前各Rank正在执行的任务
    def extract_rank(self, task_id):
            """从task_id中提取Rank标识"""
            match = re.search(r'_Rank(\d+)$', task_id)
            if match:
                return match.group(1)  # 返回字符串形式的Rank标识
            raise ValueError(f"Invalid task_id format: {task_id}")

    def add_link(self, link_id, bandwidth, delay):
        self.links[link_id] = Link(bandwidth, delay)

    def add_flow(self, flow_id, size, paths, dependency=None):
        dependency = dependency if dependency is not None else []
        flow = Flow(flow_id, size, paths, dependency)
        flow.file_name = self.file_name
        self.flows[flow_id] = flow
        if dependency:
            # 检查所有依赖是否已满足
            all_met = all(dep in self.completed_events for dep in dependency)
            if all_met:
                self.schedule_event(Event(self.current_time, 'flow_start', flow))
            else:
                self.object_dependencies[flow] = dependency.copy()
                for dep in dependency:
                    self.event_dependencies[dep].append(flow)
                self.completed_deps[flow] = set()
        else:
            self.schedule_event(Event(0, 'flow_start', flow))

    def add_task(self, task_id, compute_time, dependency=None):
        dependency = dependency if dependency is not None else []
        task = Task(task_id, compute_time, dependency)
        self.tasks[task_id] = task
        if dependency:
            all_met = all(dep in self.completed_events for dep in dependency)
            if all_met:
                self.schedule_event(Event(self.current_time, 'task_start', task))
            else:
                self.object_dependencies[task] = dependency.copy()
                for dep in dependency:
                    self.event_dependencies[dep].append(task)
                self.completed_deps[task] = set()
        else:
            self.schedule_event(Event(0, 'task_start', task))

    def schedule_event(self, event):
        heapq.heappush(self.event_queue, event)

    def cancel_event(self, event):
        """取消指定事件"""
        if event in self.event_queue:
            self.event_queue.remove(event)
            heapq.heapify(self.event_queue)
            
            
    def update_flow_rates(self):
        active_flows = set()
        for link in self.links.values():
            for flow in link.active_flows:
                if flow not in active_flows:
                    if flow.current_event:
                        transferred = flow.rate * (self.current_time - flow.last_begin_time) / 8
                        flow.remaining_size = max(flow.remaining_size - transferred, 0)
                        self.cancel_event(flow.current_event)
                    active_flows.add(flow)
        active_flows = list(active_flows)
        
        remaining_bandwidth = {link: link.bandwidth for link in self.links.values()}
        remaining_flows_count = {link: len(link.active_flows) for link in self.links.values()}
        allocated = {flow: False for flow in active_flows}
        
        # 分配速率
        while True:
            min_rate = float('inf')
            min_link = None
            
            # 找到所有链路中的最小候选速率
            for link in self.links.values():
                count = remaining_flows_count.get(link, 0)
                if count == 0:
                    continue
                current_rate = remaining_bandwidth[link] / count
                if current_rate < min_rate:
                    min_rate = current_rate
                    min_link = link
            
            if not min_link:
                break
            else:
                if (min_rate == float('inf')):
                    print("min_rate is inf")
                    break
                if (min_rate == 0):
                    print("min_rate is 0")
                flows_to_allocate = [flow for flow in min_link.active_flows if not allocated[flow]]
                if not flows_to_allocate:
                    print("no flows to allocate")
                    continue
                
                for flow in flows_to_allocate:
                    flow.rate = min_rate * 1000  # 转换为Mbps
                    allocated[flow] = True
                
                for flow in flows_to_allocate:
                    for l in flow.path:
                        remaining_bandwidth[l] -= min_rate
                        remaining_flows_count[l] -= 1
        
        # 处理未分配速率的流
        for flow in active_flows:
            if not allocated[flow]:
                flow.rate = 0
                print(f"Flow {flow.flow_id} has no bandwidth")
        
        for flow in active_flows:
            flow.rate = min(link.available_bandwidth() * 1000 for link in flow.path)  # Gbps转Mbps
    
        # 重新调度所有流的结束事件并记录
        rate_record = {}
        bottleneck_dict = {}
        for flow in active_flows:
            if flow.rate > 0:
                transmission_time = flow.transmission_time()
                end_time = self.current_time + transmission_time + flow.propagation_time()
                if (self.debug):
                    if(end_time < self.current_time):
                        with open(f"result/{self.file_name}/error.txt", "a") as file:
                            error_info = {
                                "error":"end_time less than current_time",
                                "time": self.current_time,
                                "flow_id": flow.flow_id,
                                "transmission_time": transmission_time,
                                "end_time": end_time
                            }
                            file.write(f"{error_info}\n")
                end_time = max(end_time, self.current_time) 
                flow.current_event = Event(end_time, 'flow_end', flow)
                flow.last_begin_time = self.current_time
                self.schedule_event(flow.current_event)
                rate_record[flow.flow_id] = flow.rate / 1000
                
                min_bandwidth = min(link.available_bandwidth() for link in flow.path)
                bottleneck_links = [link for link in flow.path if link.available_bandwidth() == min_bandwidth]
                related_flows = []
                for link in bottleneck_links:
                    related_flows.extend(f.flow_id for f in link.active_flows if f != flow)
                bottleneck_dict[flow.flow_id] = list(set(related_flows))
        
        # 记录速率和瓶颈信息
        if rate_record:
            with open(f"result/{self.file_name}/rate_record.txt", "a") as file:
                file.write(f"{ {'time': self.current_time, 'flow': rate_record} }\n")
        if bottleneck_dict:
            with open(f"result/{self.file_name}/bottleneck_flows.txt", "a") as file:
                file.write(f"{ {'time': self.current_time, 'bottleneck_flows': bottleneck_dict} }\n")

        
    def handle_flow_start(self, flow):
        
        if flow.path is None:
            if self.path_selection_method == 'random':
                flow.path = random.choice(flow.paths)
            elif self.path_selection_method == 'min_max_flows':
                min_max = float('inf')
                selected_path = flow.paths[0]
                for path in flow.paths:
                    current_max = max(len(link.active_flows) for link in path)
                    if current_max < min_max:
                        min_max = current_max
                        selected_path = path
                flow.path = selected_path
            else:
                raise ValueError("Invalid path selection method")
                
        # 将路径信息写入records.txt
        path_ids = [link_id for link_id, link in self.links.items() if link in flow.path]
        with open(f"result/{self.file_name}/flow_path_record.txt", "a") as file:
            file.write(
                f"Flow,{flow.flow_id},path_selected,{path_ids},{self.current_time}\n"
            )
        
        """处理流开始事件"""
        # 记录流开始日志
        with open(f"result/{self.file_name}/records.txt", "a") as file:
            file.write(f"Flow,{flow.flow_id},begin,{self.current_time}\n")
        
        # 记录链路负载变化
        with open(f"result/{self.file_name}/link_load.txt", "a") as file:
            load_dict = {
                "time": self.current_time,
                "link": {link_id: link.calculate_load() for link_id, link in self.links.items()}
            }
            file.write(f"{load_dict}\n")
        
        # 记录链路利用率变化
        with open(f"result/{self.file_name}/link_util.txt", "a") as file:
            load_dict = {
                "time": self.current_time,
                "link": {link_id: link.calculate_load() / link.bandwidth for link_id, link in self.links.items()}
            }
            file.write(f"{load_dict}\n")
        with open(f"result/{self.file_name}/link_flow_num.txt", "a") as file:
            flow_num_dict = {
                "time": self.current_time,
                "link": {link_id: len(link.active_flows) for link_id, link in self.links.items()}
            }
            file.write(f"{flow_num_dict}\n")

        # 添加流到所有路径链路
        for link in flow.path:
            link.active_flows.add(flow)
        self.update_flow_rates()

    def handle_flow_end(self, flow):
        """处理流结束事件（完整逻辑）"""
        flow.end_time = self.current_time
        flow.remaining_size = 0

        # 记录流结束日志
        with open(f"result/{self.file_name}/records.txt", "a") as file:
            file.write(f"Flow,{flow.flow_id},finish,{self.current_time}\n")

        # 记录链路负载变化
        with open(f"result/{self.file_name}/link_load.txt", "a") as file:
            load_dict = {
                "time": self.current_time,
                "link": {link_id: link.calculate_load() for link_id, link in self.links.items()}
            }
            file.write(f"{load_dict}\n")
        with open(f"result/{self.file_name}/link_flow_num.txt", "a") as file:
            flow_num_dict = {
                "time": self.current_time,
                "link": {link_id: len(link.active_flows) for link_id, link in self.links.items()}
            }
            file.write(f"{flow_num_dict}\n")

        # 从链路移除流
        for link in flow.path:
            if flow in link.active_flows:
                link.active_flows.remove(flow)
        self.update_flow_rates()

        # 生成完成事件名称（格式必须与依赖列表中的名称一致）
        completed_event = f"flow_end_{flow.flow_id}"
        self.completed_events.add(completed_event)

        # 获取所有依赖此事件的对象
        dependents = self.event_dependencies.get(completed_event, [])

        # 遍历所有依赖此事件的对象
        for dependent in dependents.copy():  # 使用副本避免遍历时修改原始列表
            # 将此事件标记为已完成的依赖
            self.completed_deps[dependent].add(completed_event)

            # 获取该对象的所有依赖列表
            required_deps = self.object_dependencies.get(dependent, [])

            # 检查是否所有依赖都已满足
            if all(dep in self.completed_deps[dependent] for dep in required_deps):
                # 根据类型创建新事件
                if isinstance(dependent, Flow):
                    new_event = Event(self.current_time, 'flow_start', dependent)
                elif isinstance(dependent, Task):
                    new_event = Event(self.current_time, 'task_start', dependent)
                else:
                    continue  # 无效类型跳过

                # 调度事件并清理状态
                self.schedule_event(new_event)
                if dependent in self.object_dependencies:
                    del self.object_dependencies[dependent]
                if dependent in self.completed_deps:
                    del self.completed_deps[dependent]

        # 清理已处理的依赖关系（防止内存泄漏）
        if completed_event in self.event_dependencies:
            del self.event_dependencies[completed_event]

    def handle_task_start(self, task):
            """修改后的任务开始处理（包含排队逻辑）"""
            rank = self.extract_rank(task.task_id)
            
            # 检查Rank是否被占用
            if rank in self.current_rank_tasks:
                # 加入队列并记录
                self.rank_queues[rank].append(task)
                # with open(f"result/{self.file_name}/records.txt", "a") as file:
                #     file.write(f"Task,{task.task_id},queued,{self.current_time},Rank{rank}\n")
                return

            # 占用Rank并开始执行
            self.current_rank_tasks[rank] = task
            with open(f"result/{self.file_name}/records.txt", "a") as file:
                file.write(f"Task,{task.task_id},begin,{self.current_time}\n")
            
            # 计算结束时间并调度
            task.start_time = self.current_time
            end_event = Event(self.current_time + task.compute_time, 'task_end', task)
            self.schedule_event(end_event)

    def handle_task_end(self, task):
        """处理任务结束事件（完整逻辑）"""
        task.end_time = self.current_time

        # 记录任务结束日志
        with open(f"result/{self.file_name}/records.txt", "a") as file:
            file.write(f"Task,{task.task_id},finish,{self.current_time}\n")

        # 生成完成事件名称（格式必须与依赖列表中的名称一致）
        completed_event = f"task_end_{task.task_id}"
        self.completed_events.add(completed_event)

        # 获取所有依赖此事件的对象
        dependents = self.event_dependencies.get(completed_event, [])

        # 遍历所有依赖此事件的对象
        for dependent in dependents.copy():
            # 更新完成状态
            self.completed_deps[dependent].add(completed_event)

            # 获取该对象的所有依赖列表
            required_deps = self.object_dependencies.get(dependent, [])

            # 检查是否所有依赖都已满足
            if all(dep in self.completed_deps[dependent] for dep in required_deps):
                # 根据类型创建事件
                if isinstance(dependent, Flow):
                    new_event = Event(self.current_time, 'flow_start', dependent)
                elif isinstance(dependent, Task):
                    new_event = Event(self.current_time, 'task_start', dependent)
                else:
                    continue

                # 调度并清理状态
                self.schedule_event(new_event)
                if dependent in self.object_dependencies:
                    del self.object_dependencies[dependent]
                if dependent in self.completed_deps:
                    del self.completed_deps[dependent]

        # 清理已处理的依赖关系
        if completed_event in self.event_dependencies:
            del self.event_dependencies[completed_event]

        rank = self.extract_rank(task.task_id)
        if self.current_rank_tasks.get(rank) == task:
            del self.current_rank_tasks[rank]
        
        # 检查并调度队列中的下一个任务
        if self.rank_queues[rank]:
            next_task = self.rank_queues[rank].popleft()
            # 立即调度（时间为当前时间）
            self.schedule_event(Event(self.current_time, 'task_start', next_task))
        
        
    def run(self):
        """运行仿真"""
        while self.event_queue:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            
            if event.event_type == 'flow_start':
                self.handle_flow_start(event.obj)
            elif event.event_type == 'flow_end':
                self.handle_flow_end(event.obj)
            elif event.event_type == 'task_start':
                self.handle_task_start(event.obj)
            elif event.event_type == 'task_end':
                self.handle_task_end(event.obj)

# # 示例测试
# if __name__ == "__main__":
#     # 初始化仿真环境
#     sim = Simulator()
    
#     # 添加网络链路
#     sim.add_link("link1", 10, 1)  # 10Gbps带宽，1ms延迟
#     sim.add_link("link2", 20, 2)
    
#     # 添加流和依赖关系
#     sim.add_flow("flow1", 8000, [sim.links["link1"]])  # 8000MB数据
#     sim.add_flow("flow2", 16000, [sim.links["link1"], sim.links["link2"]], "flow_end_flow1")
    
#     # 添加任务和依赖关系
#     sim.add_task("task1", 5, "flow_end_flow2")
#     sim.add_task("task2", 3, "task_end_task1")
    
#     # 运行仿真
#     sim.run()
    
#     # 输出结果
#     print("===== 流执行情况 =====")
#     for flow in sim.flows.values():
#         print(f"Flow {flow.flow_id}: {flow.start_time:.2f}s → {flow.end_time:.2f}s")
    
#     print("\n===== 任务执行情况 =====")
#     for task in sim.tasks.values():
#         print(f"Task {task.task_id}: {task.start_time:.2f}s → {task.end_time:.2f}s")