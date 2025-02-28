from simulator import *
from Topology import *
import json
import random
import sys



def set_16_rank_topo(simulator, topo, num, bandwidth, delay):
    link_id = 1
    link_dict = {}
    # host->leaf
    for i in range(8):
        topo.add_link(f"link{link_id}", str(i), "16")
        simulator.add_link(f"link{link_id}", 200, 0.05)
        link_dict[f"link{link_id}"] = (str(i), "16")
        link_id += 1
        topo.add_link(f"link{link_id}", "16", str(i))
        simulator.add_link(f"link{link_id}", 200, 0.05)
        link_dict[f"link{link_id}"] = ("16", str(i))
        link_id += 1
    for i in range(8):
        topo.add_link(f"link{link_id}", str(8 + i), "17")
        simulator.add_link(f"link{link_id}", 200, 0.05)
        link_dict[f"link{link_id}"] = (str(8 + i), "17")
        link_id += 1
        topo.add_link(f"link{link_id}", "17", str(8 + i))
        simulator.add_link(f"link{link_id}", 200, 0.05)
        link_dict[f"link{link_id}"] = ("17", str(8 + i))
        link_id += 1

    # leaf->spine
    for i in range(4):
        topo.add_link(f"link{link_id}", "16", "18")
        simulator.add_link(f"link{link_id}", 400, 0.05)
        link_dict[f"link{link_id}"] = ("16", "18")
        link_id += 1
        topo.add_link(f"link{link_id}", "18", "16")
        simulator.add_link(f"link{link_id}", 400, 0.05)
        link_dict[f"link{link_id}"] = ("18", "16")
        link_id += 1
        topo.add_link(f"link{link_id}", "17", "19")
        simulator.add_link(f"link{link_id}", 400, 0.05)
        link_dict[f"link{link_id}"] = ("17", "19")
        link_id += 1
        topo.add_link(f"link{link_id}", "19", "17")
        simulator.add_link(f"link{link_id}", 400, 0.05)
        link_dict[f"link{link_id}"] = ("19", "17")
        link_id += 1
    
    # spine->core
    for i in range(4):
        topo.add_link(f"link{link_id}", "18", "20")
        simulator.add_link(f"link{link_id}", 400, 0.05)
        link_dict[f"link{link_id}"] = ("18", "20")
        link_id += 1
        topo.add_link(f"link{link_id}", "20", "18")
        simulator.add_link(f"link{link_id}", 400, 0.05)
        link_dict[f"link{link_id}"] = ("20", "18")
        link_id += 1
        topo.add_link(f"link{link_id}", "19", "21")
        simulator.add_link(f"link{link_id}", 400, 0.05)
        link_dict[f"link{link_id}"] = ("19", "21")
        link_id += 1
        topo.add_link(f"link{link_id}", "21", "19")
        simulator.add_link(f"link{link_id}", 400, 0.05)
        link_dict[f"link{link_id}"] = ("21", "19")
        link_id += 1
    
    # core->core
    for i in range(num):
        topo.add_link(f"link{link_id}", "20", "21")
        simulator.add_link(f"link{link_id}", bandwidth, delay)
        link_dict[f"link{link_id}"] = ("20", "21")
        with open(f"{file_name}_core_links.txt", "a") as file:
            file.write(f"link{link_id}\n")
        link_id += 1
        topo.add_link(f"link{link_id}", "21", "20")
        simulator.add_link(f"link{link_id}", bandwidth, delay)
        link_dict[f"link{link_id}"] = ("21", "20")
        with open(f"{file_name}_core_links.txt", "a") as file:
            file.write(f"link{link_id}\n")
        link_id += 1
    
    return link_dict
    
    


if __name__ == "__main__":
    # 清空 link_load.txt 和 records.txt
    if len(sys.argv) != 3:
        print("Usage: python 16-rack-simulate.py <num> <bandwidth>")
        sys.exit(1)
    
    num = int(sys.argv[1])
    bandwidth = int(sys.argv[2])
    delay = 2
    file_name = f"link_num_{num}_bandwidth_{bandwidth}_delay_{delay}"
    open(f'{file_name}_link_load.txt', 'w').close()
    open(f'{file_name}_link_util.txt', 'w').close()
    open(f'{file_name}_records.txt', 'w').close()
    open(f'{file_name}_rate_record.txt', 'w').close()
    open(f'{file_name}_flow_path_record.txt', 'w').close()
    open(f'{file_name}_core_links.txt', 'w').close()
    
    # 创建仿真器
    simulator = Simulator(file_name)
    topo = Topology()
    link_dict = set_16_rank_topo(simulator, topo, num, bandwidth, delay)
    # 添加流
    workload_file = "/home/denghaotian/research/LLM_planning/data/workload_16_PP4_DP4_TP1_VPP2_BATCH8_NO_PRI.json"
    with open(workload_file, 'r') as f:
        workload = json.load(f)
        
    task_num = 0
    flow_num = 0
    
    for i in range(len(workload)):
        op_list = workload[i]['ops']
        for op in op_list:
            if op["op_type"] == "gpu":
                if "depends" in op:
                    if op["depends"] != "":
                        simulator.add_task(op["op_name"], op["duration"] / 1000, dependency = op["depends"])
                    else:
                        simulator.add_task(op["op_name"], op["duration"] / 1000, dependency=None)
                else:
                    simulator.add_task(op["op_name"], op["duration"] / 1000, dependency=None)
                task_num += 1
            elif op["op_type"] == "send":
                flow_path_list = topo.find_all_paths(str(op["src_rank"]), str(op["dst_rank"]))
                flow_name_path = random.choice(flow_path_list)
                with open(f"{file_name}_flow_path_record.txt", "a") as file:
                    flow_id = op["op_name"]
                    # path_nodes = []
                    # for link_name in flow_name_path:
                    #     src, dst = link_dict[link_name]
                    #     if not path_nodes:
                    #         path_nodes.append(src)
                    #     path_nodes.append(dst)
                    file.write(f"{flow_id}: {flow_name_path}\n")
                    
                flow_path = []
                for link_name in flow_name_path:
                    flow_path.append(simulator.links[link_name])
                if "depends" in op:
                    if op["depends"] != "":
                        simulator.add_flow(op["op_name"], op["size"], flow_path, dependency=op["depends"])
                    else:
                        simulator.add_flow(op["op_name"], op["size"], flow_path, dependency=None)
                else:
                    simulator.add_flow(op["op_name"], op["size"], flow_path, dependency=None)
                flow_num += 1
    simulator.run()
    print(f"task_num: {task_num}, flow_num: {flow_num}, total_num: {task_num + flow_num}")
    # 读取 records.txt，并且print最后一行
                    
            
    
   