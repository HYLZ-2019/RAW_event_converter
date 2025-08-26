# Event RAW 格式转换代码

## Q&A

1. 这些代码是用来干什么的？

	用来读取Prophesee相机产生的 [RAW格式](https://docs.prophesee.ai/stable/data/file_formats/raw.html) event，并转为更方便的其他格式（如csv、npz、h5）。

2. 为什么不用官方的Metavision库？

	因为我不想配环境。

3. 为什么不用官方的OpenEB库？

	因为我不想自己编译。

4. 纯Python跑得太慢了。

	是的，很慢。

5. 为什么不优化优化？
	
	因为我懒。而且格式转换只需要跑一遍，凑合着用用得了。

## 环境配置

用比较新的Python版本应该就能跑，我用的是Python 3.12，别的没有试过。

运行解码需要安装numpy。

保存到csv格式或h5格式需要额外安装csv或h5py，如果不想安装可以注释掉对应代码。

目前内置的视频可视化用的是ffmpeg-python这个库（注意，是`pip install ffmpeg-python`，不是`pip install ffmpeg`），这个库会根据你电脑上的PATH寻找可执行的ffmpeg文件，所以你需要先安装一个ffmpeg。如果你不想折腾ffmpeg，可以自己修改代码用别的库，或者直接注释掉这个功能。

## 使用方法

基本使用方法：
```bash
python evt3_reader.py input_file.raw
```

完整的命令行参数说明：
```bash
python evt3_reader.py input_file.raw [选项]
```

**可用选项：**
- `--max-events NUM` : 限制最大读取事件数量
- `--output-csv FILE` : 输出事件数据到CSV文件
- `--output-trigger-csv FILE` : 输出触发事件数据到CSV文件  
- `--output-npz FILE` : 输出数据到NPZ文件（NumPy压缩格式）
- `--output-h5 FILE` : 输出数据到H5文件（HDF5格式）
- `--output-video FILE` : 输出事件可视化视频（MP4格式）
- `--stats-only` : 只显示统计信息，不保存任何数据文件

**使用示例：**

```bash
# 只查看统计信息，不保存文件。
python evt3_reader.py recording.raw --stats-only

# 输出到CSV格式。EXT_TRIGGER事件通常被用于时间同步等，H5格式和NPZ格式都会把event和trigger事件一起保存，但CSV格式需要把它们分成两个文件分别保存。
python evt3_reader.py recording.raw --output-csv events.csv --output-trigger-csv triggers.csv

# 只读取前1000000个事件，输出到多种格式并保存可视化视频。
python evt3_reader.py recording.raw --max-events 1000000 --output-h5 events.h5 --output-npz events.npz --output-video events.mp4
```

如果你的程序读着读着闪退了，这大概率是数据太多爆内存了。你可以减小`--max-event`试试。（这时你可能想问，我还是想读取整个RAW文件，怎么办？——你可以换一台内存更大的电脑。或者自己找个AI再优化一下这个代码。）