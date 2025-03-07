import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
import sys
from collections import defaultdict
import ast
from dependency import DependencyGraph

        


def load_combined_rate_info(file_name):
    """加载合并后的速率和瓶颈流信息"""
    rate_records = []
    bottleneck_records = []
    
    # 读取速率记录
    rate_file = f"result/{file_name}/rate_record.txt"
    with open(rate_file, 'r') as f:
        for line in f:
            try:
                record = ast.literal_eval(line.strip())
                rate_records.append( (record['time'], record['flow']) )
            except:
                continue

    # 读取瓶颈流记录
    bottleneck_file = f"result/{file_name}/bottleneck_flows.txt"
    with open(bottleneck_file, 'r') as f:
        for line in f:
            try:
                record = ast.literal_eval(line.strip())
                bottleneck_records.append( (record['time'], record['bottleneck_flows']) )
            except:
                continue

    # 合并时间相近的记录（误差<1e-6秒视为同一时刻）
    combined = defaultdict(dict)
    eps = 1e-6
    for t, rates in rate_records:
        key = round(t / eps) * eps
        if 'rates' not in combined[key]:
            combined[key]['rates'] = {}
        # 逐个流更新速率
        for flow, rate in rates.items():
            combined[key]['rates'][flow] = rate  # 更新而不是覆盖

    # 修改后的瓶颈流处理（逐个流更新）    
    for t, bottlenecks in bottleneck_records:
        key = round(t / eps) * eps
        if 'bottlenecks' not in combined[key]:
            combined[key]['bottlenecks'] = {}
        # 逐个流更新瓶颈信息
        for flow, bn_list in bottlenecks.items():
            combined[key]['bottlenecks'][flow] = bn_list  # 更新而不是覆盖

    return combined

def parse_rate_records(rate_record_file, flow_time_info):
    """解析速率记录文件，返回合并后的速率时间线"""
    import ast
    from collections import defaultdict
    
    # 读取并预处理记录
    rate_events = []
    with open(rate_record_file, 'r') as f:
        for line in f:
            try:
                entry = ast.literal_eval(line.strip())
                rate_events.append((entry['time'], entry['flow']))
            except:
                continue
    
    # 按时间排序并添加终止标记
    rate_events.sort(key=lambda x: x[0])
    rate_events.append((float('inf'), {}))  # 添加终止标记

    flow_timelines = defaultdict(list)
    current_rates = {}
    last_event_time = 0

    # 遍历所有事件时间点
    for event_time, flow_changes in rate_events:
        # 处理每个流的时间区间
        for flow in list(current_rates.keys()):  # 使用list防止字典改变大小
            # 只处理生命周期内的流
            if flow not in flow_time_info:
                continue
            start_time = flow_time_info[flow]['start']
            end_time = flow_time_info[flow]['end']
            
            # 流尚未开始或已经结束
            if last_event_time >= end_time or event_time <= start_time:
                continue
            
            # 确定有效时间范围
            valid_start = max(start_time, last_event_time)
            valid_end = min(end_time, event_time)
            
            # 仅当存在有效持续时间时记录
            if valid_start < valid_end:
                # 合并相同速率的连续区间
                if flow_timelines[flow] and flow_timelines[flow][-1]['rate'] == current_rates[flow]:
                    flow_timelines[flow][-1]['end'] = valid_end
                else:
                    flow_timelines[flow].append({
                        'start': valid_start,
                        'end': valid_end,
                        'rate': current_rates[flow]
                    })
        
        # 更新当前速率
        current_rates.update(flow_changes)
        last_event_time = event_time

    # 后处理确保时间线完整性
    final_timelines = {}
    for flow, timeline in flow_timelines.items():
        if flow not in flow_time_info:
            continue
        
        # 确保覆盖完整生命周期
        start_time = flow_time_info[flow]['start']
        end_time = flow_time_info[flow]['end']
        
        # 添加初始速率（如果存在）
        if not timeline and flow in current_rates:
            timeline.append({
                'start': start_time,
                'end': end_time,
                'rate': current_rates[flow]
            })
        
        # 合并首尾区间
        if timeline:
            # 连接第一个区间
            if timeline[0]['start'] > start_time:
                timeline.insert(0, {
                    'start': start_time,
                    'end': timeline[0]['start'],
                    'rate': timeline[0]['rate']  # 继承第一个记录的速率
                })
            
            # 连接最后一个区间
            if timeline[-1]['end'] < end_time:
                timeline.append({
                    'start': timeline[-1]['end'],
                    'end': end_time,
                    'rate': timeline[-1]['rate']
                })
        
        final_timelines[flow] = timeline

    return final_timelines



# 生成示例数据（包含name字段）
def read_from_records(record_file, workload_file, standard_file):
    # 读取records.txt文件
    records = []
    with open(record_file, 'r') as file:
        for line in file:
            parts = line.strip().split(',')
            records.append({
                "type": parts[0].lower(),
                "name": parts[1],
                "event": parts[2],
                "time": float(parts[3])
            })

    # 读取json文件
    with open(workload_file, 'r') as file:
        json_data = json.load(file)

    # 处理数据
    elements = []
    dependencies = []
    name_to_id = {}
    current_id = 1

    for record in records:
        if record["event"] == "begin":
            element = {
                "id": current_id,
                "name": record["name"],
                "type": record["type"],
                "start_time": record["time"],
                "end_time": None,
                "standard_time": None
            }
            elements.append(element)
            name_to_id[record["name"]] = current_id
            current_id += 1
        elif record["event"] == "finish":
            for element in elements:
                if element["name"] == record["name"]:
                    element["end_time"] = record["time"]
                    break

    for rack_info in json_data:
        op_list = rack_info["ops"]
        for item in op_list:
            if "depends" in item:
                dependencies.append({
                    "child_id": name_to_id[item["op_name"]],
                    "parent_id": name_to_id[item["depends"]]
                })
            for element in elements:
                if element["name"] == item["op_name"]:
                    if item["op_type"] == "gpu":
                        element["standard_time"] = None
                    else:
                        with open(standard_file, 'r') as sf:
                            for line in sf.readlines()[1:]:
                                parts = line.strip().split(',')
                                flow_name = parts[0]
                                standard_time_ms = float(parts[-1])
                                if flow_name == item["op_name"]:
                                    element["standard_time"] = standard_time_ms / 1000.0
                                    break
                        

    return pd.DataFrame(elements), pd.DataFrame(dependencies)

num = int(sys.argv[1])
bandwidth = int(sys.argv[2])
route = sys.argv[3]


file_name = f"link_num_{num}_bandwidth_{bandwidth}_delay_2_route_{route}"
record_file = f"/home/denghaotian/research/LLM_planning/simulate/easy_simulate/result/{file_name}/records.txt"
workload_file = "/home/denghaotian/research/LLM_planning/simulate/easy_simulate/data/change_data.json"
standard_file = f"/home/denghaotian/research/LLM_planning/simulate/easy_simulate/result/{file_name}/standard_time.txt"
elements_df, dependencies_df = read_from_records(record_file, workload_file, standard_file)





# 解析速率记录
combined_data = load_combined_rate_info(file_name)
rate_record_file = f"/home/denghaotian/research/LLM_planning/simulate/easy_simulate/result/{file_name}/rate_record.txt"
flow_time_info = {row['name']: {'start': row['start_time'], 'end': row['end_time']} 
                  for _, row in elements_df.iterrows() if row['type'] == 'flow'}
rate_timelines = parse_rate_records(rate_record_file, flow_time_info)

# 格式化速率信息
def format_rate_info(flow_name, combined_data, flow_end_time):
    """生成带瓶颈流信息的速率描述（使用实际结束时间）"""
    # 收集所有相关时间点
    relevant_times = []
    for t in sorted(combined_data.keys()):
        if flow_name in combined_data[t].get('rates', {}):
            relevant_times.append(t)
    
    # 构建变化时间线
    timeline = []
    current_rate = None
    current_bottlenecks = []
    current_start = None
    
    for t in relevant_times:
        data = combined_data[t]
        new_rate = data['rates'][flow_name]
        new_bottlenecks = data.get('bottlenecks', {}).get(flow_name, [])
        
        # 检测变化
        if new_rate != current_rate or set(new_bottlenecks) != set(current_bottlenecks):
            if current_start is not None:
                # 记录前一个区间
                timeline.append({
                    'start': current_start,
                    'end': t,
                    'rate': current_rate,
                    'bottlenecks': current_bottlenecks
                })
            # 更新当前状态
            current_start = t
            current_rate = new_rate
            current_bottlenecks = new_bottlenecks
            
    # 处理最后一个区间
    if current_start is not None:
        timeline.append({
            'start': current_start,
            'end': flow_end_time,  # 使用实际结束时间
            'rate': current_rate,
            'bottlenecks': current_bottlenecks
        })
    
    # 生成展示信息
    info = []
    for period in timeline:
        # 计算有效时间段
        start = period['start']
        end = period['end']
        
        # 确保结束时间不早于开始时间
        if end < start:
            continue
            
        duration = end - start
        time_range = f"{start:.3f}s~{end:.3f}s"
        duration_str = f"{duration:.3f}s"
        
        # 构建条目
        line = f"{period['rate']}Gbps ({time_range}, 持续{duration_str})"
        if period['bottlenecks']:
            line += f"<br>  共享瓶颈流: {', '.join(period['bottlenecks'])}"
        info.append(line)
    
    return "<br>速率变化: " + "<br>".join(info) if info else ""

    

# def generate_sample_data():
#     elements = [
#         {"id": 1, "name": "系统启动", "type": "task", "start_time": 0, "end_time": 2, "standard_time": None},
#         {"id": 2, "name": "数据加载", "type": "flow", "start_time": 2, "end_time": 6, "standard_time": 3},
#         {"id": 3, "name": "缓存预热", "type": "flow", "start_time": 2, "end_time": 5, "standard_time": 2},
#         {"id": 4, "name": "服务注册", "type": "task", "start_time": 6, "end_time": 8, "standard_time": None},
#         {"id": 5, "name": "接口校验", "type": "flow", "start_time": 6, "end_time": 12, "standard_time": 4}
#     ]
    
#     dependencies = [
#         {"child_id": 2, "parent_id": 1},
#         {"child_id": 3, "parent_id": 1},
#         {"child_id": 4, "parent_id": 2},
#         {"child_id": 5, "parent_id": 3}
#     ]
#     return pd.DataFrame(elements), pd.DataFrame(dependencies)

# # 加载数据
# elements_df, dependencies_df = generate_sample_data()

# 核心参数配置
TIME_MAGNIFIER = 10000  # 0.01秒对应50像素 (0.01 * 5000=50)
BASE_Y_SPACING = 300    # 垂直基础间距
CHART_WIDTH = 20000    # 图表总宽度

# 生成紧凑的Y轴布局
def generate_compact_y_layout():
    layout = {}
    y_pos = 0
    
    # 按开始时间排序
    sorted_elements = elements_df.sort_values("start_time")
    
    # 为每个元素分配Y坐标
    current_window_start = 0
    for _, row in sorted_elements.iterrows():
        if row["start_time"] >= current_window_start + 0.01:
            current_window_start += 0.01
            y_pos = 0  # 重置y_pos到窗口内的起始位置
        layout[row["id"]] = y_pos
        y_pos += BASE_Y_SPACING  # 每个元素在窗口内的间隔为100
        
        graph = DependencyGraph(workload_file )
        
        numbered_dp_list = graph.get_numbered_dp_list()
        if row["name"] in numbered_dp_list:
            layout[row["id"]] += numbered_dp_list[row["name"]] *   BASE_Y_SPACING
        
    
    return layout

y_coordinates = generate_compact_y_layout()

# 准备线段数据（带颜色分级）
def prepare_segment_lines():
    color_levels = [
        (0.0, 0.5, 'darkblue', '<0.5x'),
        (0.5, 1.05, 'blue', '0.5-1.0x'),
        (1.05, 1.5, 'orange', '1.0-1.5x'),
        (1.5, 2.0, 'red', '1.5-2.0x'),
        (2.0, float('inf'), 'darkred', '>2.0x')
    ]
    
    line_groups = {'task': {'x': [], 'y': [], 'color': 'black', 'label': 'Task依赖'}}
    for low, high, color, label in color_levels:
        line_groups[label] = {'x': [], 'y': [], 'color': color, 'label': label}

    for _, dep in dependencies_df.iterrows():
        parent = elements_df[elements_df["id"] == dep["parent_id"]].iloc[0]
        child = elements_df[elements_df["id"] == dep["child_id"]].iloc[0]
        
        # 应用时间放大
        x = [
            parent["start_time"] * TIME_MAGNIFIER,
            child["start_time"] * TIME_MAGNIFIER,
            None
        ]
        y = [
            y_coordinates[parent["id"]],
            y_coordinates[child["id"]],
            None
        ]
        
        # 确定颜色组
        if parent["type"] == "task":
            group = 'task'
        else:
            ratio = (parent["end_time"] - parent["start_time"]) / parent["standard_time"]
            for low, high, color, label in color_levels:
                if low <= ratio < high:
                    group = label
                    break
        
        line_groups[group]['x'].extend(x)
        line_groups[group]['y'].extend(y)
    
    return line_groups

line_groups = prepare_segment_lines()

# 创建超长图表
fig = go.Figure()

# 添加线段（带图例）
legend_added = set()
for group, data in line_groups.items():
    if len(data['x']) > 0 and data['label'] not in legend_added:
        fig.add_trace(go.Scatter(
            x=data['x'],
            y=data['y'],
            mode="lines",
            line=dict(color=data['color'], width=1.5),
            name=data['label'],
            legendgroup=group,
            showlegend=True,
            hoverinfo="none"
        ))
        legend_added.add(data['label'])

# 生成节点信息
elements_df["x_plot"] = elements_df["start_time"] * TIME_MAGNIFIER

flow_end_times = {row['name']: row['end_time'] for _, row in elements_df.iterrows() if row['type'] == 'flow'}
elements_df['rate_info'] = elements_df.apply(
    lambda r: format_rate_info(r['name'], combined_data, flow_end_times.get(r['name'], None)) 
    if r['type'] == 'flow' else "", 
    axis=1
)
# 自定义悬浮提示
hover_template = (
    "<b>%{customdata[0]}</b><br>"
    "类型: %{customdata[1]}<br>"
    "开始: %{customdata[2]:.6f}s<br>"
    "结束: %{customdata[3]:.6f}s"
    "%{customdata[4]}"  # 原有标准时间信息
    "%{customdata[5]}"   # 新增速率和瓶颈流信息
    "<extra></extra>"
)
# # 添加节点
# fig.add_trace(go.Scatter(
#     x=elements_df["x_plot"],
#     y=[y_coordinates[id] for id in elements_df["id"]],
#     mode="markers+text",
#     text=elements_df["id"],
#     textposition="top center",
#     marker=dict(
#         size=10,
#         color=elements_df["type"].map({"task": "#FF6347", "flow": "#1E90FF"}),
#         line=dict(width=1, color="black")
#     ),
#     textfont=dict(size=10, color="black"),
#     customdata=elements_df.apply(lambda r: [
#         r['name'],
#         'flow' if r['type'] == 'task' else 'task',
#         r['start_time'],
#         r['end_time'],
#         f"<br>标准时间: {r['standard_time']:.6f}s" if r['type'] == 'flow' else ""
#     ], axis=1),
#     hovertemplate=hover_template,
#     showlegend=False
# ))


# ------------------------ 节点颜色配置 ------------------------
COLOR_CONFIG = {
    "flow": {
        "default": "#7EB24D",      # 常规流程
        "special": "#2F528F"       # 包含F999的特殊流程
    },
    "task": {
        "F_start": "#4B9CD3",      # 以F开头的任务
        "B_start": "#36B3A8",      # 以B开头的任务
        "default": "#8FD6E3"       # 其他任务
    }
}

# ------------------------ 节点绘制部分 ------------------------
# Task节点（分三个系列）
task_f = elements_df[(elements_df["type"] == "task") & (elements_df['name'].str.startswith('F'))]
task_b = elements_df[(elements_df["type"] == "task") & (elements_df['name'].str.startswith('B'))]
task_other = elements_df[(elements_df["type"] == "task") & (~elements_df['name'].str.startswith(('F', 'B')))]

# Flow节点（分两个系列）
flow_special = elements_df[(elements_df["type"] == "flow") & (elements_df['name'].str.contains('F999'))]
flow_normal = elements_df[(elements_df["type"] == "flow") & (~elements_df['name'].str.contains('F999'))]

# 绘制F开头的任务节点（绿色方块）
if not task_f.empty:
    fig.add_trace(go.Scatter(
        x=task_f["x_plot"],
        y=[y_coordinates[id] for id in task_f["id"]],
        mode="markers+text",
        text=task_f["id"],
        textposition="top center",
        marker=dict(
            symbol="square",
            size=12,
            color=COLOR_CONFIG["task"]["F_start"],
            line=dict(width=1.5, color="black")
        ),
        # 保持原有customdata和hovertemplate配置
        customdata=task_f.apply(lambda r: [r['name'], '任务', r['start_time'], r['end_time'], ""], axis=1),
        hovertemplate=hover_template,
        showlegend=False
    ))

# 绘制B开头的任务节点（橙色方块）
if not task_b.empty:
    fig.add_trace(go.Scatter(
        x=task_b["x_plot"],
        y=[y_coordinates[id] for id in task_b["id"]],
        mode="markers+text",
        text=task_b["id"],
        textposition="top center", 
        marker=dict(
            symbol="square",
            size=12,
            color=COLOR_CONFIG["task"]["B_start"],
            line=dict(width=1.5, color="black")
        ),
        customdata=task_b.apply(lambda r: [r['name'], '任务', r['start_time'], r['end_time'], ""], axis=1),
        hovertemplate=hover_template,
        showlegend=False
    ))

# 绘制其他任务节点（红色方块）
if not task_other.empty:
    fig.add_trace(go.Scatter(
        x=task_other["x_plot"],
        y=[y_coordinates[id] for id in task_other["id"]],
        mode="markers+text",
        text=task_other["id"],
        textposition="top center",
        marker=dict(
            symbol="square",
            size=12,
            color=COLOR_CONFIG["task"]["default"],
            line=dict(width=1.5, color="black")
        ),
        customdata=task_other.apply(lambda r: [r['name'], '任务', r['start_time'], r['end_time'], ""], axis=1),
        hovertemplate=hover_template,
        showlegend=False
    ))

# 绘制特殊流程节点（粉色圆形）
if not flow_special.empty:
    fig.add_trace(go.Scatter(
        x=flow_special["x_plot"],
        y=[y_coordinates[id] for id in flow_special["id"]],
        mode="markers+text",
        text=flow_special["id"],
        textposition="top center",
        marker=dict(
            symbol="circle",
            size=10,
            color=COLOR_CONFIG["flow"]["special"],
            line=dict(width=1, color="black")
        ),
        customdata=flow_special.apply(lambda r: [
            r['name'],
            '流程', 
            r['start_time'],
            r['end_time'],
            f"<br>标准时间: {r['standard_time']:.6f}s" if pd.notnull(r['standard_time']) else "",
            r['rate_info']  # 新增速率信息
        ], axis=1),
        hovertemplate=hover_template,
        showlegend=False
    ))

# 绘制常规流程节点（蓝色圆形）
if not flow_normal.empty:
    fig.add_trace(go.Scatter(
        x=flow_normal["x_plot"],
        y=[y_coordinates[id] for id in flow_normal["id"]],
        mode="markers+text",
        text=flow_normal["id"],
        textposition="top center",
        marker=dict(
            symbol="circle",
            size=10,
            color=COLOR_CONFIG["flow"]["default"],
            line=dict(width=1, color="black")
        ),
        customdata=flow_normal.apply(lambda r: [
            r['name'],
            '流程', 
            r['start_time'],
            r['end_time'],
            f"<br>标准时间: {r['standard_time']:.6f}s" if pd.notnull(r['standard_time']) else "",
            r['rate_info']  # 新增第五个元素
        ], axis=1),
        hovertemplate=hover_template,
        showlegend=False
    ))


max_time = max(elements_df["end_time"].max(), elements_df["start_time"].max())
max_x = max_time * TIME_MAGNIFIER

# 动态生成刻度
tick_interval = 50  # 每50像素一个刻度
tickvals = np.arange(0, max_x + tick_interval, tick_interval)
ticktext = [f"{x/TIME_MAGNIFIER:.4f}" for x in tickvals]

# 配置图表布局
fig.update_layout(
    plot_bgcolor="white",
    xaxis=dict(
        title="时间轴（秒）",
        tickvals=tickvals,  # 每50像素一个刻度
        ticktext=ticktext,
        gridcolor="rgba(200,200,200,0.3)",
        zeroline=False,
        fixedrange=False,
        rangeslider=dict(visible=True)  # 添加范围滑块
    ),
    yaxis=dict(
        showticklabels=False,
        showgrid=False,
        zeroline=False,
        fixedrange=True
    ),
    legend=dict(
        title="流程时间比例",
        x=1.02,
        y=1,
        bordercolor="#999",
        borderwidth=1
    ),
    width=CHART_WIDTH,
    height=1200,
    margin=dict(l=20, r=200, t=20, b=40),
    hoverlabel=dict(
        bgcolor="white",
        font_size=12,
        font_family="Arial"
    )
)

# 保存为可滚动HTML
fig.write_html(f"result/{file_name}/{file_name}_ultra_wide_visualization.html", include_plotlyjs='cdn', auto_open=False)