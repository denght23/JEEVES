from simulator import *
from Topology import *
import json
import ijson
import random
import sys
import os
from datetime import datetime
import pandas as pd


def calculate_flow_standard_time(flow_id, flow_name_path, simulator, standard_file):
    latency = 0  # ms
    bandwidth = 400  # Gbps
    for link_name in flow_name_path:
        link = simulator.links[link_name]
        latency += link.delay
        link_bandwidth = link.bandwidth
        if link_bandwidth < bandwidth:
            bandwidth = link_bandwidth
    flow_size = simulator.flows[flow_id].size  # MB
    standard_time = flow_size / bandwidth * 8 + latency
    with open(standard_file, "a") as file:
        file.write(f"{flow_id},{latency},{bandwidth},{flow_size},{standard_time}\n")


def set_1024_rank_topo(simulator, topo, num, bandwidth, delay, core_links_file):
    link_id = 1
    link_dict = {}
    # 读取link_list.csv文件，最后四行跨DC链路不读取，手动设置，原始数据为2 * 100Gbps
    link_file = pd.read_csv(
        "./data_1024_rack/link_list.csv", skipfooter=4, engine="python"
    )
    for _, row in link_file.iterrows():
        start_node = row["a_node_id"]
        end_node = row["z_node_id"]
        link_name = f"link{link_id}"
        bandwidth = row["bw(GBps)"] * 8  # 数据给的是GBps，转换成Gbps
        link_delay = row["delay(ms)"]
        topo.add_link(
            link_name, str(start_node), str(end_node)
        )  # 数据表里面有双向数据，这里添加单向即可
        simulator.add_link(link_name, bandwidth, link_delay)
        link_dict[link_name] = (str(start_node), str(end_node))
        link_id += 1

    # 手动设置跨DC链路，原始数据为2 * 100Gbps, 节点分别为 1060, 1061, delay=2ms
    for i in range(num):
        topo.add_link(f"link{link_id}", "1060", "1061")
        simulator.add_link(f"link{link_id}", bandwidth, delay)
        link_dict[f"link{link_id}"] = ("1060", "1061")
        with open(core_links_file, "a") as file:
            file.write(f"link{link_id}\n")
        link_id += 1
        topo.add_link(f"link{link_id}", "1061", "1060")
        simulator.add_link(f"link{link_id}", bandwidth, delay)
        link_dict[f"link{link_id}"] = ("1061", "1060")
        with open(core_links_file, "a") as file:
            file.write(f"link{link_id}\n")
        link_id += 1
    return link_dict


if __name__ == "__main__":
    # 记录模拟开始的现实时间戳
    start_time = datetime.now()
    # 清空 link_load.txt 和 records.txt
    if len(sys.argv) != 4:
        print(
            "Usage: python 1024-rack-simulate.py <num> <bandwidth> <random/min_max_flows>"
        )
        sys.exit(1)

    num = int(sys.argv[1])
    bandwidth = int(sys.argv[2])
    delay = 2
    # path_selection_method ='random'#random or min_max_flows
    path_selection_method = sys.argv[3]  # random or min_max_flows
    file_name = f"link_num_{num}_bandwidth_{bandwidth}_delay_{delay}_route_{path_selection_method}"
    # 创建文件夹
    os.makedirs(f"result_1024_rack/{file_name}", exist_ok=True)

    link_load_file = f"result_1024_rack/{file_name}/link_load.txt"
    link_util_file = f"result_1024_rack/{file_name}/link_util.txt"
    link_flow_num_file = f"result_1024_rack/{file_name}/link_flow_num.txt"
    records_file = f"result_1024_rack/{file_name}/records.txt"
    rate_record_file = f"result_1024_rack/{file_name}/rate_record.txt"
    flow_path_record_file = f"result_1024_rack/{file_name}/flow_path_record.txt"
    core_links_file = f"result_1024_rack/{file_name}/core_links.txt"
    standard_time_file = f"result_1024_rack/{file_name}/standard_time.txt"
    error_file = f"result_1024_rack/{file_name}/error.txt"
    bottleneck_file = f"result_1024_rack/{file_name}/bottleneck_flows.txt"
    simulate_time_file = f"result_1024_rack/{file_name}/simulate_time.txt"

    open(link_load_file, "w").close()
    open(link_util_file, "w").close()
    open(link_flow_num_file, "w").close()
    open(records_file, "w").close()
    open(rate_record_file, "w").close()
    open(flow_path_record_file, "w").close()
    open(core_links_file, "w").close()
    open(error_file, "w").close()
    open(bottleneck_file, "w").close()

    with open(standard_time_file, "w") as file:
        file.write(
            "flow_id,path_latency(ms),bandwidth(Gbps),flow_size(MB),standard_time(ms)\n"
        )

    # 创建仿真器
    simulator = Simulator(file_name, path_selection_method)
    topo = Topology()
    link_dict = set_1024_rank_topo(
        simulator, topo, num, bandwidth, delay, core_links_file
    )
    # 添加流
    workload_file = "./data/change_data_1024_rack.json"
    # with open(workload_file, "r") as f:
    #     workload = json.load(f)
    # 在服务器上无法一次性读取这么大的文件，内存不足，换成ijson

    task_num = 0
    flow_num = 0
    with open(workload_file,"r") as f:
        for workload in ijson.items(f, ''):
            op_list = workload["ops"]
            for op in op_list:
                if op["op_type"] == "gpu":
                    if "depends" in op:
                        if op["depends"] != "":
                            if op["depends"].startswith("DATA"):
                                dependency = ["flow_end_" + op["depends"]]
                            else:
                                dependency = ["task_end_" + op["depends"]]
                            simulator.add_task(
                                op["op_name"], op["duration"] / 1000, dependency=dependency
                            )
                        else:
                            simulator.add_task(
                                op["op_name"], op["duration"] / 1000, dependency=None
                            )
                    else:
                        simulator.add_task(
                            op["op_name"], op["duration"] / 1000, dependency=None
                        )
                    task_num += 1
                elif op["op_type"] == "send":
                    flow_path_list = topo.find_all_paths(
                        str(op["src_rank"]), str(op["dst_rank"])
                    )
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
                            if op["depends"].startswith("DATA"):
                                dependency = ["flow_end_" + op["depends"]]
                            else:
                                dependency = ["task_end_" + op["depends"]]
                            simulator.add_flow(
                                op["op_name"], op["size"], flow_paths, dependency=dependency
                            )
                        else:
                            simulator.add_flow(
                                op["op_name"], op["size"], flow_paths, dependency=None
                            )
                    else:
                        simulator.add_flow(
                            op["op_name"], op["size"], flow_paths, dependency=None
                        )
                    print(flow_path_list)
                    flow_name_path = random.choice(flow_path_list)
                    calculate_flow_standard_time(
                        flow_id, flow_name_path, simulator, standard_time_file
                    )
                    flow_num += 1
    simulator.run()

    # 记录模拟结束的现实时间戳并写入文件
    end_time = datetime.now()
    with open(simulate_time_file, "a") as file:
        file.write(f"仿真耗时:{end_time - start_time}\n")

    print(
        f"task_num: {task_num}, flow_num: {flow_num}, total_num: {task_num + flow_num}"
    )
    # 读取 records.txt，并且print最后一行
