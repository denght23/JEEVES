class Topology:
    def __init__(self):
        # 邻接表结构：{
        #   '节点A': [('相邻节点B', '链路名称1'), ('相邻节点C', '链路名称2')],
        #   ...
        # }
        self.adjacency = {}
    
    def add_link(self, link_name, start_node, end_node):
        """添加单向链路"""
        # 添加节点到邻接表（如果不存在）
        self.adjacency.setdefault(start_node, [])
        # 添加单向连接关系
        self.adjacency[start_node].append((end_node, link_name))
    
    def find_all_paths(self, start, end):
        """查找所有路径（使用深度优先搜索）"""
        def dfs(current, path_links, visited_nodes, all_paths):
            if current == end:
                all_paths.append(list(path_links))
                return
            
            for neighbor, link in self.adjacency.get(current, []):
                if neighbor not in visited_nodes:
                    # 记录访问过的节点（避免环路）
                    visited_nodes.add(neighbor)
                    # 添加当前链路到路径
                    path_links.append(link)
                    
                    dfs(neighbor, path_links, visited_nodes, all_paths)
                    
                    # 回溯
                    path_links.pop()
                    visited_nodes.remove(neighbor)
        
        all_paths = []
        if start in self.adjacency:
            dfs(start, [], set([start]), all_paths)
        return all_paths
    

# if __name__ == "__main__":
# # 创建拓扑
#     topo = Topology()

#     # 添加单向链路（链路名称，起点，终点）
#     topo.add_link("link1", "A", "B")
#     topo.add_link("link2", "B", "C")
#     topo.add_link("link3", "A", "C")
#     topo.add_link("link4", "C", "D")
#     topo.add_link("link5", "D", "A")

#     # 查找路径
#     paths = topo.find_all_paths("A", "D")
#     print(paths)

#     # # 打印结果
#     # print("A -> D 的所有路径：")
#     # for i, path in enumerate(paths, 1):
#     #     print(f"路径{i}: {' → '.join(path)}")