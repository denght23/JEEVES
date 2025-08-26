b = 1
s = 2048
h = 12288
a = 96
l = 96

# FP16, 每个microbatch在每层上占用的内存
act_Memory = 2 * (13 * b * s * h + 5 * b * s * s * a + 21 * b * s * h) / 1e9 
# FP16, 每层层数占用的内存
model_Memory = 2 * (12 * h * h + 13 * h) / 1e9
print(f"act_Memory: {act_Memory}, model_Memory: {model_Memory}")
total_act_Memory = act_Memory * 12
total_model_Memory = model_Memory * 12 / 8
print(total_act_Memory)
print(total_model_Memory)