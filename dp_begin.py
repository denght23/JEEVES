import json

# 读取 JSON 文件
with open('/home/denghaotian/research/LLM_planning/data/workload_16_PP4_DP4_TP1_VPP2_BATCH8_NO_PRI.json', 'r') as f:
    data = json.load(f)

# 找到 depends 为空的元素的 op_name
begin_dp_list = []

for rank in data:
    for op in rank['ops']:
        if '999' in op['op_name'] and 'depends' in op and op['depends'] == "":
            begin_dp_list.append(op['op_name'])


# 读取 records.txt 文件
records_file_1 = './result/link_num_4_bandwidth_10_delay_2_route_random/records.txt'
records_file_2 = './result/link_num_4_bandwidth_10_delay_2_route_min_max_flows/records.txt'

def read_records(file_path):
    with open(file_path, 'r') as f:
        return f.readlines()

records_1 = read_records(records_file_1)
records_2 = read_records(records_file_2)

def extract_begin_times(records, begin_dp_list):
    begin_times = {}
    for line in records:
        parts = line.strip().split(',')
        if len(parts) == 4:
            _, op_name, status, begin_time = parts
            if status == 'begin' and op_name in begin_dp_list:
                begin_times[op_name] = float(begin_time)
    return begin_times

begin_times_1 = extract_begin_times(records_1, begin_dp_list)
begin_times_2 = extract_begin_times(records_2, begin_dp_list)

# 比较 begin_time 的值以及差
time_differences = {}
for op_name in begin_times_1:
    if op_name in begin_times_2:
        time_differences[op_name] = begin_times_2[op_name] - begin_times_1[op_name]

# 打印结果
for op_name, time_diff in time_differences.items():
    print(f"Operation: {op_name}, Time Difference: {time_diff}")

# 统计数据
total_diff = sum(time_differences.values())
average_diff = total_diff / len(time_differences) if time_differences else 0
max_diff = max(time_differences.values(), default=0)
min_diff = min(time_differences.values(), default=0)

print(f"Total Time Difference: {total_diff}")
print(f"Average Time Difference: {average_diff}")
print(f"Max Time Difference: {max_diff}")
print(f"Min Time Difference: {min_diff}")