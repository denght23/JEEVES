import json
import re
import ijson
# 修改原始数据，为所有数据的第一个DP添加dependency，依赖为当前rank上的最后一个计算任务(op_type='gpu')
# 读取 JSON 文件
# with open('../data_1024_rack/workload_1024_PP16_DP8_TP8_VPP6_BATCH64_NO_PRI.json', 'r', encoding='utf-8') as f:
#     data = json.load(f)

# # 遍历所有条目并修改
# for rank in data:
#     for item in rank['ops']:
#         if item['op_name'].startswith("DATA0_F999"):
#             if item['op_type'] == 'send' and item['depends'] == "":
#                 # 提取 Rank（如 Rank129）
#                 match = re.search(r'Rank\d+', item['op_name'])
#                 if match:
#                     rank_str = match.group()  # 'Rank129'
#                     print(rank_str)

#                     # 查找符合条件的目标项
#                     for rank2 in data:
#                         for target in rank2['ops']:
#                             if target['op_type'] == 'gpu' and \
#                             target['op_name'].startswith('B16f') and \
#                             re.search(rf'{rank_str}(?!\d)', target['op_name']):
                                
#                                 # 写入 depends
#                                 item['depends'] = target['op_name']
#                                 print(target['op_name'])
#                                 break  # 找到后不再查找

# # 写回修改后的 JSON 文件
# with open('../data/change_data_1024_rack.json', 'w', encoding='utf-8') as f:
#     json.dump(data, f, ensure_ascii=False, indent=4)




#***********************上面为对1024的处理************************
#***********************下面为对256的处理************************

# 用于存储修改后的数据
modified_data = []

with open('../data_10240_rack/workload_10240_PP32_DP10_TP32_VPP2_BATCH64_NO_PRI.json', 'r', encoding='utf-8') as f:
    for rank in ijson.items(f, ''):
        for item in rank['ops']:
            if item['op_name'].startswith("DATA0_F999"):
                if item['op_type'] == 'send' and item['depends'] == "":
                    # 提取 Rank（如 Rank129）
                    match = re.search(r'Rank\d+', item['op_name'])
                    if match:
                        rank_str = match.group()  # 'Rank129'
                        print(rank_str)

                        # 查找符合条件的目标项
                        for rank2 in ijson.items(f,''):  # 遍历已处理的数据
                            for target in rank2['ops']:
                                if target['op_type'] == 'gpu' and \
                                target['op_name'].startswith('B64b') and \
                                re.search(rf'{rank_str}(?!\d)', target['op_name']):
                                    
                                    # 写入 depends
                                    item['depends'] = target['op_name']
                                    print(target['op_name'])
                                    break  # 找到后不再查找
        # 将修改后的 rank 添加到 modified_data
        modified_data.append(rank)

# 写回修改后的 JSON 文件
with open('../data/change_data_10240_rack.json', 'w', encoding='utf-8') as f:
    json.dump(modified_data, f, ensure_ascii=False, indent=4)
