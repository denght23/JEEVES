import re
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# ===================================================================
# 第一步：定义Flow分类逻辑
# ===================================================================
def classify_flow(flow_name):
    """
    返回类型："intra"（Rank同区间）或 "inter"（Rank跨区间）
    """
    # 提取Rank数字
    ranks = list(map(int, re.findall(r"Rank(\d+)", flow_name)))
    if len(ranks) != 2:
        return None
    
    # 过滤包含F999的Flow
    if re.search(r"F999", flow_name):
        return None
    
    x, y = ranks
    # 判断区间类型
    x_in_low = (0 <= x <= 7)
    y_in_low = (0 <= y <= 7)
    
    if (x_in_low and y_in_low) or (not x_in_low and not y_in_low):
        return "intra"  # 同区间
    elif (x_in_low ^ y_in_low):
        return "inter"  # 跨区间
    return None

# ===================================================================
# 第二步：解析文件并计算完成时间
# ===================================================================
def parse_file(filepath):
    """
    返回字典：
    {
        "intra": {"flow_name": duration, ...},
        "inter": {"flow_name": duration, ...}
    }
    """
    flow_data = defaultdict(dict)  # {flow_name: {"begin": time, "finish": time}}
    
    # 读取文件
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if parts[0] != "Flow":
                continue
            
            flow_name = parts[1]
            event_type = parts[2]
            timestamp = float(parts[3])
            
            flow_data[flow_name][event_type] = timestamp
    
    # 计算持续时间
    results = {"intra": {}, "inter": {}}
    for flow_name, times in flow_data.items():
        if "begin" not in times or "finish" not in times:
            continue
            
        flow_type = classify_flow(flow_name)
        if not flow_type:
            continue
        print(flow_name, flow_type)
            
        duration = times["finish"] - times["begin"]
        results[flow_type][flow_name] = duration
    
    return results

# ===================================================================
# 第三步：比较两个文件并计算比值
# ===================================================================
def calculate_ratios(min_max_data, random_data):
    ratios = {"intra": [], "inter": []}
    
    for flow_type in ["intra", "inter"]:
        for flow_name, min_max_duration in min_max_data[flow_type].items():
            if flow_name in random_data[flow_type]:
                random_duration = random_data[flow_type][flow_name]
                if random_duration > 0:
                    ratio = min_max_duration / random_duration
                    ratios[flow_type].append(ratio)
    
    return ratios

# ===================================================================
# 第四步：绘制CDF图
# ===================================================================
def plot_cdf(ratios, title_prefix):
    plt.figure(figsize=(10, 6))
    
    for flow_type, values in ratios.items():
        if not values:
            continue
            
        # 排序并计算CDF
        sorted_data = np.sort(values)
        cdf = np.arange(1, len(sorted_data)+1) / len(sorted_data)
        
        # 绘制曲线
        label = f"{flow_type} (n={len(values)})"
        plt.plot(sorted_data, cdf, marker='.', linestyle='-', label=label)
    
    plt.xlabel('Ratio (min_max / random)')
    plt.ylabel('CDF')
    plt.title(f"{title_prefix} - Completion Time Ratio Distribution")
    plt.grid(True)
    plt.legend()
    plt.savefig(f"{title_prefix}_completion_time_cdf.png")


def calculate_averages(flow_data):
    """计算intra和inter类别的平均完成时间"""
    averages = {}
    for flow_type in ['intra', 'inter']:
        durations = list(flow_data[flow_type].values())
        if len(durations) == 0:
            averages[flow_type] = None
        else:
            averages[flow_type] = np.mean(durations)
    return averages

# ===================================================================
# 主流程
# ===================================================================
if __name__ == "__main__":
    # 文件路径
    file1 = "result/link_num_4_bandwidth_10_delay_2_route_min_max_flows/records.txt"
    file2 = "result/link_num_4_bandwidth_10_delay_2_route_random/records.txt"
    
    # 解析文件
    min_max_data = parse_file(file1)
    random_data = parse_file(file2)
    
    min_max_avg = calculate_averages(min_max_data)
    random_avg = calculate_averages(random_data)
    
    print("\n========== 平均完成时间统计 ==========")
    print(f"[Min-Max策略]")
    print(f"Intra类: {min_max_avg['intra']:.6f} sec (样本数: {len(min_max_data['intra'])})")
    print(f"Inter类: {min_max_avg['inter']:.6f} sec (样本数: {len(min_max_data['inter'])})\n")
    
    print(f"[Random策略]")
    print(f"Intra类: {random_avg['intra']:.6f} sec (样本数: {len(random_data['intra'])})")
    print(f"Inter类: {random_avg['inter']:.6f} sec (样本数: {len(random_data['inter'])})")    

    # 计算比值
    ratios = calculate_ratios(min_max_data, random_data)
    
    # 绘制图形
    plot_cdf(ratios, "Flow Type Comparison")

# ===================================================================
# 输出说明：
# 1. 图中"intra"表示Rank在同区间的Flow（如Rank0-Rank4或Rank8-Rank12）
# 2. 图中"inter"表示Rank跨区间的Flow（如Rank2-Rank12）
# 3. X轴为min_max策略与random策略完成时间的比值
# ===================================================================