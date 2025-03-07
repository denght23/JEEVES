from simulator import *
from Topology import *
import json
import random
import sys
import os


def calculate_flow_standard_time(flow_id, flow_name_path, simulator, standard_file):
    latency = 0 #ms
    bandwidth = 400 #Gbps
    for link_name in flow_name_path:
        link = simulator.links[link_name]
        latency += link.delay
        link_bandwidth = link.bandwidth
        if link_bandwidth < bandwidth:
            bandwidth = link_bandwidth
    flow_size = simulator.flows[flow_id].size #MB
    standard_time = flow_size / bandwidth * 8 + latency
    with open(standard_file, "a") as file:
        file.write(f"{flow_id},{latency},{bandwidth},{flow_size},{standard_time}\n")

def set_16_rank_topo(simulator, topo, num, bandwidth, delay, core_links_file):
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
        with open(core_links_file, "a") as file:
            file.write(f"link{link_id}\n")
        link_id += 1
        topo.add_link(f"link{link_id}", "21", "20")
        simulator.add_link(f"link{link_id}", bandwidth, delay)
        link_dict[f"link{link_id}"] = ("21", "20")
        with open(core_links_file, "a") as file:
            file.write(f"link{link_id}\n")
        link_id += 1
    
    return link_dict
    
    


if __name__ == "__main__":
    # 清空 link_load.txt 和 records.txt
    if len(sys.argv) != 4:
        print("Usage: python 16-rack-simulate.py <num> <bandwidth> <random/min_max_flows>")
        sys.exit(1)
    
    num = int(sys.argv[1])
    bandwidth = int(sys.argv[2])
    delay = 2
    # path_selection_method ='random'#random or min_max_flows
    path_selection_method = sys.argv[3] #random or min_max_flows
    file_name = f"link_num_{num}_bandwidth_{bandwidth}_delay_{delay}_route_{path_selection_method}" 
    # 创建文件夹
    os.makedirs(f"result/{file_name}", exist_ok=True)
    
    
    
    link_load_file = f'result/{file_name}/link_load.txt'
    link_util_file = f'result/{file_name}/link_util.txt'
    records_file = f'result/{file_name}/records.txt'
    rate_record_file = f'result/{file_name}/rate_record.txt'
    flow_path_record_file = f'result/{file_name}/flow_path_record.txt'
    core_links_file = f'result/{file_name}/core_links.txt'
    standard_time_file = f'result/{file_name}/standard_time.txt'
    error_file = f'result/{file_name}/error.txt'
    
    open(link_load_file, 'w').close()
    open(link_util_file, 'w').close()
    open(records_file, 'w').close()
    open(rate_record_file, 'w').close()
    open(flow_path_record_file, 'w').close()
    open(core_links_file, 'w').close()
    open(error_file, 'w').close()
    
    with open(standard_time_file, 'w') as file:
        file.write("flow_id,path_latency(ms),bandwidth(Gbps),flow_size(MB),standard_time(ms)\n")
    
    # 创建仿真器
    simulator = Simulator(file_name, path_selection_method)
    topo = Topology()
    link_dict = set_16_rank_topo(simulator, topo, num, bandwidth, delay, core_links_file)
    # 添加流
    workload_file = "/home/denghaotian/research/LLM_planning/simulate/easy_simulate/data/change_data.json"
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
                # # flow_name_path = random.choice(flow_path_list)
                # with open(flow_path_record_file, "a") as file:
                #     flow_id = op["op_name"]
                #     file.write(f"{flow_id}: {flow_name_path}\n")
                # flow_path = []
                # for link_name in flow_name_path:
                #     flow_path.append(simulator.links[link_name])
                flow_paths = []
                flow_id = op["op_name"]
                for path in flow_path_list:
                    entry = []
                    for link_name in path:
                        entry.append(simulator.links[link_name])
                    flow_paths.append(entry)
                # print(f"flow_paths: {flow_paths}")
                if "depends" in op:
                    if op["depends"] != "":
                        simulator.add_flow(op["op_name"], op["size"], flow_paths, dependency=op["depends"])
                    else:
                        simulator.add_flow(op["op_name"], op["size"], flow_paths, dependency=None)
                else:
                    simulator.add_flow(op["op_name"], op["size"], flow_paths, dependency=None)
                flow_name_path = random.choice(flow_path_list)
                calculate_flow_standard_time(flow_id, flow_name_path, simulator, standard_time_file)
                flow_num += 1
    simulator.run()
    print(f"task_num: {task_num}, flow_num: {flow_num}, total_num: {task_num + flow_num}")
    # 读取 records.txt，并且print最后一行
                    
            
    
   