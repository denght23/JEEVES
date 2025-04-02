import json
import re
import plotly.graph_objects as go

# 配置参数
DC_INTERNAL_BW = 200  # Gbps
DC_EXTERNAL_BW = 200  # Gbps
RANK_THRESHOLD = 8  # DC分界点

# 读取数据
with open('../data/change_data.json', 'r') as f:
    data = json.load(f)

# 构建事件字典
events = {}
for rank in data:
    for op in rank['ops']:
        if op['op_type'] !='recv':
            events[op['op_name']] = op
            
depends_events = {}
for rank in data:
    for op in rank['ops']:
        if op['op_type'] =='recv':
            continue
        if op['op_name'] not in depends_events:
            depends_events[op['op_name']] = []
        if op.get('depends') and op['depends'] != '':
            if op['depends'] not in depends_events:
                depends_events[op['depends']] = []
            depends_events[op['depends']].append(op['op_name'])
                

# 处理依赖关系和事件时间
event_times = {}

def calculate_time(op_name):
    """递归计算事件时间"""
    if op_name in event_times:
        return
    
    op = events[op_name]
    start_time = 0
    
    # 处理依赖
    if op.get('depends') and op['depends'] in events:
        dep_op = op['depends']
        if dep_op not in event_times:
            calculate_time(dep_op)
        start_time = event_times[dep_op]['end']
    
    # 计算结束时间
    if op['op_type'] == 'gpu':
        end_time = start_time + op['duration']
    else:
        # 解析rank信息
        match = re.search(r'_Rank(\d+)_Rank(\d+)$', op_name)
        if not match:
            return
        e, f = map(int, match.groups())
        
        # 确定带宽
        same_dc = (e < RANK_THRESHOLD and f < RANK_THRESHOLD) or \
                 (e >= RANK_THRESHOLD and f >= RANK_THRESHOLD)
        bw = DC_INTERNAL_BW if same_dc else DC_EXTERNAL_BW
        
        # 计算传输时间
        end_time = start_time + (op['size'] * 8) / bw  # 单位: ms
    
    event_times[op_name] = {'start': start_time, 'end': end_time}

# 处理所有8个流
streams = []
for num in range(1, 9):
    path = []
    current_name = f"F{num}a_DP0_PP0_TP0_Rank0"
    end_pattern = f"B{num}a_DP0_PP0_TP0_Rank0"
    
    if current_name not in events:
        continue
    
    current_op = events[current_name]
    expected_type = 'send'
    
    while True:
        path.append(current_op)
        if end_pattern == current_op['op_name']:
            break
        
        # 查找下一个事件
        next_ops = []
        for op_name in depends_events.get(current_op['op_name']):
            op = events.get(op_name)
            if op.get('op_name').startswith('B') and current_op.get('op_name').startswith('F'):   #前向和后向的转折点会出现两个连续的计算事件
                expected_type = 'gpu'
            if op.get('op_type') == expected_type:
                next_ops.append(op)
                break
        
        if not next_ops:
            break
        
        current_op = next_ops[0]
        expected_type = 'gpu' if expected_type == 'send' else 'send'
    
    # 计算路径时间
    for op in path:
        if op['op_name'] not in event_times:
            calculate_time(op['op_name'])
    
    streams.append(path)


# 创建可视化
fig = go.Figure()
colors = {
    'gpu': '#dddddd',         
    'same_dc': '#DDDDDD',     # 深蓝
    'cross_dc_f': '#D32F2F',  # 鲜亮绿（前向）
    'cross_dc_b': '#1976D2'   # 鲜亮橙（反向）
}

y_height = {
    'gpu': 0.4,
    'same_dc': 0.6,
    'cross_dc_f': 1.2,
    'cross_dc_b': 1.2
}
print("cal is finished!")
all_shapes = []  # 临时存储所有 shape

for stream_num, path in enumerate(streams, 1):
    y_center = stream_num
    for op in path:
        if op['op_name'] not in event_times:
            continue
        y0 = y_center
        y1 = y_center
        # 确定颜色
        if op['op_type'] == 'gpu':
            color = colors['gpu']
            y0 -= y_height['gpu'] / 2
            y1 += y_height['gpu'] / 2
            
        else:
            direction = 'f' if 'DATA_F' in op['op_name'] else 'b'
            match = re.search(r'_Rank(\d+)_Rank(\d+)$', op['op_name'])
            e, f = map(int, match.groups())
            same_dc = (e < RANK_THRESHOLD and f < RANK_THRESHOLD) or \
                      (e >= RANK_THRESHOLD and f >= RANK_THRESHOLD)
            if same_dc:
                color = colors['same_dc']
                y0 -= y_height['same_dc'] / 2
                y1 += y_height['same_dc'] / 2

            else:
                color = colors[f'cross_dc_{direction}']
                y0 -= y_height[f'cross_dc_{direction}'] / 2
                y1 += y_height[f'cross_dc_{direction}'] / 2

        # 构造 shape 对象
        shape = dict(
            type="rect",
            x0=event_times[op['op_name']]['start'],
            x1=event_times[op['op_name']]['end'],
            y0=y0,
            y1=y1,
            fillcolor=color,
            line=dict(width=0)
        )
        all_shapes.append(shape)
    print(f"finish {stream_num} path!")

# 一次性添加 shapes
# fig.update_layout(shapes=all_shapes)
print("shape is finished!")

# 设置坐标轴和背景
max_time = max([e['end'] for e in event_times.values()], default=0)
fig.update_layout(
    plot_bgcolor='white',
    yaxis=dict(
        title="Stream Number",
        tickvals=list(range(1, 17)),
        range=[0.5, 16.5],
        showgrid=True,
        gridcolor='lightgrey'
    ),
    xaxis=dict(
        title="Time (ms)",
        showgrid=True,
        gridcolor='lightgrey',
        range=[0, max_time * 1.05]
    ),
    height=1600,
    showlegend=False
)
print("plot is finished!")
# # 添加网格线
# for x in range(0, int(max_time)+100, 100):
#     fig.add_vline(x=x, line=dict(color="lightgrey", width=0.5))

vline_shapes = []
for x in range(0, int(max_time)+100, 1000):
    vline_shapes.append(dict(
        type="line",
        x0=x, x1=x,
        y0=0, y1=len(streams)+1,  # Y 轴覆盖所有 path
        line=dict(color="lightgrey", width=0.5),
        layer="below"  # 放到图像下方
    ))

# 添加到已有 shapes（如果前面已经生成 all_shapes）
fig.update_layout(shapes=(all_shapes + vline_shapes))


fig.write_html("timeline_16_rack.html")
print("可视化已保存到 timeline.html")