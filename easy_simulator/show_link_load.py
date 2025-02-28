import ast
import matplotlib.pyplot as plt
import sys

def extract_link_usage(file_path, target_links):
    """
    从文件中提取指定链路的时间-带宽数据
    :param file_path: 文件路径
    :param target_links: 目标链路名称列表（如 ["link61", "link65"]）
    :return: {链路名称: (时间列表, 带宽列表)}
    """
    link_usage = {link: ([], []) for link in target_links}
    
    with open(file_path, 'r') as f:
        for line in f:
            try:
                # 将行数据解析为字典
                data = ast.literal_eval(line.strip())
                time = data['time']
                link_data = data['link']
                
                # 提取目标链路的带宽
                for link in target_links:
                    if link in link_data:
                        link_usage[link][0].append(time)
                        link_usage[link][1].append(link_data[link])
                    
            except (ValueError, SyntaxError, KeyError) as e:
                print(f"解析行时出错: {line}\n错误: {str(e)}")
                continue
                
    return link_usage

def plot_link_usage(link_usage, header):
    """
    绘制链路带宽使用情况的折线图
    :param link_usage: {链路名称: (时间列表, 带宽列表)}
    """
    plt.figure(figsize=(10, 6))
    
    for link, (timestamps, bandwidths) in link_usage.items():
        plt.plot(timestamps, bandwidths, linestyle='-', label=link)
    
    plt.title(f"{header} Link Bandwidth Load")
    plt.xlabel("time (s)")
    plt.ylabel("load(Gbps)")
    plt.grid(True)
    plt.legend()
    plt.savefig(f"{header}_link_load.png")
    
def plot_link_util(link_usage, header):
    """
    绘制链路带宽使用情况的折线图
    :param link_usage: {链路名称: (时间列表, 带宽列表)}
    """
    plt.figure(figsize=(10, 6))
    
    for link, (timestamps, bandwidths) in link_usage.items():
        plt.plot(timestamps, bandwidths, linestyle='-', label=link)
    
    plt.title(f"{header} Link Bandwidth Util")
    plt.xlabel("time (s)")
    plt.ylabel("util")
    plt.grid(True)
    plt.legend()
    plt.savefig(f"{header}_link_util.png")
    
def calculate_average_util(link_usage):
    """
    计算链路的平均util随时间变化
    :param link_usage: {链路名称: (时间列表, 带宽列表)}
    :return: (时间列表, 平均util列表)
    """
    if not link_usage:
        return [], []

    # 假设所有链路的时间戳是相同的
    timestamps = next(iter(link_usage.values()))[0]
    avg_utils = []

    for i in range(len(timestamps)):
        total_util = 0
        count = 0
        for link, (times, utils) in link_usage.items():
            if i < len(utils):
                total_util += utils[i]
                count += 1
        avg_utils.append(total_util / count if count > 0 else 0)

    return timestamps, avg_utils

# 使用示例
# 从文件中读取目标链路名称
num = int(sys.argv[1])
bandwidth = int(sys.argv[2])
delay = 2
file_name = f"link_num_{num}_bandwidth_{bandwidth}_delay_{delay}"

link_file = f"{file_name}_core_links.txt"
with open(link_file, "r") as f:
    target_links = [line.strip() for line in f.readlines()]


load_file = f"{file_name}_link_load.txt"
util_file = f"{file_name}_link_util.txt"
# 提取数据
link_load = extract_link_usage(load_file, target_links)
# 绘制图表
plot_link_usage(link_load, file_name)
link_util = extract_link_usage(util_file, target_links)
plot_link_util(link_util, file_name)


# 分别提取奇数行和偶数行的链路
odd_links = target_links[::2]
even_links = target_links[1::2]

# 提取奇数行链路的util数据并计算平均util
odd_link_util = extract_link_usage(util_file, odd_links)
odd_timestamps, odd_avg_util = calculate_average_util(odd_link_util)

# 提取偶数行链路的util数据并计算平均util
even_link_util = extract_link_usage(util_file, even_links)
even_timestamps, even_avg_util = calculate_average_util(even_link_util)

# 绘制平均util随时间变化的折线图
plt.figure(figsize=(10, 6))
plt.plot(odd_timestamps, odd_avg_util, linestyle='-', label='20-21 Util')
plt.plot(even_timestamps, even_avg_util, linestyle='-', label='21-20 Util')

plt.title(f"{file_name} Average Link Utilization")
plt.xlabel("time (s)")
plt.ylabel("average util")
plt.grid(True)
plt.legend()
plt.savefig(f"{file_name}_average_link_util.png")

# 计算并打印util不为0的点的平均值
def calculate_non_zero_average(util_list):
    non_zero_utils = [util for util in util_list if util != 0]
    if non_zero_utils:
        return sum(non_zero_utils) / len(non_zero_utils)
    return 0

odd_non_zero_avg_util = calculate_non_zero_average(odd_avg_util)
even_non_zero_avg_util = calculate_non_zero_average(even_avg_util)

print(f"Num: {num}, Bandwidth: {bandwidth}")
print(f"20-21 average util: {odd_non_zero_avg_util * 100:.2f}%")
print(f"21-20 average util: {even_non_zero_avg_util * 100:.2f}%")