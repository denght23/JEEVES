import json
import re
import heapq
import matplotlib.pyplot as plt


forward_color_list = ["#87CEEB", "#1E90FF", "#05054F", "#00008B"]
backward_color_list = ["#90EE90", "#228B22", "#006400", "#004d00"]
delay_color = ["#FFB6C1"]  # 浅粉红色
def interleave_ops(forward_list, backward_list, switch_id):
    """
    Merge two operation lists based on the interleaving rule.

    Args:
        forward_list (list): List of forward operations (each with a unique 'id' field).
        backward_list (list): List of backward operations (each with a unique 'id' field).
        switch_id: The ID in the forward list where interleaving with the backward list starts.

    Returns:
        list: Merged list of operations.
    """
    merged = []
    f_idx = 0
    b_idx = 0
    interleave = False

    # Step 1: Process forward ops until switch_id
    while f_idx < len(forward_list):
        f_op = forward_list[f_idx]
        merged.append(f_op)
        f_idx += 1

        if f_op['id'] == switch_id:
            interleave = True
            break

    # Step 2: Interleave forward and backward ops
    while interleave and f_idx < len(forward_list) and b_idx < len(backward_list):
        merged.append(backward_list[b_idx])
        b_idx += 1
        merged.append(forward_list[f_idx])
        f_idx += 1

    # Step 3: Append remaining ops from whichever list is not empty
    while f_idx < len(forward_list):
        merged.append(forward_list[f_idx])
        f_idx += 1
    while b_idx < len(backward_list):
        merged.append(backward_list[b_idx])
        b_idx += 1

    return merged



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
        m_list[-2].append({"id": name, "number": mb, "color": forward_color_list[0], "length": communication+ delay, "dependency": get_1F_1B_dependency(PP, name)})
        name = f"{mb}_backward_communication"
        m_list[-1].append({"id": name, "number": mb, "color": backward_color_list[0], "length": communication + delay, "dependency": get_1F_1B_dependency(PP, name)})
    return m_list

vp_interleave_list  = [
    f"PP{0}_VP{1}_mb{7}_forward",
    f"PP{1}_VP{1}_mb{6}_forward",
    f"PP{2}_VP{1}_mb{5}_forward",
    f"PP{3}_VP{1}_mb{4}_forward",
    f"PP{4}_VP{1}_mb{3}_forward",
    f"PP{5}_VP{1}_mb{2}_forward",
    f"PP{6}_VP{1}_mb{1}_forward",
    f"PP{7}_VP{1}_mb{0}_forward",]
# vp_interleave_list  = [
#     f"PP{0}_VP{1}_mb{7}_forward",
#     f"PP{1}_VP{1}_mb{7}_forward",
#     f"PP{2}_VP{1}_mb{7}_forward",
#     f"PP{3}_VP{1}_mb{7}_forward",
#     f"PP{4}_VP{1}_mb{6}_forward",
#     f"PP{5}_VP{1}_mb{5}_forward",
#     f"PP{6}_VP{1}_mb{2}_forward",
#     f"PP{7}_VP{1}_mb{0}_forward",]
def regular_vp_2_PP_8(B, communication, delay):
    PP = 8
    vp_size = 2
    group_size = 8
    forward_time = 1
    backward_time = 2 * forward_time
    dependencies = {}
    forward_list = []
    backward_list = []
    m_list = []
    for i in range(8):
        m_list.append([])
        forward_list.append([])
        backward_list.append([])
    for i in range(2):
        m_list.append([])
    for pp in range(PP):
        for mb_base in range(0, B, group_size):
            for vp in range(vp_size):
                for i in range(group_size):
                    mb = mb_base + i
                    name = f"PP{pp}_VP{vp}_mb{mb}_forward"
                    if pp == 0:
                        if vp == 0:
                            dependency = None
                        else:
                            dependency = f"VP{vp}_mb{mb}_forward_communication_tail"
                    elif pp == PP // 2:
                        dependency = f"VP{vp}_mb{mb}_forward_communication"
                    else:
                        dependency = f"PP{pp - 1}_VP{vp}_mb{mb}_forward"
                    forward_list[pp].append({"id": name, "number": mb, "color": forward_color_list[vp], "length": forward_time, "dependency": dependency})
    for pp in range(PP):
        for mb_base in range(0, B, group_size):
            for vp in range(vp_size):
                for i in range(group_size):
                    mb = mb_base + i
                    name = f"PP{pp}_VP{vp}_mb{mb}_backward"
                    if pp == PP - 1:
                        if vp == 0:
                            dependency = f"PP{PP-1}_VP{1}_mb{mb}_forward"
                        else:
                            dependency = f"VP{vp}_mb{mb}_backward_communication_tail"
                    elif pp == PP // 2 -1:
                        dependency = f"VP{vp}_mb{mb}_backward_communication"
                    else:
                        dependency = f"PP{pp + 1}_VP{vp}_mb{mb}_backward"
                    backward_list[pp].append({"id": name, "number": mb, "color": backward_color_list[vp], "length": backward_time, "dependency": dependency})
    for mb_base in range(0, B, group_size):
        for vp in range(vp_size):
            for i in range(group_size):
                mb = mb_base + i
                name = f"VP{vp}_mb{mb}_forward_communication"
                dependency = f"PP{PP // 2 - 1}_VP{vp}_mb{mb}_forward"
                m_list[-2].append({"id": name, "number": mb, "color": forward_color_list[vp], "length": communication + delay, "dependency": dependency})
                name = f"VP{vp}_mb{mb}_backward_communication"
                dependency = f"PP{PP // 2}_VP{vp}_mb{mb}_backward"
                m_list[-1].append({"id": name, "number": mb, "color": backward_color_list[vp], "length": communication + delay, "dependency": dependency})
    for mb_base in range(0, B, group_size):
        for i in range(group_size):
            mb = mb_base + i
            name = f"VP{1}_mb{mb}_forward_communication_tail"
            dependency = f"PP{PP - 1}_VP{0}_mb{mb}_forward"
            m_list[-2].append({"id": name, "number": mb, "color": forward_color_list[3], "length": communication + delay, "dependency": dependency})
            name = f"VP{1}_mb{mb}_backward_communication_tail"
            dependency = f"PP{0}_VP{0}_mb{mb}_backward"
            m_list[-1].append({"id": name, "number": mb, "color": backward_color_list[3], "length": communication + delay, "dependency": dependency})
            
    for pp in range(PP):
        m_list[pp] = interleave_ops(forward_list[pp], backward_list[pp], vp_interleave_list[pp])
    return m_list

dual_pipe_dict = {
    "1":"f_a",
    "2":"f_b",
    "3":"b_a",
    "4":"b_b"
}
dualpipe_parttern = [
    []
]
def dualpipe_pattern(PP,B):
    dual_pipe_B = B // 2
    parttern_list = []
    for pp in range(PP):
        parttern_list.append([])
    parttern_list[0] = [1, 1, 1, 1, 2, 4, 2, 4, 2, 4, 2, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3]
    parttern_list[1] = [1, 1, 1, 2, 1, 2, 4, 2, 4, 2, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3]
    parttern_list[2] = [1, 1, 2, 1, 2, 1, 2, 4, 2, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3]
    parttern_list[3] = [1, 2, 1, 2, 1, 2, 1, 2, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3]
    last_parttern = [
        [3, 3, 3],
        [3, 3],
        [3],
        []
    ]
    
    k = (dual_pipe_B - 8) // 8
    stage_1 = [1, 3, 1, 3, 1, 3, 1, 2, 4, 2, 4, 2, 4, 2, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3]
    stage_2 = [1, 3, 1, 3, 1, 2, 1, 2, 4, 2, 4, 2, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3]
    stage_3 = [1, 3, 1, 2, 1, 2, 1, 2, 4, 2, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3]
    stage_4 = [1, 2, 1, 2, 1, 2, 1, 2, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3]
    for i in range(k):
        parttern_list[0].extend(stage_1)
        parttern_list[1].extend(stage_2)
        parttern_list[2].extend(stage_3)
        parttern_list[3].extend(stage_4)
    parttern_list[0].extend(last_parttern[0])
    parttern_list[1].extend(last_parttern[1])
    parttern_list[2].extend(last_parttern[2])
    parttern_list[3].extend(last_parttern[3])
    # 生成第7个pattern_list，使其与第0个互换1<->2, 3<->4
    mapping = {1: 2, 2: 1, 3: 4, 4: 3}
    parttern_list[7] = [mapping.get(x, x) for x in parttern_list[0]]
    parttern_list[6] = [mapping.get(x, x) for x in parttern_list[1]]
    parttern_list[5] = [mapping.get(x, x) for x in parttern_list[2]]
    parttern_list[4] = [mapping.get(x, x) for x in parttern_list[3]]
    return parttern_list

def regular_dualPipe_2_PP_8(PP, B, parttern_list, communication, delay):
    dual_pipe_B = B // 2
    forward_time = 2
    backward_time = 2 * forward_time
    m_list = []
    for i in range(PP):
        m_list.append([])
        forward_a_idx = 0
        forward_b_idx = 0
        backward_a_idx = 0
        backward_b_idx = 0
        for op_id in parttern_list[i]:
            if op_id == 1:
                forward_a_idx += 1
                name = f"PP{i}_mb{forward_a_idx}_forward_a"
                m_list[i].append({"id": name, "number": forward_a_idx, "color": forward_color_list[0], "length": forward_time, "dependency": None})
                forward_a_idx += 1
                name = f"PP{i}_mb{forward_a_idx}_forward_a"
                m_list[i].append({"id": name, "number": forward_a_idx, "color": forward_color_list[0], "length": forward_time, "dependency": None})
            elif op_id == 2:
                forward_b_idx += 1
                name = f"PP{i}_mb{forward_b_idx}_forward_b"
                m_list[i].append({"id": name, "number": forward_b_idx, "color": forward_color_list[1], "length": forward_time, "dependency": None})
                forward_b_idx += 1
                name = f"PP{i}_mb{forward_b_idx}_forward_b"
                m_list[i].append({"id": name, "number": forward_b_idx, "color": forward_color_list[1], "length": forward_time, "dependency": None})
            elif op_id == 3:
                backward_a_idx += 1
                name = f"PP{i}_mb{backward_a_idx}_backward_a"
                m_list[i].append({"id": name, "number": backward_a_idx, "color": backward_color_list[0], "length": backward_time, "dependency": None})
            elif op_id == 4:
                backward_b_idx += 1
                name = f"PP{i}_mb{backward_b_idx}_backward_b"
                m_list[i].append({"id": name, "number": backward_b_idx, "color": backward_color_list[1], "length": backward_time, "dependency": None})
    m_list.append([]) 
    # 先填充 forward_a_communication 8 个，再填充 backward_b_communication 8 个，循环直到各自填满 dual_pipe_B 个
    comm_count = dual_pipe_B // 8
    for block in range(comm_count):
        # forward_a_communication
        for i in range(block * 8, (block + 1) * 8):
            name = f"mb{i + 1}_forward_a_communication"
            m_list[-1].append({"id": name, "number": i + 1, "color": forward_color_list[0], "length": communication + delay, "dependency": f"PP{3}_mb{i + 1}_forward_a"})
        # backward_b_communication
        for i in range(block * 8, (block + 1) * 8):
            name = f"mb{i + 1}_backward_b_communication"
            m_list[-1].append({"id": name, "number": i + 1, "color": backward_color_list[1], "length": communication + delay, "dependency": f"PP{3}_mb{i + 1}_backward_b"})
    m_list.append([])  # 添加空行以匹配8行的结构
    # 填充最后的 forward_b_communication 和 backward_a_communication
    for block in range(comm_count):
        for i in range(block * 8, (block + 1) * 8):
            # forward_b_communication
            name = f"mb{i + 1}_forward_b_communication"
            m_list[-1].append({"id": name, "number": i + 1, "color": forward_color_list[1], "length": communication + delay, "dependency": f"PP{4}_mb{i + 1}_forward_b"})
            # backward_a_communication
        for i in range(block * 8, (block + 1) * 8):
            name = f"mb{i + 1}_backward_a_communication"
            m_list[-1].append({"id": name, "number": i + 1, "color": backward_color_list[0], "length": communication + delay, "dependency":f"PP{4}_mb{i + 1}_backward_a"})
    ####指定dependency
    for pp in range(PP):
        for elem in m_list[pp]:
            elem_id = elem['id']
            # 这里根据你的需求自定义依赖关系
            # 示例：如果是forward_a，则依赖前一个forward_a，否则依赖前一个backward_a
            if 'forward_a' in elem_id:
                idx = elem['number']
                if pp == 0:
                    elem['dependency'] = None
                elif pp == 4:
                    elem['dependency'] = f"mb{idx}_forward_a_communication"
                else:
                    elem['dependency'] = f"PP{pp-1}_mb{idx}_forward_a"
            elif 'forward_b' in elem_id:
                idx = elem['number']
                if pp == 7:
                    elem['dependency'] = None
                elif pp == 3:
                    elem['dependency'] = f"mb{idx}_forward_b_communication"
                else:
                    elem['dependency'] = f"PP{pp+1}_mb{idx}_forward_b"
            elif 'backward_a' in elem_id:
                idx = elem['number']
                if pp == 7:
                    elem['dependency'] = f"PP{pp}_mb{idx}_forward_a"
                elif pp == 3:
                    elem['dependency'] = f"mb{idx}_backward_a_communication"
                else:
                    elem['dependency'] = f"PP{pp+1}_mb{idx}_backward_a"
            elif 'backward_b' in elem_id:
                idx = elem['number']
                if pp == 0:
                    elem['dependency'] = f"PP{pp}_mb{idx}_forward_b"
                elif pp == 4:
                    elem['dependency'] = f"mb{idx}_backward_b_communication"
                else:
                    elem['dependency'] = f"PP{pp-1}_mb{idx}_backward_b"
    return m_list
                    
                    
    
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
            # if elem_id == "PP0_mb1_forward_a":
            #     print(elem_id)
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
            # break
            raise RuntimeError("调度失败：存在循环依赖或未定义的依赖")
    return elements_info

def generate_schedule_json(all_rows):
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
    for row_index, row in enumerate(all_rows):
        first_elem_id = row[0]['id']
        if dependency_counters[first_elem_id] == 0:
            meta = rows_meta[row_index]
            start_time = 0
            end_time = elements[first_elem_id]['length']
            elements_info[first_elem_id] = {
                'start': start_time,
                'end': end_time,
                'elem': elements[first_elem_id]
            }
            heapq.heappush(event_queue, (end_time, first_elem_id))
            meta['busy_until'] = end_time
            meta['current_id'] = first_elem_id

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
            processed_elements.add(elem_id)
                
            for row in rows_meta:
                meta = rows_meta[row]
                if meta['busy_until'] > current_time:
                    continue  # 行忙碌中
                if meta['current_id'] is not None:
                    if meta['current_id'] not in processed_elements:
                        continue

                if row >= len(rows_meta) - 2:
                    for i in range(len(all_rows[row])):
                        elem_id = all_rows[row][i]['id']
                        if elem_id in processed_elements:
                            continue
                        if dependency_counters[elem_id] > 0:
                            continue
                        # 找到第一个未处理的元素
                        meta = rows_meta[row]
                        start_time = current_time
                        end_time = start_time + elements[elem_id]['length']
                        elements_info[elem_id] = {
                            'start': start_time,
                            'end': end_time,
                            'elem': elements[elem_id]
                        }
                        heapq.heappush(event_queue, (end_time, elem_id))
                        meta['busy_until'] = end_time
                        meta['current_id'] = elem_id
                        break
                        
                else:
                    for i in range(len(all_rows[row])):
                        elem_id = all_rows[row][i]['id']
                        if elem_id in processed_elements:
                            continue
                        else:
                            if dependency_counters[elem_id] == 0:
                                elem = elements[elem_id]
                                start_time = current_time
                                end_time = start_time + elem['length']
                                elements_info[elem_id] = {
                                    'start': start_time,
                                    'end': end_time,
                                    'elem': elem
                                }
                                heapq.heappush(event_queue, (end_time, elem_id))
                                meta['busy_until'] = end_time
                                meta['current_id'] = elem_id
                            break
                        
        else:
            break
            raise RuntimeError("调度失败：存在循环依赖或未解决的依赖")

        # if not progress:
        #     if not event_queue:
        #         raise RuntimeError("调度失败：存在循环依赖或未解决的依赖")
        #     # 推进到下一个事件时间
        #     current_time = event_queue[0][0]

    return elements_info

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
                list[PP * dp + pp].append({"id": name, "number": mb, "color": forward_color_list[dp % 4], "length": length_list[pp], "dependency": dependency})
            
            #后向计算
            for pp in reversed(range(PP)):
                if pp == PP - 1:
                    dependency = f"{mb}_{dp}_{PP - 1}_forward"
                elif pp == half_PP - 1:
                    dependency = f"{mb}_{dp}_backward_delay"
                else:
                    dependency = f"{mb}_{dp}_{pp + 1}_backward"
                name = f"{mb}_{dp}_{pp}_backward"
                list[PP * dp + pp].append({"id": name, "number": mb, "color": backward_color_list[dp % 4], "length": 2 * length_list[pp], "dependency": dependency})
            
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

def read_vp_from_file(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    all_rows = []
    for rack in data:
        ops = rack["ops"]
        
        
    
    
    return all_rows

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
            if elem_id not in elements_info:
                continue
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
        



# B = 48
# PP = 8
# DP = 64
# Bandwidth = 1.3
# Desire_delay = 5

# k = Bandwidth / 1.3
# communication = 1 / k
# delay = (Desire_delay / 10) * 2


# parttern_list = dualpipe_pattern(PP, B)
# input_rows = regular_dualPipe_2_PP_8(PP, B, parttern_list, communication, delay)
# elements_info = generate_schedule_with_sequence(input_rows)
# json_data = single_DP_visualize_schedule(elements_info, input_rows, PP)
# save_to_file(json_data, 'regular_dualPipe_2_PP_8.json')




# # ####(Bandwidth, Desire_delay) 
# B = 48
# PP = 8
# DP = 64
# settings = [(2, 10), (2, 1), (0.5, 1), (1000, 0)]
# for Bandwidth, Desire_delay in settings:
#     print(f"Bandwidth: {Bandwidth}, Desire_delay: {Desire_delay}")
#     k = Bandwidth / 1.3
#     communication = 1 / k
#     delay = (Desire_delay / 10) * 2
#     input_rows = regular_vp_2_PP_8(B, communication, delay)
#     # elements_info = generate_schedule_with_sequence(input_rows)
#     elements_info = generate_schedule_json(input_rows)
#     json_data = single_DP_visualize_schedule(elements_info, input_rows, PP)
#     save_to_file(json_data, 'regular_vp_2_PP_8.json')
#     max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
#     max_elem = elements_info[max_elem_id]
#     print(f"regular_vp_2_1F_1B: {max_elem['end']}")

#     input_rows = regular_1F_1B(1, PP, B, communication, delay, 2)
#     elements_info = generate_schedule_with_sequence(input_rows)
#     json_data = single_DP_visualize_schedule(elements_info, input_rows, PP)
#     save_to_file(json_data, 'regular_1F_1B.json')
#     max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
#     max_elem = elements_info[max_elem_id]
#     print(f"regular_1F_1B: {max_elem['end']}")
    
#     parttern_list = dualpipe_pattern(PP, B)
#     input_rows = regular_dualPipe_2_PP_8(PP, B, parttern_list, communication, delay)
#     elements_info = generate_schedule_with_sequence(input_rows)
#     json_data = single_DP_visualize_schedule(elements_info, input_rows, PP)
#     save_to_file(json_data, 'regular_dualPipe_2_PP_8.json')
#     max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
#     max_elem = elements_info[max_elem_id]
#     print(f"regular_dualPipe: {max_elem['end']}")
    
    
B = 48
PP = 8
DP = 64    

DP_list = []
sequ_list = []
VP_list = []
DualPipe_list = []

Bandwidth_list = [0.5, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
# Desire_delay = 0.1
Desire_delay =  10

for Bandwidth in Bandwidth_list:
    print(f"Bandwidth: {Bandwidth}, Desire_delay: {Desire_delay}")
    k = Bandwidth / 1.3
    if Bandwidth == 10:
        communication = 0
    else:
        communication = 1 / k
    delay = (Desire_delay / 10) * 2
    input_rows = regular_vp_2_PP_8(B, communication, delay)
    # elements_info = generate_schedule_with_sequence(input_rows)
    elements_info = generate_schedule_json(input_rows)
    json_data = single_DP_visualize_schedule(elements_info, input_rows, PP)
    # save_to_file(json_data, 'regular_vp_2_PP_8.json')
    max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
    max_elem = elements_info[max_elem_id]
    # print(f"regular_vp_2_1F_1B: {max_elem['end']}")
    VP_list.append(5 * max_elem['end'])
    

    input_rows = regular_1F_1B(1, PP, B, communication, delay, 2)
    elements_info = generate_schedule_with_sequence(input_rows)
    json_data = single_DP_visualize_schedule(elements_info, input_rows, PP)
    # save_to_file(json_data, 'regular_1F_1B.json')
    max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
    max_elem = elements_info[max_elem_id]
    # print(f"regular_1F_1B: {max_elem['end']}")
    sequ_list.append(5 * max_elem['end'])
    
    
    sync_time = Desire_delay + 700 * (2 / Bandwidth)
    parttern_list = dualpipe_pattern(PP, B)
    input_rows = regular_dualPipe_2_PP_8(PP, B, parttern_list, communication, delay)
    elements_info = generate_schedule_with_sequence(input_rows)
    json_data = single_DP_visualize_schedule(elements_info, input_rows, PP)
    # save_to_file(json_data, 'regular_dualPipe_2_PP_8.json')
    max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
    max_elem = elements_info[max_elem_id]
    DualPipe_list.append(5 * max_elem['end'] + sync_time)
    # print(f"regular_dualPipe: {max_elem['end']}")
    
    DP_list.append(5*330 + sync_time)

# Bandwidth_list.append(6)
# DP_list.append(5 * 330)
# sequ_list.append(5 * 330)
# VP_list.append(5 * 309)
# DualPipe_list.append(5 * 306)

plt.figure(figsize=(8, 5), dpi=300)
ax = plt.gca()
# 坐标轴样式配置
# plt.xticks(fontsize=18, rotation=45)
# plt.xticks([0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0], 
#            ['0', '0.5', '1.0', '1.5', '2.0', '2.5', '3.0', '3.5','4.0', '4.5','5.0', 'intra-DC'], 
#            fontsize=18, rotation=45)
plt.xticks([0, 2.0,4.0, 6.0, 8.0, 10.0], 
           ['0', '2.0', '4.0', '6.0', '8.0', '10.0'], 
           fontsize=18, rotation=45)

plt.yticks(fontsize=18)
plt.ylim(1000, 5000)
# plt.xlim(0, 3.2)
# 坐标轴边界样式
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(1.5)
ax.spines['bottom'].set_linewidth(1.5)
# 网格和范围设置
plt.grid(axis="y", linewidth=0.8, alpha=0.6)
# 绘图
plt.plot(Bandwidth_list, DP_list, linewidth=3.5, color='red', label="Cross-DC DP")
plt.plot(Bandwidth_list, sequ_list, linewidth=3.5, color='purple', label = "Cross-DC PP Sequential")
plt.plot(Bandwidth_list, VP_list, linewidth=3.5, color='blue', label = "Cross-DC PP VP")
plt.plot(Bandwidth_list, DualPipe_list, linewidth=3.5, color='green', label = "Cross-DC PP DualPipe")
plt.legend(fontsize=18, loc='best')
plt.xlabel('Bandwidth (Tbps)', fontsize=18, labelpad=10)
plt.ylabel('Iteration Time (ms)', fontsize=18, labelpad=10)
# 自动调整布局，防止标签被裁剪
plt.tight_layout(rect=[0.08, 0.05, 0.98, 0.98])
plt.savefig(f'motivation_Bandwidth.png', bbox_inches='tight')
plt.savefig(f'motivation_Bandwidth.pdf', bbox_inches='tight')









B = 48
PP = 8
DP = 64    

DP_list = []
sequ_list = []
VP_list = []
DualPipe_list = []
Bandwidth = 0.5
# Bandwidth = 2
Desire_real_delay_list = [0.1, 1, 5, 10, 20]

for Desire_delay in Desire_real_delay_list:
    print(f"Bandwidth: {Bandwidth}, Desire_delay: {Desire_delay}")
    k = Bandwidth / 1.3
    if Bandwidth == 10:
        communication = 0
    else:
        communication = 1 / k
    delay = (Desire_delay / 10) * 2
    input_rows = regular_vp_2_PP_8(B, communication, delay)
    # elements_info = generate_schedule_with_sequence(input_rows)
    elements_info = generate_schedule_json(input_rows)
    json_data = single_DP_visualize_schedule(elements_info, input_rows, PP)
    # save_to_file(json_data, 'regular_vp_2_PP_8.json')
    max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
    max_elem = elements_info[max_elem_id]
    # print(f"regular_vp_2_1F_1B: {max_elem['end']}")
    VP_list.append(5 * max_elem['end'])
    

    input_rows = regular_1F_1B(1, PP, B, communication, delay, 2)
    elements_info = generate_schedule_with_sequence(input_rows)
    json_data = single_DP_visualize_schedule(elements_info, input_rows, PP)
    # save_to_file(json_data, 'regular_1F_1B.json')
    max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
    max_elem = elements_info[max_elem_id]
    # print(f"regular_1F_1B: {max_elem['end']}")
    sequ_list.append(5 * max_elem['end'])
    
    
    sync_time = Desire_delay + 700 * (2 / Bandwidth)
    parttern_list = dualpipe_pattern(PP, B)
    input_rows = regular_dualPipe_2_PP_8(PP, B, parttern_list, communication, delay)
    elements_info = generate_schedule_with_sequence(input_rows)
    json_data = single_DP_visualize_schedule(elements_info, input_rows, PP)
    # save_to_file(json_data, 'regular_dualPipe_2_PP_8.json')
    max_elem_id = max(elements_info, key=lambda eid: elements_info[eid]['end'])
    max_elem = elements_info[max_elem_id]
    DualPipe_list.append(5 * max_elem['end'] + sync_time)
    # print(f"regular_dualPipe: {max_elem['end']}")
    
    DP_list.append(5*330 + sync_time)

# Bandwidth_list.append(0)
# DP_list.append(5 * 330)
# sequ_list.append(5 * 330)
# VP_list.append(5 * 309)
# DualPipe_list.append(5 * 306)

plt.figure(figsize=(8, 5), dpi=300)
ax = plt.gca()
# 坐标轴样式配置
# plt.xticks(fontsize=18, rotation=45)
plt.xticks([0, 5, 10, 15, 20], 
           ['0', '5', '10', '15', '20'], 
           fontsize=18, rotation=45)

plt.yticks(fontsize=18)
plt.ylim(1000, 5000)
# plt.xlim(0, 3.2)
# 坐标轴边界样式
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(1.5)
ax.spines['bottom'].set_linewidth(1.5)
# 网格和范围设置
plt.grid(axis="y", linewidth=0.8, alpha=0.6)
# 绘图
plt.plot(Desire_real_delay_list , DP_list, linewidth=3.5, color='red', label="Cross-DC DP")
plt.plot(Desire_real_delay_list , sequ_list, linewidth=3.5, color='purple', label = "Cross-DC PP Sequential")
plt.plot(Desire_real_delay_list , VP_list, linewidth=3.5, color='blue', label = "Cross-DC PP VP")
plt.plot(Desire_real_delay_list , DualPipe_list, linewidth=3.5, color='green', label = "Cross-DC PP DualPipe")
plt.legend(fontsize=18, loc='best')
plt.xlabel('Delay (ms)', fontsize=18, labelpad=10)
plt.ylabel('Iteration Time (ms)', fontsize=18, labelpad=10)
# 自动调整布局，防止标签被裁剪
plt.tight_layout(rect=[0.08, 0.05, 0.98, 0.98])
plt.savefig(f'motivation_Delay.png', bbox_inches='tight')
plt.savefig(f'motivation_Delay.pdf', bbox_inches='tight')


# Desire_real_delay_list = [0.1, 1, 5, 10, 20]





