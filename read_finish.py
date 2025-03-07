import os
import re

import matplotlib.pyplot as plt

def extract_value_from_line(line):
    return float(line.strip().split(',')[-1])

def process_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
        if lines:
            return extract_value_from_line(lines[-1])
    return None

def main():
    directory = '/home/denghaotian/research/LLM_planning/simulate/easy_simulate/'
    routes = ["random", "min_max_flows"]
    filenames_template = [
        'result/link_num_4_bandwidth_400_delay_2_route_{route}/records.txt',
        'result/link_num_4_bandwidth_25_delay_2_route_{route}/records.txt',
        'result/link_num_4_bandwidth_10_delay_2_route_{route}/records.txt',
        'result/link_num_2_bandwidth_10_delay_2_route_{route}/records.txt',
        'result/link_num_1_bandwidth_10_delay_2_route_{route}/records.txt',
    ]
    x_values = [1, 2, 3, 4, 5]  # Manually specified x-coordinates

    for route in routes:
        y_values = []
        for filename_template in filenames_template:
            filename = filename_template.format(route=route)
            value = process_file(os.path.join(directory, filename))
            if value is not None:
                y_values.append(value)

        plt.plot(x_values, y_values, marker='o', label=f'Route {route}')

    plt.xticks(x_values, ['1:1', '16:1', '40:1', "80:1", "160:1"])  # Manually specified x-tick labels
    plt.xlabel('Computed X Value')
    plt.ylabel('Finish Time')
    plt.title('Finish Time vs. Computed X Value for Different Routes')
    plt.legend()
    plt.grid(True)
    plt.savefig('finish_time_plot.png')

if __name__ == "__main__":
    main()