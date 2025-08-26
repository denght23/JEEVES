from collections import defaultdict, deque
import random
import json
import matplotlib.pyplot as plt


forward_color_list = ["#87CEEB", "#1E90FF", "#05054F", "#00008B"]
backward_color_list = ["#90EE90", "#228B22", "#006400", "#004d00"]


import heapq

def get_optimal_memory_limit(DP, PP, communication):
    forward_time = 2
    backward_time = 2 * forward_time
    bound = PP * (forward_time + backward_time) + DP * communication
    if communication * DP > forward_time + backward_time:
        # 如果通信时间大于前向和后向计算时间之和，则内存限制为通信时间
        
        for i in range(100):
            if communication * DP * i + forward_time > bound:
                return 2 * (i)
    else:
        # 如果通信时间小于等于前向和后向计算时间之和，则内存限制为前向和后向计算时间之和
        for i in range(100):
            if (forward_time + backward_time) * i + communication * DP > bound:
                return 2 * (i)

def calculate_optimal_time(DP, PP, B, communication):
    forward_time = 2
    backward_time = 2 * forward_time
    time = PP * (forward_time + backward_time) + (DP + 1) * communication + (B - 1) * max(DP * communication, forward_time + backward_time)
    return time

def generate_length_list(PP):
    # 生成长度列表，长度为PP的偶数
    return [2/3, 9/10, 9/10, 9/10]
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
            'queue': []
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
                    'elem': elem
                }
                # # 更新负载
                if 'forward' in elem_id:
                    rows_meta[row_index]['load'] += length_list[row_index % PP]
                elif 'backward' in elem_id:
                    rows_meta[row_index]['load'] -= length_list[row_index % PP]
                heapq.heappush(event_queue, (end_time, elem_id))
                meta['busy_until'] = end_time
    


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
                        dep_row = element_rows[dep_elem_id]
                        rows_meta[dep_row]['queue'].append(dep_elem_id)
            processed_elements.add(elem_id)

            # 尝试调度各行的元素
            progress = False
            for row in rows_meta:
                meta = rows_meta[row]
                if meta['busy_until'] > current_time:
                    continue  # 行忙碌中

                # 遍历队列寻找可执行元素
                if row >= len(rows_meta) - 2:
                    ####给meta['queue']重新排序
                    meta['queue'] = sorted(
                        meta['queue'],
                        key=lambda x: tuple(map(int, x.split('_')[:2]))  # (mb, dp)
                    )
                for i in range(len(meta['queue'])):
                    elem_id = meta['queue'][i]
                    elem = elements[elem_id]
                    can_execute = False
                    if row < len(rows_meta) - 2 and 'forward' in elem_id:
                        if meta['load'] < k:
                            can_execute = True
                    else:
                        can_execute = True

                    if can_execute:
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


def m_vp_int(DP, PP, B, commnication, warm_up_num = 4):
    ####warm_up_num: 考虑内存限制，预热的micro batch num
    info_dict = {"index": {}, "dependency": {}, "color":{}, "length":{}}
    FORWARD_TIME = 1
    BACKWARD_TIME = 2
    if PP % 2 != 0:
        raise ValueError("PP维度必须是偶数")
    half_PP = PP // 2
    m_list = []
    for i in range(PP + 2):
        m_list.append([])
    for mb in range(B):
        for dp in range(DP):
            action_list = []
            for i in range(half_PP):
                name = f"{mb}_{dp}_{i}_a_forward"
                action_list.append(name)
                info_dict["index"][name] = mb
                info_dict["color"][name] = forward_color_list[dp]
                info_dict["length"][name] = FORWARD_TIME
                m_list[i].append(name)
            for i in reversed(range(half_PP)):
                name = f"{mb}_{dp}_{i}_b_forward"
                action_list.append(name)
                info_dict["index"][name] = mb
                info_dict["color"][name] = forward_color_list[dp]
                info_dict["length"][name] = FORWARD_TIME
                m_list[i].append(name)
            name = f"{mb}_{dp}_forward_communication"
            action_list.append(name)
            info_dict["index"][name] = mb
            info_dict["color"][name] = forward_color_list[dp]
            info_dict["length"][name] = commnication
            m_list[PP].append(name)
            for i in range(half_PP, PP):
                name = f"{mb}_{dp}_{i}_a_forward"
                action_list.append(name)
                info_dict["index"][name] = mb
                info_dict["color"][name] = forward_color_list[dp]
                info_dict["length"][name] = FORWARD_TIME
                m_list[i].append(name)
            for i in reversed(range(half_PP, PP)):
                name = f"{mb}_{dp}_{i}_b_forward"
                action_list.append(name)
                info_dict["index"][name] = mb
                info_dict["color"][name] = forward_color_list[dp]
                info_dict["length"][name] = FORWARD_TIME
                m_list[i].append(name)
            for i in  range(half_PP, PP):
                name = f"{mb}_{dp}_{i}_a_backward"
                action_list.append(name)
                info_dict["index"][name] = mb
                info_dict["color"][name] = backward_color_list[dp]
                info_dict["length"][name] = BACKWARD_TIME
                m_list[i].append(name)
            for i in reversed(range(half_PP, PP)):
                name = f"{mb}_{dp}_{i}_b_backward"
                action_list.append(name)
                info_dict["index"][name] = mb
                info_dict["color"][name] = backward_color_list[dp]
                info_dict["length"][name] = BACKWARD_TIME
                m_list[i].append(name)
            name = f"{mb}_{dp}_backward_communication"
            action_list.append(name)
            info_dict["index"][name] = mb
            info_dict["color"][name] = backward_color_list[dp]
            info_dict["length"][name] = commnication
            m_list[PP + 1].append(name)
            for i in range(half_PP):
                name = f"{mb}_{dp}_{i}_b_backward"
                action_list.append(name)
                info_dict["index"][name] = mb
                info_dict["color"][name] = backward_color_list[dp]
                info_dict["length"][name] = BACKWARD_TIME
                m_list[i].append(name)
            for i in reversed(range(half_PP)):
                name = f"{mb}_{dp}_{i}_a_backward"
                action_list.append(name)
                info_dict["index"][name] = mb
                info_dict["color"][name] = backward_color_list[dp]
                info_dict["length"][name] = BACKWARD_TIME
                m_list[i].append(name)
            for index, name in enumerate(action_list):
                if index == 0:
                    info_dict["dependency"][name] = None
                else:
                    info_dict["dependency"][name] = action_list[index - 1]
                
    input_list = []
    for index, row in enumerate(m_list):
        if index < PP + 2:
            input_list.append([])
            for elem in row:
                input_list[-1].append({"id": elem, "number": info_dict["index"][elem], "color": info_dict["color"][elem], "length": info_dict["length"][elem], "dependency": info_dict["dependency"][elem]})
    #####给每个DP的GPU0的forward action重新指定dependecy
    for dp in range(DP):
        GPU_0_row = dp * (PP)
        for elem in input_list[GPU_0_row]:
            if "a_forward" in elem["id"]:
                index = elem["number"]
                if index == 0:
                    elem["dependency"] = None
                elif index < warm_up_num:
                    elem["dependency"] = f"{index - 1}_{dp}_{0}_a_forward"
                else:
                    elem["dependency"] = f"{index - warm_up_num}_{dp}_{0}_b_backward"

                    
    return input_list
                
    
                
                
                
        
    

def test_init(DP, PP, B, communication):
    info_dict = {"index": {}, "dependency": {}, "color":{}, "length":{}}
    #DP:DP维度，PP：PP维度，B：micro batch num
    # 每个micro batch 的id的依赖链：
    # {batch_id}_{DP}_{0}_forward -> {batch_id}_{DP}_{1}_forward,..-> {batch_id}_{DP}_{PP/2-1}_forward -> {batch_id}_{DP}_forward_communication->{batch_id}_{DP}_{PP/2}_forward->...->{batch_id}_{DP}_{PP-1}_forward->
    # {batch_id}_{DP}_{PP-1}_backward -> {batch_id}_{DP}_{PP-2}_backward ..-> {batch_id}_{DP}_{PP/2}_backward -> {batch_id}_{DP}_backward_communication->{batch_id}_{DP}_{PP/2 -1}_backward->...->{batch_id}_{DP}_{0}_backward
    if PP % 2 != 0:
        raise ValueError("PP维度必须是偶数")
    half_PP = PP // 2
    
    # 初始化数据结构
    excution_begin_dict = {}
    info_dict = {"index": {}, "dependency": {}, "color":{}, "length":{}}
    task_lists = defaultdict(list)
    forward_comm_list = []
    backward_comm_list = []
    
    # 前向/后向阶段时间常量
    FORWARD_TIME = 1
    BACKWARD_TIME = 2
    
    # 主时间轴
    forward_communication_init_time = half_PP * FORWARD_TIME
    
    for mb in range(B):
        for dp in range(DP):
            forward_comm_id = f"{mb}_{dp}_forward_communication"
            info_dict["dependency"][forward_comm_id] = f"{mb}_{dp}_{half_PP - 1}_forward"
            info_dict["index"][forward_comm_id] = mb
            info_dict["color"][forward_comm_id] = forward_color_list[dp]
            info_dict["length"][forward_comm_id] = communication
            
            for pp in range(PP):
                # 前向计算阶段
                calc_id = f"{mb}_{dp}_{pp}_forward"
                if pp == 0:
                    info_dict["dependency"][calc_id] = None
                elif pp == half_PP:
                    info_dict["dependency"][calc_id] = forward_comm_id
                else:
                    info_dict["dependency"][calc_id] = f"{mb}_{dp}_{pp - 1}_forward"
                info_dict["index"][calc_id] = mb
                info_dict["color"][calc_id] = forward_color_list[dp]
                info_dict["length"][calc_id] = FORWARD_TIME
                
            backward_comm_id = f"{mb}_{dp}_backward_communication"
            info_dict["dependency"][backward_comm_id] = f"{mb}_{dp}_{half_PP}_backward"
            info_dict["index"][backward_comm_id] = mb
            info_dict["color"][backward_comm_id] = backward_color_list[dp]
            info_dict["length"][backward_comm_id] = BACKWARD_TIME
            
            for pp in range(PP):
                # 后向计算阶段
                calc_id = f"{mb}_{dp}_{pp}_backward"
                if pp == PP - 1:
                    info_dict["dependency"][calc_id] = f"{mb}_{dp}_{PP - 1}_forward"
                elif pp == half_PP - 1:
                    info_dict["dependency"][calc_id] = backward_comm_id
                else:
                    info_dict["dependency"][calc_id] = f"{mb}_{dp}_{pp + 1}_backward"
                info_dict["index"][calc_id] = mb
                info_dict["color"][calc_id] = backward_color_list[dp]
                info_dict["length"][calc_id] = BACKWARD_TIME

    for mb in range(B):
        for dp in range(DP):
            # 前向通信阶段
            forward_comm_id = f"{mb}_{dp}_forward_communication"
            excution_begin_dict[forward_comm_id] = forward_communication_init_time
            forward_comm_list.append(forward_comm_id)
            # 前半段前向计算
            for pp in range(half_PP):
                calc_id = f"{mb}_{dp}_{pp}_forward"
                start_time = forward_communication_init_time - (half_PP - pp) * FORWARD_TIME
                excution_begin_dict[calc_id] = start_time
                
                
                # 添加到对应PP位置的列表
                task_lists[(dp, pp)].append(calc_id)
            
            # 后半段前向计算（含通信时间）
            for pp in range(half_PP, PP):
                calc_id = f"{mb}_{dp}_{pp}_forward"
                start_time = forward_communication_init_time + (pp - half_PP) * FORWARD_TIME + communication
                excution_begin_dict[calc_id] = start_time
                
                task_lists[(dp, pp)].append(calc_id)
            
            # 后半段后向计算
            backward_start_base = forward_communication_init_time + half_PP * FORWARD_TIME + communication
            for pp in range(half_PP, PP):
                calc_id = f"{mb}_{dp}_{pp}_backward"
                start_time = backward_start_base + (PP - pp - 1) * BACKWARD_TIME
                excution_begin_dict[calc_id] = start_time
                
                task_lists[(dp, pp)].append(calc_id)
            
            # 后向通信阶段
            backward_comm_id = f"{mb}_{dp}_backward_communication"
            comm_time = forward_communication_init_time + (half_PP + PP) * FORWARD_TIME + communication
            excution_begin_dict[backward_comm_id] = comm_time
            backward_comm_list.append(backward_comm_id)
            
            # 前半段后向计算
            for pp in range(half_PP):
                calc_id = f"{mb}_{dp}_{pp}_backward"
                start_time = comm_time + (half_PP - pp) * BACKWARD_TIME
                excution_begin_dict[calc_id] = start_time
                
                task_lists[(dp, pp)].append(calc_id)
            
            forward_communication_init_time += communication  # 下一个micro batch的时间基准

    # 构建最终列表
    final_lists = []
    
    # 前DP*PP个列表
    for dp in range(DP):
        for pp in range(PP):
            # 获取该DP/PP位置的所有任务
            tasks = task_lists[(dp, pp)]
            
            # 排序逻辑：按开始时间，相同时间随机排序
            sorted_tasks = sorted(
                tasks,
                key=lambda x: (excution_begin_dict[x], random.random())
            )
            
            final_lists.append(sorted_tasks)
    
    # 最后两个通信列表
    final_lists.append(
        sorted(forward_comm_list, key=lambda x: (excution_begin_dict[x], random.random()))
    )
    final_lists.append(
        sorted(backward_comm_list, key=lambda x: (excution_begin_dict[x], random.random()))
    )

    return final_lists, excution_begin_dict, info_dict


def single_DP_visualize_schedule(elements_info, all_rows):
    # 第二阶段：初始化JSON数据结构
    json_data = {
        "mainTable": [[{"color": "", "content": ""} for _ in range(160)] for _ in range(4)],
        "table1": [[{"color": "", "content": ""} for _ in range(160)]],
        "table2": [[{"color": "", "content": ""} for _ in range(160)]]
    }
    for table_idx, row_list in enumerate(all_rows):
        # 确定目标表格和行索引
        if table_idx < 4:
            table_name = "mainTable"
            row_index = table_idx
        elif table_idx == 4:
            table_name = "table1"
            row_index = 0
        else:
            table_name = "table2"
            row_index = 0

        # 获取目标行引用
        target_row = json_data[table_name][row_index]

        # 处理每个元素
        for elem in row_list:
            elem_id = elem['id']
            info = elements_info[elem_id]
            
            start_time = info['start']
            length = elem['length']
            color = elem['color']
            number = elem['number']

            # 计算占据的列范围
            for t in range(start_time, start_time + length):
                if t >= 160:
                    break  # 超出表格范围忽略
                
                # 设置颜色
                target_row[t]["color"] = color
                
                # 只在起始列设置数字
                if t == start_time:
                    target_row[t]["content"] = str(number)

    return json_data
    

def visualize_schedule(elements_info, all_rows):
    # 第二阶段：初始化JSON数据结构
    json_data = {
        "mainTable": [[{"color": "", "content": ""} for _ in range(160)] for _ in range(4)],
        "mainTable2": [[{"color": "", "content": ""} for _ in range(160)] for _ in range(4)],
        "table1": [[{"color": "", "content": ""} for _ in range(160)]],
        "table2": [[{"color": "", "content": ""} for _ in range(160)]]
    }

    # 第三阶段：填充颜色和数字到表格
    for table_idx, row_list in enumerate(all_rows):
        # 确定目标表格和行索引
        if table_idx < 4:
            table_name = "mainTable"
            row_index = table_idx
        elif table_idx < 8:
            table_name = "mainTable2"
            row_index = table_idx - 4
        elif table_idx == 8:
            table_name = "table1"
            row_index = 0
        else:
            table_name = "table2"
            row_index = 0

        # 获取目标行引用
        target_row = json_data[table_name][row_index]

        # 处理每个元素
        for elem in row_list:
            elem_id = elem['id']
            info = elements_info[elem_id]
            
            start_time = info['start']
            length = elem['length']
            color = elem['color']
            number = elem['number']

            # 计算占据的列范围
            for t in range(start_time, start_time + length):
                if t >= 160:
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
        
        
#################### DP1配置通信 ###############
# DP = 1
# PP = 4
# communication = 0
# B = 6
# memory_limit = 8
# # length_list = generate_length_list(PP)
# # length_list = [4/3, 8/5, 38/15, 38/15]  # 为了测试方便，长度都设置为1
# length_list = [2,2,2,2]
# # length_list = [1.3333333333333333, 2.2222222222222228, 2.2222222222222228, 2.2222222222222223]
# # length_list = [1.6, 1.6, 2.4, 2.4]
# # length_list = [1.6, 2.0, 2.2, 2.2]

################### DP2配置通信 ###############
# DP = 2
# PP = 4
# communication = 3
# B = 12
# memory_limit = 100
# # length_list = generate_length_list(PP)
# # length_list = [4/3, 8/5, 38/15, 38/15]  # 为了测试方便，长度都设置为1
# length_list = [2,2,2,2]
# length_list = [1.3333333333333333, 2.2222222222222228, 2.2222222222222228, 2.2222222222222223]
# length_list = [1.6, 1.6, 2.4, 2.4]
# length_list = [1.6, 2.0, 2.2, 2.2]

###############DP4 配置############
# DP = 4
# PP = 8
# communication = 1.5
# B = 12
# memory_limit = 16
# length_list = [2,2,2,2,2,2,2,2] # 为了测试方便，长度都设置为1
# # length_list = [1.7777777777777777, 2.0, 2.0370370370370376, 2.0370370370370376, 2.0370370370370376, 2.0370370370370376, 2.0370370370370376, 2.0370370370370376]


#############massiveDP 配置###########
DP = 64
PP = 8
communication = 6 / 64
B = 48
length_list = [2, 2, 2, 2, 2, 2, 2, 2] # 为了测试方便，长度都设置为1
memory_limit = 18

print(length_list[0] + length_list[1] + length_list[2] + length_list[3])
input_rows = ununiform_init(DP, PP, B, communication, length_list = length_list)
elements_info = generate_schedule_json(input_rows, length_list, memory_limit)

# 找出end最大的元素
max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
max_elem = elements_info[max_elem_id]
print(f"Max end: {max_elem['end']}, elem_id: {max_elem_id}, length_list:{length_list}")
print(f"optimal time: {calculate_optimal_time(DP, PP, B, communication)}")
print(f"optimal memory limit: {get_optimal_memory_limit(DP, PP, communication)}")

if DP == 1:
    # 只需要一个表格
    json_data = single_DP_visualize_schedule(elements_info, input_rows)
else:
    # 需要两个表格
    json_data = visualize_schedule(elements_info, input_rows)
# 保存到文件
save_to_file(json_data, f'greedy_schedule_DP_{DP}_PP_{PP}_B_{B}_C_{communication}_ml_{memory_limit}.json')



################## 类似VP方式的优化调度 ############
# DP = 1
# PP = 4
# communication = 4
# B = 12
# memory_limit = 12

# input_list = m_vp_int(DP, PP, B, communication, memory_limit)
# elements_info = generate_schedule_json(input_list, k = 100)
# json_data = single_DP_visualize_schedule(elements_info, input_list)
# # 保存到文件
# save_to_file(json_data, f"greedy_schedule_vp_DP_{DP}_PP_{PP}_B_{B}_C_{communication}_ml_{memory_limit}.json")
