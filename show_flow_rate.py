import re
from ast import literal_eval

def extract_flow_rates(file_path, target_flow):
    results = []
    
    with open(file_path, 'r') as f:
        for line in f:
            # 修复单引号问题并解析为字典
            try:
                line_data = literal_eval(line.strip())
                timestamp = float(line_data['time'])
                flows = line_data['flow']
                
                # 精确匹配目标流量名称
                if target_flow in flows:
                    results.append( (timestamp, flows[target_flow]) )
                    
            except Exception as e:
                print(f"解析行时出错: {line}\n错误: {str(e)}")
                continue
                
    # 按时间排序并去重（保留最后出现值）
    sorted_results = sorted(results, key=lambda x: x[0])
    final = {}
    for t, rate in sorted_results:
        final[t] = rate  # 相同时间戳保留最后出现的值
    return list(final.items())


def calculate_total_data(rate_sequence, end_time):
    """
    计算总发送数据量
    :param rate_sequence: 速率变化序列，格式 [(时间戳, 速率), ...]
    :param end_time: 结束时间（秒）
    :return: (开始时间, 结束时间, 总发送数据量)
    """
    # 提取开始时间
    t_start = rate_sequence[0][0]
    
    total_data = 0  # 总数据量（MB）
    
    # 遍历速率序列，计算每个时间段的数据量
    for i in range(len(rate_sequence) - 1):
        t1, rate1 = rate_sequence[i]
        t2, rate2 = rate_sequence[i + 1]
        duration = t2 - t1  # 时间段长度（秒）
        data = rate1 * 1000 * duration / 8  # 数据量（MB）
        total_data += data
    
    # 添加最后一个时间段的数据量（从最后一个时间点到结束时间）
    last_time, last_rate = rate_sequence[-1]
    last_duration = end_time - last_time  # 最后一个时间段的长度
    if last_duration > 0:  # 确保时间段有效
        total_data += last_rate * 1000 * last_duration / 8
    
    return t_start, end_time, total_data

# 使用示例
file_path = "rate_record.txt"
target_name = "DATA_B2b_DP1_PP1_TP0_Rank5_Rank1"
end_time = 0.19188333333333332
rate_sequence = extract_flow_rates(file_path, target_name)

# 打印输出
print(f"流量 {target_name} 的速率变化：")
for timestamp, rate in rate_sequence:
    print(f"时间: {timestamp:.4f}s, 速率: {rate} Gbps")

t_start, t_end, total_data = calculate_total_data(rate_sequence, end_time)

# 输出结果
print(f"开始时间: {t_start:.4f}s")
print(f"结束时间: {t_end:.4f}s")
print(f"总发送数据量: {total_data:.2f} MB")

    

    