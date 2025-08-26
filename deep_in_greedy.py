from collections import defaultdict, deque
import random
import json
import matplotlib.pyplot as plt
import gurobipy as gp
from gurobipy import GRB
import re
import heapq
import os
forward_color_list = ["#87CEEB", "#1E90FF", "#05054F", "#00008B"]
backward_color_list = ["#90EE90", "#228B22", "#006400", "#004d00"]
delay_color = ["#FFB6C1"]  # 浅粉红色

def ununiform_init_no_communication(DP, PP, B, length_list):
    list = []
    for pp in range(PP * DP) :
        list.append([])
    list.append([])  # 前向通信
    list.append([])  # 后向通信
    
    
    for dp in range(DP):
        for mb in range(B):
            #前向计算
            for pp in range(PP):
                if pp == 0:
                    dependency = None
                else:
                    dependency = f"{mb}_{dp}_{pp - 1}_forward"
                name = f"{mb}_{dp}_{pp}_forward"
                list[PP * dp + pp].append({"id": name, "number": mb, "color": forward_color_list[dp % 4], "length": length_list[pp], "dependency": dependency})
            
            #后向计算
            for pp in reversed(range(PP)):
                if pp == PP - 1:
                    dependency = f"{mb}_{dp}_{PP - 1}_forward"
                else:
                    dependency = f"{mb}_{dp}_{pp + 1}_backward"
                name = f"{mb}_{dp}_{pp}_backward"
                list[PP * dp + pp].append({"id": name, "number": mb, "color": backward_color_list[dp % 4], "length": 2 * length_list[pp], "dependency": dependency})
            
    return list

def ununiform_init(DP, PP, B, communication, length_list = None):
    list = []
    for pp in range(PP * DP) :
        list.append([])
    list.append([])  # 前向通信
    list.append([])  # 后向通信
    
    half_PP = PP // 2
    
    for dp in range(DP):
        for mb in range(B):
            #前向计算
            for pp in range(PP):
                if pp == 0:
                    dependency = None
                elif pp < half_PP:
                    dependency = f"{mb}_{dp}_{pp - 1}_forward"
                elif pp == half_PP:
                    dependency = f"{mb}_{dp}_forward_communication"
                else:
                    dependency = f"{mb}_{dp}_{pp - 1}_forward"
                name = f"{mb}_{dp}_{pp}_forward"
                list[PP * dp + pp].append({"id": name, "number": mb, "color": forward_color_list[dp % 4], "length": length_list[pp], "dependency": dependency})
            
            #后向计算
            for pp in reversed(range(PP)):
                if pp == PP - 1:
                    dependency = f"{mb}_{dp}_{PP - 1}_forward"
                elif pp == half_PP - 1:
                    dependency = f"{mb}_{dp}_backward_communication"
                else:
                    dependency = f"{mb}_{dp}_{pp + 1}_backward"
                name = f"{mb}_{dp}_{pp}_backward"
                list[PP * dp + pp].append({"id": name, "number": mb, "color": backward_color_list[dp % 4], "length": 2 * length_list[pp], "dependency": dependency})
            
            #前向通信
            list[-2].append({"id": f"{mb}_{dp}_forward_communication", 
                             "number": mb, "color": forward_color_list[dp % 4], 
                             "length": communication, 
                             "dependency": f"{mb}_{dp}_{half_PP - 1}_forward"})
            #后向通信
            list[-1].append({"id": f"{mb}_{dp}_backward_communication",
                             "number": mb, "color": backward_color_list[dp % 4],
                             "length": communication,
                             "dependency": f"{mb}_{dp}_{half_PP}_backward"})
    return list

def generate_schedule_json(all_rows, length_list = None, k = 4):
    # greedy的的调度方式，k表示每个GPU上最大的负载（内存开销）；
    # 每行元素之前没有先后关系，仅通过依赖来决定执行顺序；
    
    elements = {}
    dependency_graph = {}
    element_rows = {}
    rows_meta = {}
    dependency_counters = {}
    processed_elements = set()
    event_queue = []
    elements_info = {}

    # 收集所有元素并构建依赖图
    for row_index, row in enumerate(all_rows):
        rows_meta[row_index] = {
            'busy_until': 0,
            'load': 0,
            'queue': [],
            "current_id":None,
        }
        for elem in row:
            elem_id = elem['id']
            elements[elem_id] = elem
            element_rows[elem_id] = row_index
            dependency = elem.get('dependency')
            if dependency is not None:
                if dependency not in dependency_graph:
                    dependency_graph[dependency] = []
                dependency_graph[dependency].append(elem_id)
                dependency_counters[elem_id] = 1
            else:
                dependency_counters[elem_id] = 0

    current_time = 0
    total_elements = len(elements)

    # 初始化无依赖元素的队列
    for elem_id in elements:
        if dependency_counters[elem_id] == 0:
            row_index = element_rows[elem_id]
            meta = rows_meta[row_index]
            if meta['busy_until'] > current_time:
                row_index = element_rows[elem_id]
                rows_meta[row_index]['queue'].append(elem_id)
            else:
                start_time = 0 
                end_time = elements[elem_id]['length']
                elements_info[elem_id] = {
                    'start': start_time,
                    'end': end_time,
                    'elem': elements[elem_id]
                }
                # # 更新负载
                if 'forward' in elem_id:
                    rows_meta[row_index]['load'] += length_list[row_index % PP]
                elif 'backward' in elem_id:
                    rows_meta[row_index]['load'] -= length_list[row_index % PP]
                heapq.heappush(event_queue, (end_time, elem_id))
                meta['busy_until'] = end_time
                meta['current_id'] = elem_id
    


    while len(processed_elements) < total_elements:
        # 处理事件队列
        # while event_queue and event_queue[0][0] <= current_time:
        if event_queue:
            end_time, elem_id = heapq.heappop(event_queue)
            current_time = end_time
            elem = elements[elem_id]
            row = element_rows[elem_id]
            # 触发后续元素
            if elem_id in dependency_graph:
                for dep_elem_id in dependency_graph[elem_id]:
                    dependency_counters[dep_elem_id] -= 1
                    if dependency_counters[dep_elem_id] == 0:
                        if "delay" not in dep_elem_id:
                            dep_row = element_rows[dep_elem_id]
                            rows_meta[dep_row]['queue'].append(dep_elem_id)
                        else:
                            end_time = current_time + delay
                            elements_info[dep_elem_id] = {
                                'start': current_time,
                                'end': end_time,
                                'elem': dep_elem_id}
                            heapq.heappush(event_queue, (end_time, dep_elem_id))
            processed_elements.add(elem_id)

            # 尝试调度各行的元素f"{mb}_{dp}_{PP - 1}_forward"
            # if elem_id == f"{2}_{0}_{PP - 1}_forward":
            #     print(f"{2}_{0}_{PP - 1}_forward")
            #     print(rows_meta[7])
            #     print(current_time)
            # if elem_id == f"{0}_{0}_{PP - 1}_forward":
            #     print(f"{0}_{0}_{PP - 1}_forward")
            #     print(rows_meta[7])
            #     print(current_time)
            # if elem_id == f"{3}_{0}_{6}_forward":
            #     print(f"{3}_{0}_{6}_forward")
            #     print(rows_meta[7])
            #     print(current_time)
                
            progress = False
            for row in rows_meta:
                meta = rows_meta[row]
                if meta['busy_until'] > current_time:
                    continue  # 行忙碌中
                if meta['current_id'] is not None:
                    if meta['current_id'] not in processed_elements:
                        continue

                # 遍历队列寻找可执行元素
                if row >= len(rows_meta) - 2:
                    ####给meta['queue']重新排序
                    meta['queue'] = sorted(
                        meta['queue'],
                        key=lambda x: tuple(map(int, x.split('_')[:2]))  # (mb, dp)
                    )
                have_backward = False
                for i in range(len(meta['queue'])):
                    elem_id = meta['queue'][i]
                    if "backward" in elem_id:
                        have_backward = True
                        break
                for i in range(len(meta['queue'])):
                    elem_id = meta['queue'][i]
                    elem = elements[elem_id]
                    can_execute = False
                    if row < len(rows_meta) - 2 and 'forward' in elem_id:
                        if meta['load'] < k and not have_backward:
                            can_execute = True
                    else:
                        can_execute = True

                    if can_execute:
                        # if (elem_id == "3_0_7_forward"):
                        #     print("3_0_7_forward")
                        #     print(current_time)
                        #     print(rows_meta[7])
                        # 调度此元素
                        start_time = current_time
                        end_time = start_time + elem['length']
                        elements_info[elem_id] = {
                            'start': start_time,
                            'end': end_time,
                            'elem': elem
                        }
                        # # 更新负载
                        if row < len(rows_meta) - 2:
                            if 'forward' in elem_id:
                                rows_meta[row]['load'] += length_list[row % PP]
                            elif 'backward' in elem_id:
                                rows_meta[row]['load'] -= length_list[row % PP]
                        heapq.heappush(event_queue, (end_time, elem_id))
                        meta['busy_until'] = end_time
                        meta['current_id'] = elem_id
                        del meta['queue'][i]
                        progress = True
                        break
        else:
            raise RuntimeError("调度失败：存在循环依赖或未解决的依赖")

        # if not progress:
        #     if not event_queue:
        #         raise RuntimeError("调度失败：存在循环依赖或未解决的依赖")
        #     # 推进到下一个事件时间
        #     current_time = event_queue[0][0]

    return elements_info

def single_DP_visualize_schedule(elements_info, all_rows, PP):
    # 第二阶段：初始化JSON数据结构
    json_data = {
        "mainTable": [[{"color": "", "content": ""} for _ in range(400)] for _ in range(PP)],
        "table1": [[{"color": "", "content": ""} for _ in range(400)] for _ in range(2)],
        "table2": [[{"color": "", "content": ""} for _ in range(400)] for _ in range(2)]
    }
    for table_idx, row_list in enumerate(all_rows):
        # 遍历前 PP 行以及最后两行
        if table_idx < PP:
            table_name = "mainTable"
            row_index = table_idx
        elif table_idx == len(all_rows) - 4:
            table_name = "table1"
            row_index = 1
        elif table_idx == len(all_rows) - 3:
            table_name = "table2"
            row_index = 1
        elif table_idx == len(all_rows) - 2:
            # 最后两行分别对应 table1 和 table2
            table_name = "table1"
            row_index = 0
        elif table_idx == len(all_rows) - 1:
            table_name = "table2"
            row_index = 0
        # elif table_idx >= len(all_rows) - 2:
        #     # 最后两行分别对应 table1 和 table2
        #     table_name = "table1" if table_idx == len(all_rows) - 2 else "table2"
        #     row_index = 0
        else:
            continue  # 跳过中间未使用的行

        # 获取目标行引用
        target_row = json_data[table_name][row_index]

        # 处理每个元素
        for elem in row_list:
            elem_id = elem['id']
            info = elements_info[elem_id]
            
            start_time = int(info['start'])
            length = int(elem['length'])
            color = elem['color']
            number = elem['number']

            # 计算占据的列范围
            for t in range(start_time, start_time + length):
                if t >= 400:
                    break  # 超出表格范围忽略
                
                # 设置颜色
                target_row[t]["color"] = color
                
                # 只在起始列设置数字
                if t == start_time:
                    target_row[t]["content"] = str(number)

    return json_data

def save_to_file(data, filename):
    """保存JSON数据到文件"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
        

DP = 1
PP = 8
B = 48
communication = 8
delay = 0
length_list = PP * [2]
input_rows = ununiform_init_no_communication(DP, PP, B, length_list)
elements_info = generate_schedule_json(input_rows, length_list, k = 16)
json_data = single_DP_visualize_schedule(elements_info, input_rows, PP)
output_dir = "deep_in"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
save_to_file(json_data, 'deep_in/no_communication.json')

input_rows = ununiform_init(DP, PP, B, communication, length_list)
elements_info = generate_schedule_json(input_rows, length_list, k = 20)
json_data = single_DP_visualize_schedule(elements_info, input_rows, PP)
save_to_file(json_data, f'deep_in/communication_{communication}.json')