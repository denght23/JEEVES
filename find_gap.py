from collections import defaultdict, deque
import random
import json
import matplotlib.pyplot as plt
import gurobipy as gp
from gurobipy import GRB
import re
import concurrent.futures
from final_calculate_division import get_best_devision,get_heuristic_division_total,get_heuristic_division_total_concurrent

forward_color_list = ["#87CEEB", "#1E90FF", "#05054F", "#00008B"]
backward_color_list = ["#90EE90", "#228B22", "#006400", "#004d00"]
delay_color = ["#FFB6C1"]  # 浅粉红色


import heapq


# def get_best_devision(PP, M, DP, CM, K, Delay, Memory_limit):
#     model = gp.Model()
#     x = model.addVars(PP, lb=0, name="x")
#     # optimal_num = [get_optimal_num(PP, DP, CM, stage, Delay) for stage in range(PP)]
#     optimal_num = model.addVars(PP, lb=0, vtype=GRB.INTEGER, name="optimal_num")
#     delta_time = model.addVar(lb=0, name="delta_time")
#     actual_num = model.addVars(PP, lb=0, vtype=GRB.INTEGER, name="actual_num")
#     num_delta = model.addVars(PP, lb=0, vtype=GRB.INTEGER, name="num_delta")
#     t = model.addVar(lb=0, name="t")

#     BIG_M = 1e6
#     z = model.addVars(PP, vtype=GRB.BINARY, name="z")

#     # 内存限制
#     for s in range(int(PP / 2)):
#         model.addConstr(actual_num[s] <= optimal_num[s], name=f"actual_num_s{s}_leq_optimal")
#         model.addConstr(actual_num[s] * x[s] <= Memory_limit, name=f"mem_limit_s{s}")
#         f1 = gp.quicksum(3 * x[i] for i in range(s, PP)) + 2 * CM + 2 * Delay
#         f2 = 6 * optimal_num[s]
#         model.addConstr(f1 <= f2, name=f"opt_bound_s{s}")

#     # 添加约束
#     for stage in range(PP):
#         # obj_1
#         obj_1 = gp.quicksum(3 * x[i] for i in range(stage + 1))
#         obj_1 += (M - 1) * 3 * x[stage]
#         if stage >= PP / 2:
#             obj_1 += CM * (DP + 1) + 2 * Delay
#         model.addConstr(t >= obj_1, name=f"MaxConstraint_{stage}_1")

#         # obj_2
#         obj_2 = gp.quicksum(3 * x[i] for i in range(PP))
#         obj_2 += (DP + 1) * CM + 2 * Delay
#         obj_2 += 3 * x[stage] * (M - 1)

#         if stage < PP / 2:
#             # stage_delta only applies when optimal_num[stage] ≠ actual_num[stage]
#             expr_part = model.addVar(lb=-gp.GRB.INFINITY, name=f"expr_part_{stage}")
#             model.addConstr(expr_part == (
#                 (optimal_num[stage] - actual_num[stage] - 1) * 3 * x[stage]
#                 + gp.quicksum(3 * x[i] for i in range(stage, PP))
#                 + (2) * CM
#                 + 2 * Delay
#                 - actual_num[stage] * x[stage] * 3
#             ), name=f"expr_part_def_{stage}")
            
#             # Create a variable for the product
#             product = model.addVar(lb=-gp.GRB.INFINITY, name=f"product_{stage}")
#             model.addConstr(product == num_delta[stage] * expr_part, name=f"product_def_{stage}")
#             model.addConstr((num_delta[stage] + 1) * actual_num[stage] >= M, 
#                        name=f"num_delta_constraint_{stage}")
                
            
            

#             # Use z[stage] to control whether delta_expr is active
#             delta_var = model.addVar(lb=0, name=f"delta_stage_{stage}")
#             model.addConstr(delta_var >= product - BIG_M * (1 - z[stage]), name=f"delta_active_{stage}_1")
#             model.addConstr(delta_var <= product + BIG_M * (1 - z[stage]), name=f"delta_active_{stage}_2")
#             model.addConstr(delta_var <= BIG_M * z[stage], name=f"delta_active_{stage}_upper")

#             # Logical constraint: z[stage] == 1 if optimal != actual
#             # Because Gurobi doesn't support strict equality, simulate it
#             diff = model.addVar(lb=-BIG_M, ub=BIG_M, name=f"diff_{stage}")
#             model.addConstr(diff == optimal_num[stage] - actual_num[stage], name=f"diff_def_{stage}")
#             model.addGenConstrIndicator(z[stage], True, diff >= 1e-5, name=f"z1_if_diff_{stage}")
#             model.addGenConstrIndicator(z[stage], True, diff <= -1e-5, name=f"z1_if_diff_neg_{stage}")

#             model.addGenConstrIndicator(z[stage], False, diff == 0, name=f"z0_if_equal_{stage}")

#             model.addConstr(delta_var <= delta_time, name=f"delta_leq_dt_{stage}")
#             obj_2 += delta_var

#         model.addConstr(t >= obj_2, name=f"MaxConstraint_{stage}_2")

#     # 通信上限
#     obj_cm = gp.quicksum(3 * x[stage] for stage in range(PP))
#     obj_cm += (DP + 1) * CM + (M - 1) * DP * CM + 2 * Delay
#     obj_cm += delta_time
#     model.addConstr(t >= obj_cm, name="MaxConstraint_Communication")

#     # 总数量限制
#     model.addConstr(gp.quicksum(x[i] for i in range(PP)) == K, name="SumConstraint")

#     # 目标函数
#     model.setObjective(t, GRB.MINIMIZE)

#     model.Params.NonConvex = 2
#     model.optimize()

#     x_vals = [x[i].X for i in range(PP)]
#     print("Optimal values of x:", x_vals)
#     t_val = t.X
#     print("Optimal value of t:", t_val)
#     num_vals = [actual_num[i].X for i in range(PP)]
#     print("actual values of num:", num_vals)
#     optimal_num_vals = [optimal_num[i].X for i in range(PP)]
#     print("optimal values of num:", optimal_num_vals)
#     print("delta_time:", delta_time.X)
#     num_delta_vals = [num_delta[i].X for i in range(PP)]
#     print("num_delta values:", num_delta_vals)
#     return x_vals


def get_optimal_memory_limit_without_communication(PP):
    forward_time = 2
    backward_time = 2 * forward_time
    bound = PP * (forward_time + backward_time) - backward_time
    for i in range(100):
        if (forward_time + backward_time) * i > bound:
            return 2 * (i)

def get_optimal_memory_limit(DP, PP, communication, delay):
    forward_time = 2
    backward_time = 2 * forward_time
    bound = PP * (forward_time + backward_time) + (2) * communication + 2 * delay
    if communication * DP > forward_time + backward_time:
        # 如果通信时间大于前向和后向计算时间之和，则内存限制为通信时间
        for i in range(100):
            if communication * DP * i + forward_time >= bound:
                return 2 * (i)
    else:
        # 如果通信时间小于等于前向和后向计算时间之和，则内存限制为前向和后向计算时间之和
        for i in range(100):
            if (forward_time + backward_time) * i >= bound:
                return 2 * (i)

def calculate_optimal_time(DP, PP, B, communication, delay, length_list):
    forward_time = max(length_list)
    backward_time = 2 * forward_time
    time = PP * (forward_time + backward_time) + (DP + 1) * communication + (B - 1) * max(DP * communication, forward_time + backward_time) + 2 * delay
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
           
def get_1F_1B_dependency(PP, name):
    # -------- helper regex matchers --------
    m_fwd         = re.fullmatch(r"(\d+)_([A-Za-z0-9]+)_forward",  name)
    m_bwd         = re.fullmatch(r"(\d+)_([A-Za-z0-9]+)_backward", name)
    m_fwd_comm    = re.fullmatch(r"([A-Za-z0-9]+)_forward_communication",  name)
    m_bwd_comm    = re.fullmatch(r"([A-Za-z0-9]+)_backward_communication", name)

    # ---------- rule-based returns ----------
    if m_fwd:                        # "{pp}_{i}_forward"
        pp, i = int(m_fwd[1]), m_fwd[2]
        if pp == 0:
            return None
        elif pp == PP // 2:
            return f"{i}_forward_communication"
        else:
            return f"{pp - 1}_{i}_forward"

    elif m_bwd:                      # "{pp}_{i}_backward"
        pp, i = int(m_bwd[1]), m_bwd[2]
        if pp == PP - 1:
            return f"{pp}_{i}_forward"
        elif pp == PP // 2 - 1:
            return f"{i}_backward_communication"
        else:
            return f"{pp + 1}_{i}_backward"

    elif m_fwd_comm:                 # "{i}_forward_communication"
        i = m_fwd_comm[1]
        return f"{PP // 2 - 1}_{i}_forward"

    elif m_bwd_comm:                 # "{i}_backward_communication"
        i = m_bwd_comm[1]
        return f"{PP // 2}_{i}_backward"

    return None
def regular_1F_1B(DP, PP, B, communication, delay, forward):
    m_list = []
    for pp in range(PP) :
        m_list.append([])
    m_list.append([])  # 前向通信
    m_list.append([])  # 后向通信
    for pp in range(PP):
        for i in range(PP - pp):
            name = f"{pp}_{i}_forward"
            m_list[pp].append({"id": name, "number": i, "color": forward_color_list[0], "length": forward, "dependency": get_1F_1B_dependency(PP, name)})
        for i in range(B):
            ####1F1B
            ####B
            name = f"{pp}_{i}_backward"
            m_list[pp].append({"id": name, "number": i, "color": backward_color_list[0], "length": 2 * forward, "dependency": get_1F_1B_dependency(PP, name)})
            if i + PP - pp < B:
                name = f"{pp}_{i + PP - pp}_forward"
                m_list[pp].append({"id": name, "number": i + PP - pp, "color": forward_color_list[0], "length": forward, "dependency": get_1F_1B_dependency(PP, name)})
    for mb in range(B):
        name = f"{mb}_forward_communication"
        m_list[-2].append({"id": name, "number": mb, "color": forward_color_list[0], "length": communication * DP + delay, "dependency": get_1F_1B_dependency(PP, name)})
        name = f"{mb}_backward_communication"
        m_list[-1].append({"id": name, "number": mb, "color": backward_color_list[0], "length": communication * DP + delay, "dependency": get_1F_1B_dependency(PP, name)})
    return m_list


            
            
def ununiform_init_with_delay(DP, PP, B, communication, delay, length_list = None):
    #############
    ####DP:communication 
    ###B:一个replica处理的micro batch的数量
    ###communication: 一个micro batch跨数据中心通信的传输时间
    ###delay：一个micro batch 跨数据中心通信的传播时间
    ###length_list:每个pipeline stage前向计算所用的时间，例如一共4个stage，每个stage layer数量相同，length_list可以为【2，2，2，2】
    #############
    list = []
    for pp in range(PP * DP) :
        list.append([])
    list.append([]) #前向delay
    list.append([]) #后向delay
    list.append([])  # 前向通信
    list.append([])  # 后向通信
    
    half_PP = PP // 2
    
    for dp in range(DP):
        for mb in range(B):
            #前向计算
            for pp in range(PP):
                if pp == 0:
                    if mb == 0:
                        dependency = None
                    else:
                        dependency = f"{mb-1}_{dp}_{0}_forward"
                elif pp < half_PP:
                    dependency = f"{mb}_{dp}_{pp - 1}_forward"
                elif pp == half_PP:
                    dependency = f"{mb}_{dp}_forward_delay"
                else:
                    dependency = f"{mb}_{dp}_{pp - 1}_forward"
                name = f"{mb}_{dp}_{pp}_forward"
                list[PP * dp + pp].append({"id": name, "number": mb, "color": forward_color_list[dp % 4], "length": length_list[pp] / 6, "dependency": dependency})
            
            #后向计算
            for pp in reversed(range(PP)):
                if pp == PP - 1:
                    dependency = f"{mb}_{dp}_{PP - 1}_forward"
                elif pp == half_PP - 1:
                    dependency = f"{mb}_{dp}_backward_delay"
                else:
                    dependency = f"{mb}_{dp}_{pp + 1}_backward"
                name = f"{mb}_{dp}_{pp}_backward"
                list[PP * dp + pp].append({"id": name, "number": mb, "color": backward_color_list[dp % 4], "length": 2 * length_list[pp] / 6, "dependency": dependency})
            
            #前向通信
            list[-2].append({"id": f"{mb}_{dp}_forward_communication", 
                             "number": mb, "color": forward_color_list[dp % 4], 
                             "length": communication, 
                             "dependency": f"{mb}_{dp}_{half_PP - 1}_forward"})
            list[-4].append({"id": f"{mb}_{dp}_forward_delay",
                                "number": mb, "color": delay_color[0], 
                                "length": delay, 
                                "dependency": f"{mb}_{dp}_forward_communication"})
            #后向通信
            list[-1].append({"id": f"{mb}_{dp}_backward_communication",
                             "number": mb, "color": backward_color_list[dp % 4],
                             "length": communication,
                             "dependency": f"{mb}_{dp}_{half_PP}_backward"})
            list[-3].append({"id": f"{mb}_{dp}_backward_delay",
                                "number": mb, "color": delay_color[0],
                                "length": delay,
                                "dependency": f"{mb}_{dp}_backward_communication"})
    return list

def generate_schedule_with_sequence(all_rows):
    # 每行元素按照行的顺序来调度，当前row没有操作，memroy不超过上限时才能执行
    elements_info = {}
    # 初始化每行的元数据：当前处理索引和前一元素结束时间
    rows_meta = [{'index': 0, 'prev_end': 0} for _ in all_rows]
    total_elements = sum(len(row) for row in all_rows)
    processed_count = 0

    while processed_count < total_elements:
        progress = False
        for row_idx, row in enumerate(all_rows):
            meta = rows_meta[row_idx]
            # 如果该行已处理完所有元素，跳过
            if meta['index'] >= len(row):
                continue
            elem = row[meta['index']]
            elem_id = elem['id']
            dependency_id = elem.get('dependency')
            
            # 检查依赖是否满足
            dep_end = 0
            if dependency_id is not None:
                if dependency_id not in elements_info:
                    continue  # 依赖未处理，跳过该元素
                dep_end = elements_info[dependency_id]['end']
            
            # 计算开始时间
            start = max(meta['prev_end'], dep_end)
            end = start + elem['length']
            
            # 记录调度信息并更新状态
            elements_info[elem_id] = {
                'start': start,
                'end': end,
                'elem': elem
            }
            meta['prev_end'] = end
            meta['index'] += 1
            processed_count += 1
            progress = True
        
        if not progress:
            raise RuntimeError("调度失败：存在循环依赖或未定义的依赖")
    return elements_info
    

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
                #TODO:这里为了测试注释掉了，实际使用时需要改回来
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
                        if meta['load'] + length_list[row % PP] <= k and not have_backward:
                        # if meta['load']  < k and not have_backward:
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

def get_length_list(memory):
    target_sum = 96
    first_range = range(9, 13)  # 第一个数的取值范围是12到16
    second_range = range(9, 13)  # 第二个数的取值范围是15到16
    
    # 存放所有可能的8个数的组合
    all_possible_sets = []
    
    # 穷举第一个和第二个数的所有组合
    for first_num in first_range:
        for second_num in second_range:
            remaining_sum = target_sum - first_num - second_num  # 剩余6个数的总和
            
            # 求出6个数的均值和余数
            base_value = remaining_sum // 6  # 每个数的基本值
            remainder = remaining_sum % 6    # 余数
            
            # 创建一个初步的6个数列表
            remaining_nums = [base_value] * 6
            
            # 将余数分配给前几个数，保证递增
            for i in range(remainder):
                remaining_nums[i] += 1
            
            # 确保剩余6个数按顺序排列，若不是按顺序，则需要排序
            remaining_nums.sort()
            
            # 现在生成最终的8个数的组合
            possible_set = [first_num, second_num] + remaining_nums
            all_possible_sets.append(possible_set)
    
    return all_possible_sets


# def get_length_list(Memory):
#     ####只考虑前2个stage
#     all_length_list  = [8 * [2]]
#     K_list = [(9, 7), (9, 8), (9, 9), (10, 7), (10, 8), (10, 9), (10, 10)]
#     for pair in K_list:
#         length_1 = int(Memory / pair[0] * 100) / 100
#         length_2 = int(Memory / pair[1] * 100) / 100
#         others = (16 - length_1 - length_2) / 6
#         if length_2 > others:
#             length_2 = (16 - length_1) / 6
#             others = length_2
#         for i in range(6):
#             length_list = [length_1, length_2] + [others] * 6
#         all_length_list.append(length_list)
#     return all_length_list


# 计算每个 length_list 对应的 max_uniform_elem['end']
def process_length_list(length_list, DP, communication, delay, memory_limit, PP, B):
    input_rows = ununiform_init_with_delay(DP, PP, B, communication, delay, length_list=length_list)
    elements_info = generate_schedule_json(input_rows, length_list, memory_limit)
    max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
    max_elem = elements_info[max_elem_id]
    return max_elem['end'], length_list

# 封装的多线程处理函数
def find_min_end_length(DP, communication, delay, memory_limit, PP, B):
    all_length_list = get_length_list(memory_limit)
    
    min_end = float('inf')
    best_length_list = None
    best_5x_end = None
    
    # 使用多线程处理每个 length_list
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_length_list, length_list, DP, communication, delay, memory_limit, PP, B): length_list for length_list in all_length_list}
        
        for future in concurrent.futures.as_completed(futures):
            end_value, length_list = future.result()
            if end_value < min_end:
                min_end = end_value
                best_length_list = length_list
                best_5x_end = 5 * end_value
    
    return best_length_list, best_5x_end
    

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
    

def visualize_schedule(elements_info, all_rows):
    # 第二阶段：初始化JSON数据结构
    json_data = {
        "mainTable": [[{"color": "", "content": ""} for _ in range(400)] for _ in range(4)],
        "mainTable2": [[{"color": "", "content": ""} for _ in range(400)] for _ in range(4)],
        "table1": [[{"color": "", "content": ""} for _ in range(400)]],
        "table2": [[{"color": "", "content": ""} for _ in range(400)]]
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
        
# ##########test DP############
# optimal_list = []
# greedy_list = []
# for DP in range(4, 68, 4):
#     PP = 8
#     communication = 6 / DP
#     B = 48
#     length_list = [2, 2, 2, 2, 2, 2, 2, 2] # 为了测试方便，长度都设置为1
#     memory_limit = get_optimal_memory_limit(DP, PP, communication)
#     input_rows = ununiform_init(DP, PP, B, communication, length_list = length_list)
#     elements_info = generate_schedule_json(input_rows, length_list, memory_limit)
#     max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
#     max_elem = elements_info[max_elem_id]
#     greedy_list.append(max_elem['end'])
#     optimal_list.append(calculate_optimal_time(DP, PP, B, communication, length_list))
    
# plt.figure(figsize=(8, 5), dpi=300)
# ax = plt.gca()
# # 坐标轴样式配置
# plt.xticks(fontsize=14, rotation=45)
# plt.yticks(fontsize=14)

# # 坐标轴边界样式
# ax.spines['top'].set_visible(False)
# ax.spines['right'].set_visible(False)
# ax.spines['left'].set_linewidth(1.5)
# ax.spines['bottom'].set_linewidth(1.5)

# # 网格和范围设置
# plt.grid(axis="y", linewidth=0.8, alpha=0.6)

# # 绘图
# plt.plot(list(range(4, 68, 4)), optimal_list, linewidth=3.5, color='purple', label="optimal")
# plt.plot(list(range(4, 68, 4)), greedy_list, linewidth=3.5, color='blue', label="greedy")
# plt.legend(fontsize=12, loc='best')
# plt.xlabel('DP', fontsize=16, labelpad=10)
# plt.ylabel('Time (ms)', fontsize=16, labelpad=10)

# # 自动调整布局，防止标签被裁剪
# plt.tight_layout(rect=[0.08, 0.05, 0.98, 0.98])
# plt.savefig(f'optimal_vs_greedy_with_various_DP.png', bbox_inches='tight')


##########test bandwidth############
# optimal_list = []
# greedy_list = []
# for Bandwidth in range(100, 1000, 100):
#     DP = 64
#     PP = 8
#     communication = 80 / Bandwidth
#     B = 48
#     length_list = [2, 2, 2, 2, 2, 2, 2, 2] # 为了测试方便，长度都设置为1
#     memory_limit = get_optimal_memory_limit(DP, PP, communication)
#     input_rows = ununiform_init(DP, PP, B, communication, length_list = length_list)
#     elements_info = generate_schedule_json(input_rows, length_list, memory_limit)
#     max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
#     max_elem = elements_info[max_elem_id]
#     greedy_list.append(max_elem['end'])
#     optimal_list.append(calculate_optimal_time(DP, PP, B, communication, length_list))
    
# plt.figure(figsize=(8, 5), dpi=300)
# ax = plt.gca()
# # 坐标轴样式配置
# plt.xticks(fontsize=14, rotation=45)
# plt.yticks(fontsize=14)

# # 坐标轴边界样式
# ax.spines['top'].set_visible(False)
# ax.spines['right'].set_visible(False)
# ax.spines['left'].set_linewidth(1.5)
# ax.spines['bottom'].set_linewidth(1.5)

# # 网格和范围设置
# plt.grid(axis="y", linewidth=0.8, alpha=0.6)


    
# plt.plot(list(range(100, 1000, 100)), optimal_list, linewidth=3.5, color='purple', label="optimal")
# plt.plot(list(range(100, 1000, 100)), greedy_list, linewidth=3.5, color='blue', label="greedy")
# plt.legend(fontsize=12, loc='best')
# plt.xlabel('Bandwidth (Gbps)', fontsize=16, labelpad=10)
# plt.ylabel('Time (ms)', fontsize=16, labelpad=10)

# # 自动调整布局，防止标签被裁剪
# plt.tight_layout(rect=[0.08, 0.05, 0.98, 0.98])
# plt.savefig(f'optimal_vs_greedy_with_various_Bandwidth.png', bbox_inches='tight')


# ##########test PP############
# optimal_list = []
# greedy_list = []
# for PP in range(6, 20, 2):
#     DP = 64
#     communication = 6 / 64
#     B = 48
#     length_list = PP * [2] # 为了测试方便，长度都设置为1
#     memory_limit = get_optimal_memory_limit(DP, PP, communication)
#     input_rows = ununiform_init(DP, PP, B, communication, length_list = length_list)
#     elements_info = generate_schedule_json(input_rows, length_list, memory_limit)
#     max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
#     max_elem = elements_info[max_elem_id]
#     greedy_list.append(max_elem['end'])
#     optimal_list.append(calculate_optimal_time(DP, PP, B, communication, length_list))
    
# plt.figure(figsize=(8, 5), dpi=300)
# ax = plt.gca()
# # 坐标轴样式配置
# plt.xticks(fontsize=14, rotation=45)
# plt.yticks(fontsize=14)

# # 坐标轴边界样式
# ax.spines['top'].set_visible(False)
# ax.spines['right'].set_visible(False)
# ax.spines['left'].set_linewidth(1.5)
# ax.spines['bottom'].set_linewidth(1.5)

# # 网格和范围设置
# plt.grid(axis="y", linewidth=0.8, alpha=0.6)


    
# plt.plot(list(range(6, 20, 2)), optimal_list, linewidth=3.5, color='purple', label="optimal")
# plt.plot(list(range(6, 20, 2)), greedy_list, linewidth=3.5, color='blue', label="greedy")
# plt.legend(fontsize=12, loc='best')
# plt.xlabel('PP', fontsize=16, labelpad=10)
# plt.ylabel('Time (ms)', fontsize=16, labelpad=10)

# # 自动调整布局，防止标签被裁剪
# plt.tight_layout(rect=[0.08, 0.05, 0.98, 0.98])
# plt.savefig(f'optimal_vs_greedy_with_various_PP.png', bbox_inches='tight')

##########test DP############
# PP = 4
# print(get_optimal_memory_limit_without_communication(PP))
# DP = 2
# communication = 6 / DP
# print(get_optimal_memory_limit(DP, PP, communication))
# B = 48
# length_list = PP * [2] # 为了测试方便，长度都设置为1
# memory_limit = get_optimal_memory_limit_without_communication(PP)
# input_rows = ununiform_init(DP, PP, B, communication, length_list = length_list)
# elements_info = generate_schedule_json(input_rows, length_list, memory_limit)
# max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
# max_elem = elements_info[max_elem_id]
# print(max_elem['end'])




##########考虑时延和内存限制############
# optimal_list = []
# greedy_list = []
# uniform_list = []
# # for DP in range(4, 68, 4):
# DP = 2
# PP = 4
# communication = 2 / DP
# B = 7
# delay = 2
# memory_limit = get_optimal_memory_limit_without_communication(PP)
# print(memory_limit)
# length_list, t_val = get_heuristic_division_total_concurrent(PP, B, DP, communication, 16, delay, memory_limit)
# print(length_list, t_val)
# if t_val == None:
#     length_list = PP * [2]  # 为了测试方便，长度都设置为1
# input_rows = ununiform_init_with_delay(DP, PP, B, communication, delay, length_list = length_list)
# elements_info = generate_schedule_json(input_rows, length_list, memory_limit)
# result_json = single_DP_visualize_schedule(elements_info, input_rows, PP)
# save_to_file(result_json, 'JEEVES_PP.json')
# max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
# max_elem = elements_info[max_elem_id]
# greedy_list.append(max_elem['end'])
# optimal_list.append(calculate_optimal_time(DP, PP, B, communication,  delay, length_list))
    
# # for DP in range(4, 68, 4):
# DP = 64
# PP = 8
# communication = 2 / DP
# B = 48
# length_list = PP * [2] # 为了测试方便，长度都设置为1
# memory_limit = get_optimal_memory_limit_without_communication(PP)
# input_rows = ununiform_init_with_delay(DP, PP, B, communication, delay, length_list = length_list)
# elements_info = generate_schedule_json(input_rows, length_list, memory_limit)
# max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
# max_elem = elements_info[max_elem_id]
# uniform_list.append(max_elem['end'])

# print(optimal_list)
# print(greedy_list)
# print(uniform_list)


# DP = 1
# PP = 4
# # communication = 2 / DP ###对应带宽1Tbps
# # communication = 4 / DP 
# # delay = 0.2
# communication = 0
# delay = 1
# # B = 48
# B = 8
# forward = 1
# input_rows = regular_1F_1B(DP, PP, B, communication, delay, forward)
# elements_info = generate_schedule_with_sequence(input_rows)
# max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
# max_elem = elements_info[max_elem_id]
# print(f"regular_1F_1B: {max_elem['end']}")
# result_json = single_DP_visualize_schedule(elements_info, input_rows, PP)
# save_to_file(result_json, f'regular_PP_CM_{communication}_delay_{delay}.json')

    
# plt.figure(figsize=(8, 5), dpi=300)
# ax = plt.gca()
# # 坐标轴样式配置
# plt.xticks(fontsize=14, rotation=45)
# plt.yticks(fontsize=14)

# # 坐标轴边界样式
# ax.spines['top'].set_visible(False)
# ax.spines['right'].set_visible(False)
# ax.spines['left'].set_linewidth(1.5)
# ax.spines['bottom'].set_linewidth(1.5)

# # 网格和范围设置
# plt.grid(axis="y", linewidth=0.8, alpha=0.6)

# # 绘图
# plt.plot(list(range(4, 68, 4)), optimal_list, linewidth=3.5, color='purple', label="optimal")
# plt.plot(list(range(4, 68, 4)), greedy_list, linewidth=3.5, color='blue', label="greedy")
# plt.plot(list(range(4, 68, 4)), uniform_list, linewidth=3.5, color='green', label="uniform")
# plt.legend(fontsize=12, loc='best')
# plt.xlabel('DP', fontsize=16, labelpad=10)
# plt.ylabel('Time (ms)', fontsize=16, labelpad=10)

# # 自动调整布局，防止标签被裁剪
# plt.tight_layout(rect=[0.08, 0.05, 0.98, 0.98])
# plt.savefig(f'optimal_vs_greedy_with_various_DP_ununiform.png', bbox_inches='tight')



#########考虑时延############
# optimal_list = []
# greedy_list = []
# for DP in range(4, 68, 4):
#     PP = 8
#     communication = 6 / DP
#     B = 48
#     delay = 2
#     memory_limit = get_optimal_memory_limit(DP, PP, communication, delay)
#     length_list = PP * [2]
#     input_rows = ununiform_init_with_delay(DP, PP, B, communication, delay, length_list = length_list)
#     elements_info = generate_schedule_json(input_rows, length_list, memory_limit)
#     max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
#     max_elem = elements_info[max_elem_id]
#     greedy_list.append(max_elem['end'])
#     optimal_list.append(calculate_optimal_time(DP, PP, B, communication, delay, length_list))
    
# plt.figure(figsize=(8, 5), dpi=300)
# ax = plt.gca()
# # 坐标轴样式配置
# plt.xticks(fontsize=14, rotation=45)
# plt.yticks(fontsize=14)

# # 坐标轴边界样式
# ax.spines['top'].set_visible(False)
# ax.spines['right'].set_visible(False)
# ax.spines['left'].set_linewidth(1.5)
# ax.spines['bottom'].set_linewidth(1.5)

# # 网格和范围设置
# plt.grid(axis="y", linewidth=0.8, alpha=0.6)

# # 绘图
# plt.plot(list(range(4, 68, 4)), optimal_list, linewidth=3.5, color='purple', label="optimal")
# plt.plot(list(range(4, 68, 4)), greedy_list, linewidth=3.5, color='blue', label="greedy")
# plt.legend(fontsize=12, loc='best')
# plt.xlabel('DP', fontsize=16, labelpad=10)
# plt.ylabel('Time (ms)', fontsize=16, labelpad=10)

# # 自动调整布局，防止标签被裁剪
# plt.tight_layout(rect=[0.08, 0.05, 0.98, 0.98])
# plt.savefig(f'optimal_vs_greedy_with_various_DP_with_delay.png', bbox_inches='tight')

# DP = 64
# PP = 8
# communication = 6 / 64
# B = 48
# delay = 0
# length_list = PP * [2] # 为了测试方便，长度都设置为1
# cal_memory_limit = get_optimal_memory_limit(DP, PP, communication, delay)
# print(cal_memory_limit)
# memory_limit = cal_memory_limit
# input_rows = ununiform_init_with_delay(DP, PP, B, communication, delay, length_list = length_list)
# elements_info = generate_schedule_json(input_rows, length_list, memory_limit)
# max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
# max_elem = elements_info[max_elem_id]
# print(max_elem['end'])
# optimal_time = calculate_optimal_time(DP, PP, B, communication, delay, length_list)
# print(optimal_time)
# data = visualize_schedule(elements_info, input_rows)
# save_to_file(data, 'schedule_with_delay.json')


# # print(get_optimal_memory_limit(1, 8, 0.00, 0.00))
#############################################################################################################################################
#########################################JEVEES_vs_Optimal_vs_Inproved_PP_with_various_Bandwidth.png#########################################
#############################################################################################################################################
JEVEES_list = []
# Optimal_list = []
intra_ununiform_list = []
# intra_ununiform_optimal_list = []
Inproved_PP_list = []
F1B1_list = []
intra_DC = []
# for DP in range(4, 68, 4):
DP = 64
PP = 8
B = 48
# memory_limit = get_optimal_memory_limit_without_communication(PP)
memory_limit = 96
k = 1
delay = 0.1 #####real_delay = (delay / 2) * 10ms
Desire_bandwidth = [0.2,0.3, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0]
for Bandwidth in Desire_bandwidth:
    k = Bandwidth / 1.3
    communication = (1 / DP) / k
    # length_list, t_val = get_heuristic_division_total_concurrent(PP, B, DP, communication, 16, delay, memory_limit)
    # if t_val == None:
    #     length_list = PP * [2]
    # ########## JEEVES & OPtimal ##########
    # input_rows = ununiform_init_with_delay(DP, PP, B, communication, delay, length_list = length_list)
    # elements_info = generate_schedule_json(input_rows, length_list, memory_limit)
    # max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
    # max_elem = elements_info[max_elem_id]
    # JEVEES_list.append(5 * max_elem['end'])
    # # Optimal_list.append(5 * calculate_optimal_time(DP, PP, B, communication, delay, length_list))
    # Optimal_list.append(5 * t_val)
    # print(best_length_list, best_5x_end)
    # length_list, t_val = get_heuristic_division_total_concurrent(PP, B, 1, communication * DP + delay, 16, 0, memory_limit)
    # if t_val == None:
    #     length_list = PP * [2]
    #     print("not_found")
    # uniform_input = ununiform_init_with_delay(1, PP, B, communication * DP + delay, 0, length_list =length_list)
    # uniform_elements_info = generate_schedule_json(uniform_input, length_list, memory_limit)
    # max_uniform_elem_id = max(uniform_elements_info, key=lambda eid: uniform_elements_info[eid]['end'])
    # max_uniform_elem = uniform_elements_info[max_uniform_elem_id]
    # intra_ununiform_list.append(5 * max_uniform_elem['end'])
    # intra_ununiform_optimal_list.append(5 * t_val)
    ########JEEVES##########
    best_length_list, best_5x_end = find_min_end_length(DP, communication, delay, memory_limit, PP, B)
    JEVEES_list.append(best_5x_end)
    ########intra ununiform ##########
    best_length_list, best_5x_end = find_min_end_length(1, communication * DP + delay, 0, memory_limit, PP, B)
    intra_ununiform_list.append(best_5x_end)
    # print(best_length_list, best_5x_end)
    ########## Inproved_1F1B ##########
    length_list = PP * [12]
    improved_input = ununiform_init_with_delay(1, PP, B, communication * DP + delay, 0, length_list = length_list)
    improved_elements_info = generate_schedule_json(improved_input, length_list, memory_limit)
    max_improved_elem_id = max(improved_elements_info, key=lambda eid: improved_elements_info[eid]['end'])
    max_improved_elem = improved_elements_info[max_improved_elem_id]
    Inproved_PP_list.append(5 * max_improved_elem['end'])
    ########## F1B1 ##########
    F1B1_input = regular_1F_1B(DP, PP, B, communication, delay, forward=2)
    F1B1_elements_info = generate_schedule_with_sequence(F1B1_input)
    max_F1B1_elem_id = max(F1B1_elements_info, key=lambda eid: F1B1_elements_info[eid]['end'])
    max_F1B1_elem = F1B1_elements_info[max_F1B1_elem_id]
    F1B1_list.append(5 * max_F1B1_elem['end'])
    
######### intra_DC #########
intra_DC.append(5 * ((PP) * 6 + (B-1) * 6))
intra_DC = intra_DC * len(Desire_bandwidth)

# 保存结果到txt文件
with open("JEVEES_vs_Optimal_vs_Inproved_PP_with_various_Bandwidth.txt", "w") as f:
    f.write("JEVEES_list:\n")
    f.write(",".join(map(str, JEVEES_list)) + "\n")
    f.write("intra_ununiform_list:\n")
    f.write(",".join(map(str, intra_ununiform_list)) + "\n")
    # f.write("intra_ununiform_optimal_list:\n")
    # f.write(",".join(map(str, intra_ununiform_optimal_list)) + "\n")
    f.write("Inproved_PP_list:\n")
    f.write(",".join(map(str, Inproved_PP_list)) + "\n")
    f.write("intra_DC:\n")
    f.write(",".join(map(str, intra_DC)) + "\n")
    f.write("F1B1_list:\n")
    f.write(",".join(map(str, F1B1_list)) + "\n")

plt.figure(figsize=(8, 5), dpi=300)
ax = plt.gca()
# 坐标轴样式配置
plt.xticks(fontsize=18, rotation=45)
plt.yticks(fontsize=18)
plt.ylim(1600, 3400)
# plt.xlim(0, 3.2)
# 坐标轴边界样式
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(1.5)
ax.spines['bottom'].set_linewidth(1.5)
# 网格和范围设置
plt.grid(axis="y", linewidth=0.8, alpha=0.6)
# 绘图
plt.plot(Desire_bandwidth, JEVEES_list, linewidth=3.5, color='purple', label="JEEVES")
# plt.plot(Desire_bandwidth, Optimal_list, linewidth=3.5, color='blue', label="Optimal")
plt.plot(Desire_bandwidth, intra_ununiform_list, linewidth=3.5, color='blue', label="Mem-aware Division")
plt.plot(Desire_bandwidth, Inproved_PP_list, linewidth=3.5, color='green', label="Comm-aware schedule")
plt.plot(Desire_bandwidth, F1B1_list, linewidth=3.5, color='red', label="DAPPLE")
plt.plot(Desire_bandwidth, intra_DC, linewidth=3.5, color='orange', linestyle='--', label="Intra DC")
plt.legend(fontsize=18, loc='best')
plt.xlabel('Bandwidth (Tbps)', fontsize=18, labelpad=10)
plt.ylabel('Time (ms)', fontsize=18, labelpad=10)
# 自动调整布局，防止标签被裁剪
plt.tight_layout(rect=[0.08, 0.05, 0.98, 0.98])
plt.savefig(f'JEVEES_vs_Optimal_vs_Inproved_PP_with_various_Bandwidth.png', bbox_inches='tight')
plt.savefig(f'JEVEES_vs_Optimal_vs_Inproved_PP_with_various_Bandwidth.pdf', bbox_inches='tight')



############################################################################################################################################
########################################JEVEES_vs_Optimal_vs_Inproved_PP_with_various_delay.png#########################################
############################################################################################################################################

JEVEES_list = []
# Optimal_list = []
intra_ununiform_list = []
# intra_ununiform_optimal_list = []
Inproved_PP_list = []
F1B1_list = []
intra_DC = []
# for DP in range(4, 68, 4):
DP = 64
PP = 8
B = 48
# memory_limit = get_optimal_memory_limit_without_communication(PP)
memory_limit = 96
Bandwidth = 1
k = Bandwidth / 1.3
communication = (1 / DP) / k
# delay = 0.1 #####real_delay = (delay / 2) * 10ms
Desire_real_delay = [0.1, 1, 5, 10, 20]
for real_delay in Desire_real_delay:
    delay = (real_delay / 10) * 2
    # length_list, t_val = get_heuristic_division_total_concurrent(PP, B, DP, communication, 16, delay, memory_limit)
    # if t_val == None:
    #     length_list = PP * [2]
    # print(length_list, t_val)
    # ########## JEEVES & OPtimal ##########
    # input_rows = ununiform_init_with_delay(DP, PP, B, communication, delay, length_list = length_list)
    # elements_info = generate_schedule_json(input_rows, length_list, memory_limit)
    # max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
    # max_elem = elements_info[max_elem_id]
    # JEVEES_list.append(5 * max_elem['end'])
    # Optimal_list.append(5 * calculate_optimal_time(DP, PP, B, communication, delay, length_list))
    # Optimal_list.append(5 * t_val)
    ########## uniform ##########
    ########JEEVES##########
    best_length_list, best_5x_end = find_min_end_length(DP, communication, delay, memory_limit, PP, B)
    JEVEES_list.append(best_5x_end)
    ##########intra ununiform ##########
    best_length_list, best_5x_end = find_min_end_length(1, communication * DP + delay, 0, memory_limit, PP, B)
    intra_ununiform_list.append(best_5x_end)
    # length_list, t_val = get_heuristic_division_total_concurrent(PP, B, 1, communication * DP + delay, 16, 0, memory_limit)
    # if t_val == None:
    #     length_list = PP * [2]
    #     print("not_found")
    # uniform_input = ununiform_init_with_delay(1, PP, B, communication * DP + delay, 0, length_list =length_list)
    # uniform_elements_info = generate_schedule_json(uniform_input, length_list, memory_limit)
    # max_uniform_elem_id = max(uniform_elements_info, key=lambda eid: uniform_elements_info[eid]['end'])
    # max_uniform_elem = uniform_elements_info[max_uniform_elem_id]
    # intra_ununiform_list.append(5 * max_uniform_elem['end'])
    # intra_ununiform_optimal_list.append(5 * t_val)
    ########## Inproved_1F1B ##########
    length_list = PP * [12]
    improved_input = ununiform_init_with_delay(1, PP, B, communication * DP + delay, 0, length_list = length_list)
    improved_elements_info = generate_schedule_json(improved_input, length_list, memory_limit)
    max_improved_elem_id = max(improved_elements_info, key=lambda eid: improved_elements_info[eid]['end'])
    max_improved_elem = improved_elements_info[max_improved_elem_id]
    Inproved_PP_list.append(5 * max_improved_elem['end'])
    ########## F1B1 ##########
    F1B1_input = regular_1F_1B(DP, PP, B, communication, delay, forward=2)
    F1B1_elements_info = generate_schedule_with_sequence(F1B1_input)
    max_F1B1_elem_id = max(F1B1_elements_info, key=lambda eid: F1B1_elements_info[eid]['end'])
    max_F1B1_elem = F1B1_elements_info[max_F1B1_elem_id]
    F1B1_list.append(5 * max_F1B1_elem['end'])
    
######### intra_DC #########
intra_DC.append(5 * ((PP) * 6 + (B-1) * 6))
intra_DC = intra_DC * len(Desire_real_delay)

# 保存结果到txt文件
with open("JEVEES_vs_Optimal_vs_Inproved_PP_with_various_Delay.txt", "w") as f:
    f.write("JEVEES_list:\n")
    f.write(",".join(map(str, JEVEES_list)) + "\n")
    # f.write("Optimal_list:\n")
    # f.write(",".join(map(str, Optimal_list)) + "\n")
    f.write("intra_ununiform_list:\n")
    f.write(",".join(map(str, intra_ununiform_list)) + "\n")
    # f.write("intra_ununiform_optimal_list:\n")
    # f.write(",".join(map(str, intra_ununiform_optimal_list)) + "\n")
    f.write("Inproved_PP_list:\n")
    f.write(",".join(map(str, Inproved_PP_list)) + "\n")
    f.write("intra_DC:\n")
    f.write(",".join(map(str, intra_DC)) + "\n")
    f.write("F1B1_list:\n")
    f.write(",".join(map(str, F1B1_list)) + "\n")

plt.figure(figsize=(8, 5), dpi=300)
ax = plt.gca()
# 坐标轴样式配置
plt.xticks(fontsize=18, rotation=45)
plt.yticks(fontsize=18)
plt.ylim(1600, 3000)
# plt.xlim(0, 3.2)
# 坐标轴边界样式
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(1.5)
ax.spines['bottom'].set_linewidth(1.5)
# 网格和范围设置
plt.grid(axis="y", linewidth=0.8, alpha=0.6)
# 绘图
plt.plot(Desire_real_delay, JEVEES_list, linewidth=3.5, color='purple', label="JEEVES")
plt.plot(Desire_real_delay, intra_ununiform_list, linewidth=3.5, color='blue', label="Mem-aware Division")
plt.plot(Desire_real_delay, Inproved_PP_list, linewidth=3.5, color='green', label="Comm-aware schedule")
plt.plot(Desire_real_delay, F1B1_list, linewidth=3.5, color='red', label="DAPPLE")
plt.plot(Desire_real_delay, intra_DC, linewidth=3.5, color='orange', linestyle='--', label="Intra DC")
plt.legend(fontsize=18, loc='best')
plt.xlabel('Latency (ms)', fontsize=18, labelpad=10)
plt.ylabel('Time (ms)', fontsize=18, labelpad=10)
# 自动调整布局，防止标签被裁剪
plt.tight_layout(rect=[0.08, 0.05, 0.98, 0.98])
plt.savefig(f'JEVEES_vs_Optimal_vs_Inproved_PP_with_various_Delay.png', bbox_inches='tight')
plt.savefig(f'JEVEES_vs_Optimal_vs_Inproved_PP_with_various_Delay.pdf', bbox_inches='tight')


##########
#TODO:
# JEEVES:JEEVES方法
# Inproved_PP：优化调度，均匀layer分配，replica之间竞争
# intra_ununiform_list：优化调度，非均匀layer分配，replica之间竞争
##########


# #############################################################################################################################################
# #########################################JEVEES_vs_Optimal_vs_Inproved_PP_with_various_memory#########################################
# #############################################################################################################################################
JEVEES_list = []
Optimal_list = []
Inproved_PP_list = []
intra_ununiform_list = []
# intra_ununiform_optimal_list = []
# uniform_JEVEES_list = []
intra_DC = []
F1B1_list = []
# for DP in range(4, 68, 4):
DP = 64
PP = 8
B = 48
memory_limit = get_optimal_memory_limit_without_communication(PP)
Bandwidth = 1
k = Bandwidth / 1.3
communication = (1 / DP) / k
delay = 1
# delay = 0.1 #####real_delay = (delay / 2) * 10ms
Memory_limit_list = [96, 100, 104, 108, 112, 116, 120, 124] ###通过layer计数
show_Memory_limit_list = [68, 71, 74, 77, 79, 82, 85, 88] ####GB
for memory_limit in Memory_limit_list:
    
    # length_list, t_val = get_heuristic_division_total_concurrent(PP, B, DP, communication, 16, delay, memory_limit)
    # if t_val == None:
    #     length_list = PP * [2]
    # print(length_list, t_val)
    # ########## JEEVES & OPtimal ##########
    # input_rows = ununiform_init_with_delay(DP, PP, B, communication, delay, length_list = length_list)
    # elements_info = generate_schedule_json(input_rows, length_list, memory_limit)
    # max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
    # max_elem = elements_info[max_elem_id]
    # JEVEES_list.append(5 * max_elem['end'])
    # # Optimal_list.append(5 * calculate_optimal_time(DP, PP, B, communication, delay, length_list))
    # Optimal_list.append(5 * t_val)
    
    ########JEEVES##########
    best_length_list, best_5x_end = find_min_end_length(DP, communication, delay, memory_limit, PP, B)
    JEVEES_list.append(best_5x_end)
    print(best_length_list, best_5x_end)
    ########## Inproved_1F1B ##########
    length_list = PP * [12]
    improved_input = ununiform_init_with_delay(1, PP, B, communication * DP + delay, 0, length_list = length_list)
    improved_elements_info = generate_schedule_json(improved_input, length_list, memory_limit)
    max_improved_elem_id = max(improved_elements_info, key=lambda eid: improved_elements_info[eid]['end'])
    max_improved_elem = improved_elements_info[max_improved_elem_id]
    Inproved_PP_list.append(5 * max_improved_elem['end'])
    ##########intra ununiform ##########
    best_length_list, best_5x_end = find_min_end_length(1, communication * DP + delay, 0, memory_limit, PP, B)
    intra_ununiform_list.append(best_5x_end)
    print(best_length_list, best_5x_end)
    
    # length_list, t_val = get_heuristic_division_total_concurrent(PP, B, 1, communication * DP + delay, 16, 0, memory_limit)
    # if t_val == None:
    #     length_list = PP * [2]
    #     print("not_found")
    # uniform_input = ununiform_init_with_delay(1, PP, B, communication * DP + delay, 0, length_list =length_list)
    # uniform_elements_info = generate_schedule_json(uniform_input, length_list, memory_limit)
    # max_uniform_elem_id = max(uniform_elements_info, key=lambda eid: uniform_elements_info[eid]['end'])
    # max_uniform_elem = uniform_elements_info[max_uniform_elem_id]
    # intra_ununiform_list.append(5 * max_uniform_elem['end'])
    # intra_ununiform_optimal_list.append(5 * t_val)
    # ##########uniform_JEVEES ##########
    # length_list = PP * [2]
    # uniform_input = ununiform_init_with_delay(DP, PP, B, communication, delay, length_list = length_list)
    # uniform_elements_info = generate_schedule_json(uniform_input, length_list, memory_limit)
    # max_uniform_elem_id = max(uniform_elements_info, key=lambda eid: uniform_elements_info[eid]['end'])
    # max_uniform_elem = uniform_elements_info[max_uniform_elem_id]
    # uniform_JEVEES_list.append(5 * max_uniform_elem['end'])
    ########## F1B1 ##########
    F1B1_input = regular_1F_1B(DP, PP, B, communication, delay, forward=2)
    F1B1_elements_info = generate_schedule_with_sequence(F1B1_input)
    max_F1B1_elem_id = max(F1B1_elements_info, key=lambda eid: F1B1_elements_info[eid]['end'])
    max_F1B1_elem = F1B1_elements_info[max_F1B1_elem_id]
    F1B1_list.append(5 * max_F1B1_elem['end'])
    
    
######### intra_DC #########
intra_DC.append(5 * ((PP) * 6 + (B-1) * 6))
intra_DC = intra_DC * len(Memory_limit_list)

# 保存结果到txt文件
with open("JEVEES_vs_Optimal_vs_Inproved_PP_with_various_memory.txt", "w") as f:
    f.write("JEVEES_list:\n")
    f.write(",".join(map(str, JEVEES_list)) + "\n")
    f.write("Optimal_list:\n")
    f.write(",".join(map(str, Optimal_list)) + "\n")
    f.write("Inproved_PP_list:\n")
    f.write(",".join(map(str, Inproved_PP_list)) + "\n")
    f.write("intra_DC:\n")
    f.write(",".join(map(str, intra_DC)) + "\n")
    f.write("intra_ununiform_list:\n")
    f.write(",".join(map(str, intra_ununiform_list)) + "\n")
    # f.write("intra_ununiform_optimal_list:\n")
    # f.write(",".join(map(str, intra_ununiform_optimal_list)) + "\n")
    f.write("F1B1_list:\n")
    f.write(",".join(map(str, F1B1_list)) + "\n")
    

plt.figure(figsize=(8, 5), dpi=300)
ax = plt.gca()
# 坐标轴样式配置
plt.yticks(fontsize=18)
plt.ylim(1500, 2300)
# plt.xlim(0, 3.2)
plt.xticks(show_Memory_limit_list, [str(x) for x in show_Memory_limit_list], fontsize=18, rotation=45)

# 坐标轴边界样式
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(1.5)
ax.spines['bottom'].set_linewidth(1.5)
# 网格和范围设置
plt.grid(axis="y", linewidth=0.8, alpha=0.6)
# 绘图
plt.plot(show_Memory_limit_list, JEVEES_list, linewidth=3.5, color='purple', label="JEEVES")
# plt.plot(Desire_bandwidth, Optimal_list, linewidth=3.5, color='blue', label="Optimal")
plt.plot(show_Memory_limit_list, intra_ununiform_list, linewidth=3.5, color='blue', label="Mem-aware Division")
plt.plot(show_Memory_limit_list, Inproved_PP_list, linewidth=3.5, color='green', label="Comm-aware schedule")
plt.plot(show_Memory_limit_list, F1B1_list, linewidth=3.5, color='red', label="DAPPLE")
plt.plot(show_Memory_limit_list, intra_DC, linewidth=3.5, color='orange', linestyle='--', label="Intra DC")
plt.legend(fontsize=18, loc='best')
plt.xlabel('Peak Memory constraint (GB)', fontsize=18, labelpad=10)
plt.ylabel('Time (ms)', fontsize=18, labelpad=10)
# 自动调整布局，防止标签被裁剪
plt.tight_layout(rect=[0.08, 0.05, 0.98, 0.98])
plt.savefig(f'JEVEES_vs_Optimal_vs_Inproved_PP_with_various_Memory.png', bbox_inches='tight')
plt.savefig(f'JEVEES_vs_Optimal_vs_Inproved_PP_with_various_Memory.pdf', bbox_inches='tight')



# # #############################################################################################################################################
# # # #########################################debug_test#########################################
# # # #############################################################################################################################################
# # print(intra_ununiform_list)
# # print(intra_ununiform_optimal_list)
# DP = 64
# PP = 8
# B = 48
# memory_limit = 108
# Bandwidth = 1
# k = Bandwidth / 1.3 
# communication = (1 / DP) / k
# print(communication)
# delay = 1
# # length_list, t_val = get_heuristic_division_total_concurrent(PP, B, DP, communication, 16, delay, memory_limit)
# # print(length_list, t_val)
# # length_list = [1.76, 2.0, 2.0370370370370368, 2.0370370370370368, 2.0370370370370368, 2.0370370370370368, 2.037037037037037, 2.037037037037037]
# # length_list = [1.5, 1.5, 2.1666666666666665, 2.1666666666666665, 2.1666666666666665, 2.1666666666666665, 2.1666666666666665, 2.1666666666666665]
# length_list = 8 * [12]
# # length_list = 8*[2]
# # if t_val == None:
# #     length_list = PP * [2]
# #     print("not_found")
# # print(length_list, 5 * t_val)
# # print(length_list)
# # uniform_input = ununiform_init_with_delay(DP, PP, B, communication, delay, length_list =length_list)
# uniform_input = ununiform_init_with_delay(1, PP, B, communication * DP + delay, 0, length_list =length_list)
# uniform_elements_info = generate_schedule_json(uniform_input, length_list, memory_limit)
# result_json = single_DP_visualize_schedule(uniform_elements_info, uniform_input, PP)
# save_to_file(result_json, 'JEEVES_PP_intra_Memory_aware_division.json')
# max_uniform_elem_id = max(uniform_elements_info, key=lambda eid: uniform_elements_info[eid]['end'])
# max_uniform_elem = uniform_elements_info[max_uniform_elem_id]
# print(5 * max_uniform_elem['end'])
# # best_length_list, best_5x_end = find_min_end_length(1, communication * DP + delay, 0, memory_limit, PP, B)
# # print(best_length_list, best_5x_end)
# # best_length_list, best_5x_end = find_min_end_length(DP, communication, delay, memory_limit, PP, B)
# # print(best_length_list, best_5x_end)

# # # 1938
# # # # memory_limit = 20
# # # # Bandwidth = 1.3
# # # # k = Bandwidth / 1.3
# # # # communication = (1 / DP) / k
# # # # # delay = 0.1 #####real_delay = (delay / 2) * 10ms
# # # # delay = 1
# # # # # length_list, t_val = get_heuristic_division_total_concurrent(PP, B, DP, communication, 16, delay, memory_limit)
# # # # # if t_val == None:
# # # # #     length_list = PP * [2]
# # # # # print(length_list, t_val)
# # # # ########## JEEVES & OPtimal ##########
# # # # # input_rows = regular_1F_1B(1, PP, B, communication * DP + delay, 0, forward=2)
# # # # # elements_info = generate_schedule_with_sequence(input_rows)
# # # # # max_F1B1_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
# # # # # max_F1B1_elem = elements_info[max_F1B1_elem_id]
# # # # length_list = PP * [1]
# # # # input_rows = ununiform_init_with_delay(1, PP, B, communication * DP, delay, length_list = length_list)
# # # # elements_info = generate_schedule_json(input_rows, length_list, memory_limit)
# # # # max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
# # # # max_elem = elements_info[max_elem_id]
# # # # result_json = single_DP_visualize_schedule(elements_info, input_rows, PP)
# # # # save_to_file(result_json, 'JEEVES_PP_no_memory_cons.json')
# # # # # save_to_file(result_json, 'JEEVES_PP.json')
# # # # # save_to_file(result_json, 'JEEVES_PP_backward_advanced.json')

# # 12, 16
# # 15, 16


