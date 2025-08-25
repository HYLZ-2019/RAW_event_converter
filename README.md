RAW格式的文件用于存储event data。
Raw format说明：https://docs.prophesee.ai/stable/data/file_formats/raw.html
由于metavision的官方库在很多环境上不支持运行，所以我们使用通用的python语言实现一个RAW文件的解码器，这样我们可以把它转换为h5格式，方便后续处理。