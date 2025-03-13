## 可视化文件说明
- `read_finish.py` 生成 `finish_time_plot.png`
- `show_finish.sh` 生成 `scatter_plot.png`
- `visual.sh` 生成 `link_num_4_bandwidth_400_delay_2_route_random_ultra_wide_visualization.html`这类文件


# 更新日志

## [日期: 2025-03-07]
### 修复
- 修复了流的 `remaining size` 会小于 0 的问题。
    - 由于传播时延的存在，更新速率的时候，可能此时 `remaining size` 为 0，但是流还未结束，原来未考虑到这一点，会导致 `remaining size` 小于 0，因此错误计算剩余所需的时间。
## [日期: 2025-03-07]
### 新增
- 增加了 `read_finish.py` 对照两种路由方式的结果。