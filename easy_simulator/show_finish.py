import matplotlib.pyplot as plt
import sys

def parse_file(file_path):
    """
    解析文件并提取两类 FLOW 数据
    :param file_path: 文件路径
    :return: (第一类数据列表, 第二类数据列表)
    """
    class1_data = []  # 第一类数据：包含 F999 且为 finish
    class2_data = []  # 第二类数据：不包含 F999 且为 finish
    
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) < 4:
                continue  # 跳过格式错误行
            
            event_type, flow_name, event_status, timestamp = parts
            
            if event_type == "Flow" and event_status == "finish":
                if "F999" in flow_name:
                    # 第一类数据
                    dp = flow_name.split('_')[2]  # 提取 DP
                    pp = flow_name.split('_')[3]  # 提取 PP
                    label = f"DP{dp}_PP{pp}"  # 生成纵坐标标签
                    class1_data.append((float(timestamp), 1, label))
                else:
                    # 第二类数据
                    dp = flow_name.split('_')[2]  # 提取 DP
                    pp = flow_name.split('_')[3]  # 提取 PP
                    label = f"DP{dp}_PP{pp}"  # 生成纵坐标标签
                    class2_data.append((float(timestamp), 2, label))
    
    return class1_data, class2_data

def plot_scatter(class1_data, class2_data, file_name):
    """
    绘制散点图
    :param class1_data: 第一类数据 [(时间, 纵坐标值, 标签), ...]
    :param class2_data: 第二类数据 [(时间, 纵坐标值, 标签), ...]
    :param file_name: 文件名前缀
    """
    plt.figure(figsize=(10, 6))
    
    # 打印两类数据的数量
    print(f"第一类数据数量: {len(class1_data)}")
    print(f"第二类数据数量: {len(class2_data)}")
    
    # 绘制第一类数据
    timestamps1, y_values1, labels1 = zip(*class1_data)
    plt.scatter(timestamps1, y_values1, color='blue', label='DP')
    
    # 绘制第二类数据
    timestamps2, y_values2, labels2 = zip(*class2_data)
    plt.scatter(timestamps2, y_values2, color='red', label='PP')
    
    # # 添加纵坐标标签
    # for timestamp, y_value, label in class1_data + class2_data:
    #     plt.text(timestamp, y_value, label, fontsize=8, ha='right', va='bottom')
    
    # 设置图表标题和标签
    plt.title("FLOW Completion Time Distribution")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Category")
    plt.yticks([1, 2], ["DP", "PP"])
    plt.grid(True)
    plt.legend()
    
    # 保存图表
    plt.savefig(f"{file_name}_scatter_plot.png")
    plt.show()

# 使用示例
num = int(sys.argv[1])
bandwidth = int(sys.argv[2])
delay = 2
file_name = f"link_num_{num}_bandwidth_{bandwidth}_delay_{delay}"


record_file = f"{file_name}_records.txt"

# 解析文件并提取数据
class1_data, class2_data = parse_file(record_file)

# 绘制散点图
plot_scatter(class1_data, class2_data, file_name)