import json
import ast
import sys
# 计算所有通路的情况，基于statistics_dependency.py的结果分析，复杂度应该在O(event)
# 数据基于standard_time.txt和flow_start_end.txt。分别为标准时间和模拟时间
# 对于事件图，每条边都是时间，对于计算时间，边长固定，对于流事件，边长可变，随链路负载情况而定
# 这里不要使用的s到ms之间的计算容易出现精度问题，所以这里直接用ms来计算
def events_full_path(standard_file, simulate_file, depend_file, target_file):
    graph = {}  # key: event_name, value: {'next_event': [], 'standard_time': , 'start_time': , 'end_time': }
    all_events = set()
    forward_refs = set()  # 所有有依赖（有前向引用）的事件

    with open(depend_file, "r") as f:
        work_load = json.load(f)
    for task in work_load:
        for op in task['ops']:
            op_name = op['op_name']
            all_events.add(op_name)
            if op_name not in graph:
                graph[op_name] = {'next_event': []}
            if 'depends' in op:
                depends_on = op['depends']
                forward_refs.add(op_name)
                if depends_on not in graph:
                    graph[depends_on] = {'next_event': []}
                graph[depends_on]['next_event'].append(op_name)
            if op['op_type'] == 'gpu':
                graph[op_name]['standard_time'] = op['duration'] # ms
                graph[op_name]['time'] = op['duration'] # ms

    # 读取标准时间
    with open(standard_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                data_dict = ast.literal_eval(line)
                op_name = data_dict['flow_id']
                if op_name not in graph:
                    graph[op_name] = {'next_event': []}
                graph[op_name]['standard_time'] = data_dict['standard_time']  # ms

    # 读取模拟时间
    with open(simulate_file, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                data_dict = ast.literal_eval(line)
                op_name = data_dict['flow_id']
                if op_name not in graph:
                    graph[op_name] = {'next_event': []}
                graph[op_name]['time'] = data_dict['time'] # ms

    # 找到起点事件（没有被其他事件依赖的）
    begin_events = all_events - forward_refs

    # 找到终点事件（next_event为空的）
    end_events = {event for event, info in graph.items() if not info['next_event']}

    # DFS
    all_paths = []  # 记录所有路径
    path_count = 0

    def dfs(current, path, time_sum, standard_sum):
        nonlocal path_count
        path.append(current)
        time_sum += graph[current]['time']
        standard_sum += graph[current].get('standard_time', 0)

        if current in end_events:
            # 到达终点，记录路径
            all_paths.append({
                'path': list(path),
                'real_time_sum': time_sum,
                'standard_time_sum': standard_sum
            })
            path_count += 1
        else:
            for next_event in graph[current]['next_event']:
                dfs(next_event, path, time_sum, standard_sum)

        path.pop()

    for start_event in begin_events:
        dfs(start_event, [], 0, 0)

    # 记录结果
    with open(target_file, 'w') as f:
        f.write(f"{ {'total_full_path_num': path_count}}\n")
        for p in all_paths:
            f.write(f"{p}\n")
    return all_paths

# 找到模拟与理论值差距最大的前k个路径
def top_k_paths(all_paths, time_diff_file, k=5):
    # 计算每个路径的差值，并按差值从大到小排序
    sorted_paths = sorted(
        all_paths,
        key=lambda p: abs(p['real_time_sum'] - p['standard_time_sum']),
        reverse=True
    )
    with open(time_diff_file, 'a') as f:
        for p in sorted_paths:
            time_diff = p['real_time_sum'] - p['standard_time_sum']
            if time_diff > 0:
                if p['standard_time_sum'] > 0:
                    ratio = (time_diff / p['standard_time_sum']) * 100
                else:
                    ratio = 0
                f.write(f"{ {'time_diff': time_diff, 'Ratio': ratio, 'path':p['path']}}\n") # ms, %
            # else:
            #     print(f"Time diff error! real_time < standard_time at path {p['path']}")
    # 取前 k 个路径
    return sorted_paths[:k]

def just_events_full_path( depend_file, target_file):
    graph = {}  # key: event_name, value: {'next_event': [], 'standard_time': , 'start_time': , 'end_time': }
    all_events = set()
    forward_refs = set()  # 所有有依赖（有前向引用）的事件

    with open(depend_file, "r") as f:
        work_load = json.load(f)
    for task in work_load:
        for op in task['ops']:
            op_name = op['op_name']
            all_events.add(op_name)
            if op_name not in graph:
                graph[op_name] = {'next_event': []}
            if 'depends' in op and op['depends'] != '':
                depends_on = op['depends']
                forward_refs.add(op_name)
                if depends_on not in graph:
                    graph[depends_on] = {'next_event': []}
                graph[depends_on]['next_event'].append(op_name)

    # 找到起点事件（没有被其他事件依赖的）
    begin_events = all_events - forward_refs

    # 找到终点事件（next_event为空的）
    end_events = {event for event, info in graph.items() if not info['next_event']}

    # DFS
    all_paths = []  # 记录所有路径
    path_count = 0

    def dfs(current, path):
        nonlocal path_count
        path.append(current)
        if current in end_events:
            # 到达终点，记录路径
            all_paths.append({
                'path': list(path)
            })
            path_count += 1
        else:
            for next_event in graph[current]['next_event']:
                dfs(next_event, path)

        path.pop()

    for start_event in begin_events:
        dfs(start_event, [])

    # 记录结果
    with open(target_file, 'w') as f:
        f.write(f"{ {'total_full_path_num': path_count}}\n")
        for p in all_paths:
            f.write(f"{p}\n")
    return all_paths

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python full_path_cal.py <num> <bandwidth> <random/min_max_flows>")
        sys.exit(1)
    num = int(sys.argv[1])
    bandwidth = int(sys.argv[2])
    path_selection_method = sys.argv[3]
    delay = 2
    # file_path = f"../result/link_num_{num}_bandwidth_{bandwidth}_delay_{delay}_route_{path_selection_method}"
    # file_path = f"../result_1024_rack/link_num_{num}_bandwidth_{bandwidth}_delay_{delay}_route_{path_selection_method}"
    # file_path = f"../result_4096_rack/link_num_{num}_bandwidth_{bandwidth}_delay_{delay}_route_{path_selection_method}"
    file_path = f"../result_4096_rack/link_num_{num}_bandwidth_{bandwidth}_delay_{delay}_route_{path_selection_method}_single"
    
    standard_file = f"{file_path}/standard_time.txt"
    simulate_file = f"{file_path}/flow_start_end.txt"
    #work_load_file = f"../data/change_data.json" # 这里为小规模数据
    #work_load_file = f"../data/change_data_1024_rack.json" # 这里为大规模数据
    work_load_file = f"../data_4096_rack/workload_4096_PP32_DP8_TP16_VPP2_BATCH64_NO_PRI.json" # 这里为大规模数据
    target_file = f"{file_path}/full_path.txt"
    time_diff_file = f"{file_path}/time_diff.txt"
    
    all_paths = []
    top_k_path = []
    
    open(target_file, 'w').close()
    open(time_diff_file, 'w').close()
    
    # 1024rack
    all_paths = just_events_full_path(work_load_file, target_file)
    
    
    # 计算所有通路的理论最短耗时和模拟耗时, 16rack
    # all_paths = events_full_path(standard_file, simulate_file, work_load_file, target_file)
    # top_k_path = top_k_paths(all_paths, time_diff_file) # 获取top_k_paths

    # 输出每个路径的时间差和时间差与标准时间的比值
    # for p in top_k_path:
    #     time_diff = abs(p['real_time_sum'] - p['standard_time_sum'])
    #     if p['standard_time_sum'] > 0:
    #         ratio = (time_diff / p['standard_time_sum']) * 100
    #     else:
    #         ratio = 0
    #     print(f"Time Difference: {time_diff} ms, Ratio: {ratio:.2f}%")


