# RAW File Format

## Table of Contents
- [Definition](https://docs.prophesee.ai/stable/data/file_formats/raw.html#definition)
- [RAW Files Header](https://docs.prophesee.ai/stable/data/file_formats/raw.html#raw-files-header)
- [RAW Files Event Data](https://docs.prophesee.ai/stable/data/file_formats/raw.html#raw-files-event-data)
  - [Event Stream RAW Files Data](https://docs.prophesee.ai/stable/data/file_formats/raw.html#event-stream-raw-files-data)
  - [Event Frame RAW Files Data](https://docs.prophesee.ai/stable/data/file_formats/raw.html#event-frame-raw-files-data)
- [RAW Files Usage](https://docs.prophesee.ai/stable/data/file_formats/raw.html#raw-files-usage)
  - [Event Stream RAW Files usage](https://docs.prophesee.ai/stable/data/file_formats/raw.html#event-stream-raw-files-usage)
  - [Event Frame RAW Files usage](https://docs.prophesee.ai/stable/data/file_formats/raw.html#event-frame-raw-files-usage)
- [Event Stream RAW Index File](https://docs.prophesee.ai/stable/data/file_formats/raw.html#event-stream-raw-index-file)

## Definition
RAW files store the output of the event camera without any decoding or processing.  
**RAW sensor data** can be stored using various [encoding formats](https://docs.prophesee.ai/stable/data/encoding_formats/index.html#chapter-data-encoding-formats).

RAW files are made of two parts:
- Header written in ASCII
- Event data written in binary [little or big-endian](https://en.wikipedia.org/wiki/Endianness) (depending on the sensor configuration, little-endian by default)

## RAW Files Header
RAW file header contains metadata associated to the RAW file.

It is a sequence of “keyword, value” pairs written line by line.  
More precisely, the file header is composed of text lines starting with “%” (0x25) followed by a space (0x20), a keyword, a space (0x20), a value and New Line NL / Line Feed (0x0A).

There is one special keyword: `end` without value that is used to mark the end of the header so that the code used to parse the header can know that after this keyword data will be found. This keyword is optional though as the parser will decide data begins as soon as a line does not start with “% ” (i.e the character ‘%’ followed by ‘ ‘).

Here is an example of RAW file header obtained using an [EVK4](https://docs.prophesee.ai/stable/hw/evk/evk4.html#chapter-hw-evk-evk4) using [EVT 3.0](https://docs.prophesee.ai/stable/data/encoding_formats/evt3.html#chapter-data-encoding-formats-evt3) encoding format:

```
% camera_integrator_name Prophesee
% date 2023-03-29 16:37:46
% evt 3.0
% format EVT3;height=720;width=1280
% generation 4.2
% geometry 1280x720
% integrator_name Prophesee
% plugin_integrator_name Prophesee
% plugin_name hal_plugin_imx636_evk4
% sensor_generation 4.2
% serial_number 00ca0009
% system_ID 49
% end
```


> **Note**  
> For some examples of RAW file headers using Event Frame Data Format, see [Diff3D RAW file header section](https://docs.prophesee.ai/stable/data/encoding_formats/diff3d.html#chapter-data-encoding-formats-diff3d-header) and [Histo3D RAW file header section](https://docs.prophesee.ai/stable/data/encoding_formats/histo3d.html#chapter-data-encoding-formats-histo3d-header).

Below, a table with common keyword/value pairs:

| Keyword                | Value                                                                 |
|-------------------------|----------------------------------------------------------------------|
| date                   | Recording date, format: YYYY-MM-DD HH:MM:SS                          |
| camera_integrator_name | Company name of the camera integrator                                 |
| plugin_integrator_name | Company name of the plugin integrator                                 |
| plugin_name            | HAL plugin used to generate the RAW file                              |
| serial_number          | Camera serial number                                                 |
| format                 | Encoding format version & size of sensor array. Format: [EVTn,HISTO3D,DIFF3D];height=y;width=x |
| system_ID              | Camera System ID                                                     |
| end                    | No Value. Used to specify end of header                               |

With the current version of Prophesee camera plugin, to be able to read a RAW file, the keyword `format` is favored as it contains both the encoding format (required to decode the data) and the geometry of the sensor (required when displaying events as frames).

Setting both keywords `camera_integrator_name` and `plugin_integrator_name` to the value `Prophesee` will allow Prophesee plugin to use the `system_ID` field to infer information on the stream that might be missing from the header (i.e. if the `% format` value is missing).

The other keywords (e.g. serial_number) are optional and currently only used to provide information to the [`I_HW_Identification`](https://docs.prophesee.ai/stable/api/cpp/hal/facilities.html#_CPPv4N10Metavision19I_HW_IdentificationE) class.

> **Note**  
> There are multiple related/synonyms keyword in the example shown above (`integrator_name` and `camera_integrator_name`, or `evt` and `format` etc.). Those keywords are present for backward compatibility of the recordings, i.e. to allow previous versions of Metavision SDK to read RAW files.

## RAW Files Event Data
RAW file event data contains event encoded either as Event Stream or Event Frames as presented in the [Encoding Formats page](https://docs.prophesee.ai/stable/data/encoding_formats/index.html#chapter-data-encoding-formats).

### Event Stream RAW Files Data
Event stream RAW files data is stored using [EVT 2.0](https://docs.prophesee.ai/stable/data/encoding_formats/evt2.html#chapter-data-encoding-formats-evt2), [EVT 2.1](https://docs.prophesee.ai/stable/data/encoding_formats/evt21.html#chapter-data-encoding-formats-evt21) or [EVT 3.0](https://docs.prophesee.ai/stable/data/encoding_formats/evt3.html#chapter-data-encoding-formats-evt3) encoding formats which is specified in the `format` keyword in the header.  
As described in the [Selecting Data Formats](https://docs.prophesee.ai/stable/data/encoding_formats/index.html#chapter-data-encoding-formats-selecting) section, you can choose which encoding format to use via Metavision Studio or the SDK API.

On some versions of RAW files, the format might be absent from the header. In that case, the data encoding format of the RAW file can be figured out using [metavision_file_info](https://docs.prophesee.ai/stable/samples/modules/stream/file_info.html#chapter-samples-stream-file-info) tool.

Reference decoder code is available for EVT2 and EVT3 in the samples below:
- To decode data from [EVT 2.0](https://docs.prophesee.ai/stable/data/encoding_formats/evt2.html#chapter-data-encoding-formats-evt2) RAW file, see [EVT2 RAW File decoder sample](https://docs.prophesee.ai/stable/samples/standalone/evt2_decoder.html#chapter-evt2-decoder)
- To decode data from [EVT 3.0](https://docs.prophesee.ai/stable/data/encoding_formats/evt3.html#chapter-data-encoding-formats-evt3) RAW file, see [EVT3 RAW File decoder sample](https://docs.prophesee.ai/stable/samples/standalone/evt3_decoder.html#chapter-evt3-decoder)

Reference encoder code is available for EVT2 in the following sample:
- To encode CSV format into [EVT 2.0](https://docs.prophesee.ai/stable/data/encoding_formats/evt2.html#chapter-data-encoding-formats-evt2) data, see [EVT2 RAW File encoder sample](https://docs.prophesee.ai/stable/samples/standalone/evt2_encoder.html#chapter-evt2-encoder)

### Event Frame RAW Files Data
Event frame RAW file data is stored using [Histo3D](https://docs.prophesee.ai/stable/data/encoding_formats/histo3d.html#chapter-data-encoding-formats-histo3d) or [Diff3D](https://docs.prophesee.ai/stable/data/encoding_formats/diff3d.html#chapter-data-encoding-formats-diff3d) encoding formats which is specified in the `format` keyword in the header.

## RAW Files Usage

### Event Stream RAW Files usage
Event Stream RAW files can be written and read by [Metavision Studio](https://docs.prophesee.ai/stable/metavision_studio/index.html#chapter-metavision-studio) and most of our [Code Samples](https://docs.prophesee.ai/stable/samples.html#chapter-samples) (if you don’t have any RAW file and no camera to produce one, you can use one from our [Sample Recordings](https://docs.prophesee.ai/stable/datasets.html#chapter-datasets)).

As shown in [metavision_noise_filtering sample](https://docs.prophesee.ai/stable/samples/modules/cv/noise_filtering_cpp.html#chapter-samples-cv-noise-filtering-cpp), it is possible to process the events of a RAW file with an [algorithm](https://docs.prophesee.ai/stable/algorithms.html#chapter-algorithms) (e.g. [`ActivityNoiseFilterAlgorithm`](https://docs.prophesee.ai/stable/api/cpp/cv/algorithms.html#_CPPv4I0EN10Metavision28ActivityNoiseFilterAlgorithmE) or [`TrailFilterAlgorithm`](https://docs.prophesee.ai/stable/api/cpp/cv/algorithms.html#_CPPv4I0EN10Metavision21TrailFilterAlgorithmTE)).

To apply a filter on a RAW file and encode it back to EVT2 RAW file, you can refer to the following samples:
- [metavision_raw_evt_encoder C++ sample](https://docs.prophesee.ai/stable/samples/modules/stream/raw_evt_encoder_cpp.html#chapter-samples-stream-raw-evt-encoder-cpp)
- [metavision_raw_evt_encoder Python sample](https://docs.prophesee.ai/stable/samples/modules/stream/raw_evt_encoder_py.html#chapter-samples-stream-raw-evt-encoder-py)

Another option to process event data is to [convert the RAW file](https://docs.prophesee.ai/stable/samples/modules/stream/file_to_hdf5.html#chapter-samples-stream-file-to-hdf5) into an [HDF5 event file](https://docs.prophesee.ai/stable/data/file_formats/hdf5.html#chapter-data-file-formats-hdf5), which features a better compression than RAW, and then process the HDF5 event file as easily as RAW files.

Finally, you can convert an Event Stream RAW file into an AVI video file using the [metavision_file_to_video tool](https://docs.prophesee.ai/stable/samples/modules/core/file_to_video.html#chapter-samples-core-file-to-video).

### Event Frame RAW Files usage
Here are some samples that produce or consume Event Frame RAW files:
- To generate Event Frame RAW files from Event Stream RAW files (and display them), you can use [metavision_event_frame_generation C++ sample](https://docs.prophesee.ai/stable/samples/modules/core/event_frame_generation.html#chapter-samples-core-event-frame-generation-cpp).
- To display Event Frame RAW files, you can use the [metavision_event_frame_viewer Python sample](https://docs.prophesee.ai/stable/samples/modules/core/event_frame_viewer.html#chapter-samples-core-event-frame-viewer-py).
- To convert Event Stream RAW files into AVI video files, use the [metavision_file_to_video tool](https://docs.prophesee.ai/stable/samples/modules/core/file_to_video.html#chapter-samples-core-file-to-video)
- The C++ sample [metavision_event_frame_gpu_loading](https://docs.prophesee.ai/stable/samples/modules/core/event_frame_gpu_loading.html#chapter-samples-core-event-frame-gpu-loading-cpp) shows how to preprocess Event Frame RAW files on a GPU using CUDA.

## Event Stream RAW Index File
When reading an event stream RAW file using the SDK, an index file named `[raw_file_name].tmp_index` may be automatically generated in the same directory as the RAW file. This index file contains metadata that maps the locations of timestamps within the RAW file. The primary purpose of this index file is to optimize performance during seek operations, allowing for faster access to specific points in the event stream.

The creation of this index file may take varying amounts of time, depending on the size of the RAW file. However, for subsequent openings, the previously created index file will be reused, significantly speeding up the process. If the index file is deleted, the SDK will automatically regenerate it the next time the RAW file is opened. This will introduce a minor delay but has no other impact on the system.

Please ensure that you have write permissions for the directory where the RAW file is stored. If the SDK cannot generate the index file due to insufficient permissions, a terminal message similar to the following will be displayed:

Please ensure that you have write permissions for the directory where the RAW file is stored. If the SDK cannot generate the index file due to insufficient permissions, a terminal message similar to the following will be displayed:

```
[HAL][WARNING] Failed to write index file /path/to/file.raw.tmp_index for input RAW file /path/to/file.raw
[HAL][WARNING] Make sure the folder which contains the RAW file is writeable to avoid building the index from scratch again next time
```
It is possible to specify that a RAW file should not be indexed when opening it:

* when using HAL C++ API, you should leverage RawFileConfig:
```
Metavision::RawFileConfig config;
config.build_index_ = false;
device = Metavision::DeviceDiscovery::open_raw_file(file_path, config);
```
* when using HAL Python API, you should leverage RawFileConfig:
```
from metavision_hal import DeviceDiscovery, RawFileConfig
config = RawFileConfig()
config.build_index = False
device = DeviceDiscovery.open_raw_file(file_path, config)
```
* when using SDK Stream C++ API, you should leverage FileConfigHints:
```
Metavision::FileConfigHints config;
config.set("index", false);
camera = Metavision::Camera::from_file(file_path, config);
```