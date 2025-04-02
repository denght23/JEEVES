import json

small_data = '../data/change_data.json'
large_data = '../data/change_data_1024_rack.json'
# 统计每个事件的依赖和被依赖的数量，做一个简单的通路复杂度分析
def use_depend_analyse(file_path):
    dict = {}
    with open(file_path, 'r') as f:
        data = json.load(f)
    for rank in data:
        for op in rank['ops']:
            if op['op_name'] not in dict:
                dict[op['op_name']] = {'depend_num':0, 'use_num':0}
    for rank in data:
        for op in rank['ops']:
            if 'depends' in op and op['op_type']!='recv':
                depends_name = op['depends']
                use_name = op['op_name']
                # 依赖的事件被使用了，事件本身多了一个依赖
                dict[depends_name]['use_num'] +=1
                dict[use_name]['depend_num'] +=1
    min_use = 10000
    max_use = -100
    min_depend = 10000
    max_depend = -100
    
    for key in dict:
        if dict[key]['use_num'] <min_use:
            min_use = dict[key]['use_num']
        if dict[key]['use_num'] >max_use:
            max_use = dict[key]['use_num']
        if dict[key]['depend_num']<min_depend:
            min_depend = dict[key]['depend_num']
        if dict[key]['depend_num']>max_depend:
            max_depend = dict[key]['depend_num']
    print('min_use:', min_use) # 0 最后一个事件没有被任何事件依赖
    print('max_use:', max_use) # 2 一个事件最多被两个事件依赖
    print('min_depend:', min_depend) # 0 第一个事件没有依赖任何事件
    print('max_depend:', max_depend) # 1 一个事件最多只依赖一个事件

if __name__ == "__main__":
    print('small_data:')
    use_depend_analyse(small_data)
    print('large_data:')
    use_depend_analyse(large_data)
    
