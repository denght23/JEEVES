import json

class DependencyGraph:
    def __init__(self, filepath):
        self.nodes = self._load_data(filepath)
        self.parent_map = self._build_parent_map()
        self.ancestors = self._preprocess_ancestors()
        self.file_path = filepath
    
    def _load_data(self, filepath):
        """加载JSON数据并过滤出op_type为send或gpu的节点"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        nodes = []
        for rank in data:
            for op in rank['ops']:
                if op['op_type'] in {'send', 'gpu'}:
                    nodes.append(op)
        return nodes
    
    def _build_parent_map(self):
        """构建父节点映射表，记录每个节点的直接依赖"""
        op_names = {op['op_name'] for op in self.nodes}
        parent_map = {}
        for op in self.nodes:
            depends = op.get('depends')
            if depends and depends in op_names:
                parent_map[op['op_name']] = depends
            else:
                parent_map[op['op_name']] = None
        return parent_map
    
    def _preprocess_ancestors(self):
        """预处理每个节点的所有祖先集合（包含自己）"""
        ancestors = {}
        for node in self.parent_map:
            current = node
            visited = set()
            while current is not None:
                if current in visited:
                    break  # 防止循环依赖
                visited.add(current)
                current = self.parent_map.get(current)
            ancestors[node] = visited
        return ancestors
    
    def is_reachable(self, a, b):
        """检查从b的依赖路径是否能到达a"""
        return a in self.ancestors.get(b, set())
    
    def get_numbered_dp_list(self):
        begin_dp_list = []
        with open(self.file_path, 'r') as f:
            data = json.load(f)
        for rank in data:
            for op in rank['ops']:
                if '999' in op['op_name'] and 'depends' in op and op['depends'].startswith('B'):
                    begin_dp_list.append(op['op_name'])
        pp_numbers = []
        for op_name in begin_dp_list:
            if 'PP' in op_name:
                pp_index = op_name.index('PP') + 2
                pp_number = ''
                while pp_index < len(op_name) and op_name[pp_index].isdigit():
                    pp_number += op_name[pp_index]
                    pp_index += 1
                if pp_number:
                    pp_numbers.append((op_name, int(pp_number)))
        
        pp_numbers.sort(key=lambda x: x[1])
        numbered_begin_dp_list = {op_name: idx for idx, (op_name, _) in enumerate(pp_numbers)}
        dp_depend_dict = {}
        for rank in data:
            for op in rank['ops']:
                if '999' in op['op_name'] and 'depends' in op:
                    for begin_dp in begin_dp_list:
                        if self.is_reachable(begin_dp, op['op_name']):
                            if begin_dp not in dp_depend_dict:
                                dp_depend_dict[begin_dp] = []
                            dp_depend_dict[begin_dp].append(op['op_name'])
                            break
        for begin_dp in dp_depend_dict:
            for op_name in dp_depend_dict[begin_dp]:
                if op_name not in numbered_begin_dp_list:
                    numbered_begin_dp_list[op_name] = numbered_begin_dp_list[begin_dp]
        return numbered_begin_dp_list

# # 使用示例
# if __name__ == "__main__":
#     # 初始化依赖图（替换为实际文件路径）
#     workload_file = '/home/denghaotian/research/LLM_planning/simulate/easy_simulate/data/change_data.json'
#     graph = DependencyGraph(workload_file)
    
#     # 示例查询
#     a = "F1a_DP3_PP2_TP0_Rank11"
#     b = "DATA_F2a_DP0_PP0_TP0_Rank0_Rank4"
#     print(graph.is_reachable(a, b))  # 应输出 True

    
#     begin_dp_list = []
#     with open(workload_file, 'r') as f:
#         data = json.load(f)
#     for rank in data:
#         for op in rank['ops']:
#             if '999' in op['op_name'] and 'depends' in op and op['depends'].startswith('B'):
#                 begin_dp_list.append(op['op_name'])
    
#     # 提取pp_number并排序
#     pp_numbers = []
#     for op_name in begin_dp_list:
#         if 'PP' in op_name:
#             pp_index = op_name.index('PP') + 2
#             pp_number = ''
#             while pp_index < len(op_name) and op_name[pp_index].isdigit():
#                 pp_number += op_name[pp_index]
#                 pp_index += 1
#             if pp_number:
#                 pp_numbers.append((op_name, int(pp_number)))
    
#     # 根据pp_number排序并编号
#     pp_numbers.sort(key=lambda x: x[1])
#     numbered_begin_dp_list = {op_name: idx for idx, (op_name, _) in enumerate(pp_numbers)}
    
#     # 打印编号后的begin_dp_list
#     for op_name, idx in numbered_begin_dp_list.items():
#         print(f"{op_name} -> {idx}")
                
#     print(len(begin_dp_list))
#     print(begin_dp_list)
#     dp_depend_dict = {}
#     for rank in data:
#          for op in rank['ops']:
#              if '999' in op['op_name'] and 'depends' in op:
#                  for begin_dp in begin_dp_list:
#                      if graph.is_reachable(begin_dp, op['op_name']):
#                          if begin_dp not in dp_depend_dict:
#                             dp_depend_dict[begin_dp] = []
#                          dp_depend_dict[begin_dp].append(op['op_name'])
#                          break
#     for begin_dp in dp_depend_dict:
#         print(begin_dp, dp_depend_dict[begin_dp])
#         for op_name in dp_depend_dict[begin_dp]:
#             if op_name not in numbered_begin_dp_list:
#                 numbered_begin_dp_list[op_name] = numbered_begin_dp_list[begin_dp]
                
#     print(numbered_begin_dp_list)