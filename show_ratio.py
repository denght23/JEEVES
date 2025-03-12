import ast
import matplotlib.pyplot as plt
import sys

def get_optimal_load(banwidth, link_num, flow_num):
    # bandwith: Gbps
    if flow_num <= link_num:
        return banwidth * flow_num
    else:
        return banwidth * link_num

def extract_real_optimal_ratio(load_file, number_file, target_links, banwidth, link_num):
    """
    bandwith: Gbps
    """
    real_optimal_ratio = [[],[]]
    with open(load_file, 'r') as rf, open(number_file, 'r') as nf:
        for load_line, number_line in zip(rf, nf):
            try:
                load_data = ast.literal_eval(load_line.strip())
                number_data = ast.literal_eval(number_line.strip())
                time = load_data['time']
                link_data = load_data['link']
                flow_numbers = number_data['link']
                total_flow_num = 0
                total_load = 0
                load_list = []
                number_list = []
                for link in target_links:
                    if link in link_data:
                        total_flow_num += flow_numbers[link]
                        total_load += link_data[link]
                        load_list.append(link_data[link])
                        number_list.append(flow_numbers[link])
                
                
                optimal_load = get_optimal_load(banwidth, link_num, total_flow_num)
                if (total_load > optimal_load):
                    print(f"time: {time}, total_load: {total_load}, optimal_load: {optimal_load}")
                    print(f"Load list at time {time}: {load_list}")
                    print(f"Number list at time {time}: {number_list}")
                
                if optimal_load == 0:
                    ratio = 0
                else:
                    ratio = total_load / optimal_load               
                real_optimal_ratio[0].append(time)
                real_optimal_ratio[1].append(ratio)
                
            except (ValueError, SyntaxError, KeyError) as e:
                print(f"解析行时出错: {load_line}, {number_line}\n错误: {str(e)}")
                continue
    
                
    return real_optimal_ratio



def plot_ratio(real_optimal_ratio, header):
    """
    绘制链路带宽使用情况的折线图
    :param link_usage: {链路名称: (时间列表, 带宽列表)}
    """
    plt.figure(figsize=(10, 6))
    
    plt.plot(real_optimal_ratio[0], real_optimal_ratio[1], linestyle='-', label='Real Optimal Ratio')
    
    plt.title(f"{header} Real Optimal Ratio")
    plt.xlabel("time (s)")
    plt.ylabel("ratio")
    plt.grid(True)
    plt.legend()
    plt.savefig(f"result/{header}/real_optimal_ratio.png")


# 使用示例
# 从文件中读取目标链路名称
num = int(sys.argv[1])
bandwidth = int(sys.argv[2])
delay = 2
odd = int(sys.argv[3]) # 1 or 0, 1 for odd,0 for even

route_list = ["random", "min_max_flows"]

ratios = {}
for route in route_list:
    file_name = f"link_num_{num}_bandwidth_{bandwidth}_delay_{delay}_route_{route}"
    link_file = f"result/{file_name}/core_links.txt"
    with open(link_file, "r") as f:
        target_links = [line.strip() for line in f.readlines()]
        load_file = f"result/{file_name}/link_load.txt"
        flow_number_file = f"result/{file_name}/link_flow_num.txt"
        if (odd == 1):
            links = target_links[::2]
        else:
            links = target_links[1::2]
        ratio = extract_real_optimal_ratio(load_file, flow_number_file, links, bandwidth, num)
        ratios[route] = ratio

# Plot all routes on the same graph
plt.figure(figsize=(10, 6))
for route, ratio in ratios.items():
    filtered_time = [t for t in ratio[0] if t <= 0.6]
    filtered_ratio = [r for t, r in zip(ratio[0], ratio[1]) if t <= 0.6]
    plt.plot(filtered_time, filtered_ratio, linestyle='-', label=f'{route} Real Optimal Ratio')

plt.title(f"Real Optimal Ratio for Different Routes")
plt.xlabel("time (s)")
plt.ylabel("ratio")
plt.grid(True)
plt.legend()
plt.savefig(f"result/{file_name}/real_optimal_ratio_{odd}.png")

        
        
        
