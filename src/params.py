win_size = (1280, 720)
n_bins = 9
cell_size = (256, 90)
block_size = (512, 180)
block_stride = cell_size
feature_len = n_bins * (block_size[0] // cell_size[0]) * (
    block_size[1] // cell_size[1]
) * (win_size[0] // block_stride[0] - block_size[0] // block_stride[0] + 1) * (
    win_size[1] // block_stride[1] - block_size[1] // block_stride[1] + 1)
