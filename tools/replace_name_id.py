import csv
import json
def replace_flow_names_with_ids(csv_file_path, mapping_file_path, output_file_path):
    # 读取映射文件，创建名称到ID的字典
    flow_mapping = {}
    with open(mapping_file_path, mode='r') as mapping_file:
        # 假设映射文件是CSV格式，第一列是名称，第二列是ID
        data = json.load(mapping_file)
        for rank in data:
            for item in rank['ops']:
                if 'flow_id' in item:
                    flow_mapping[item['op_name']] = item['flow_id']
    
    # 读取原始CSV文件并替换第一列的值
    with open(csv_file_path, mode='r') as input_file, \
         open(output_file_path, mode='w', newline='') as output_file:
        
        reader = csv.reader(input_file)
        writer = csv.writer(output_file)
        
        for row in reader:
            if len(row) >= 1:
                original_flow = row[0]
                # 替换第一列的值为对应的ID，如果找不到则保持原样
                row[0] = flow_mapping.get(original_flow, original_flow)
                writer.writerow(row)

# 使用示例
replace_flow_names_with_ids(
    '../data/',      # 输入CSV文件路径
    '../data_4096_rack/workload_3k_1k_NO_PRI.json',    # 流名称到ID的映射文件路径
    './data_csv_new/4096_double_flow_paths.csv'      # 输出文件路径
)