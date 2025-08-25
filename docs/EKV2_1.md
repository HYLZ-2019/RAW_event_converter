# EVT 2.1 Format

EVT 2.1 is a 64-bit data format.

This format outputs events of the same polarity in groups of 32 pixel.

EVT2.1 format represents an extension to the [EVT 2.0](https://docs.prophesee.ai/stable/data/encoding_formats/evt2.html#chapter-data-encoding-formats-evt2) format.
Events are encoded on 64 bits and are vectorized (thus ideal for high event rate applications).
It is robust and provides good decoding performances.
We recommend this format for all applications requiring high bandwidth and efficient decoding.

The data transmission follows either [little or big-endian format](https://en.wikipedia.org/wiki/Endianness),
which is determined by the sensor configuration.
By default, [IMX636](https://docs.prophesee.ai/stable/hw/sensors/imx636.html#chapter-hw-sensors-imx636) and [GenX320](https://docs.prophesee.ai/stable/hw/sensors/genx320.html#chapter-hw-sensors-genx320)
sensors transmit data in little-endian format, where the least significant byte comes first and the most significant one comes last.

> **Note**
> 
> IMX636 and GenX320 handle the little-endian format differently:
>
> - On IMX636, the 64-bit word is transmitted in two steps. First, the initial 32-bit segment of the word
>   is sent in little-endian format, followed by the transmission of the second 32-bit segment,
>   also in little-endian.
> - On GenX320, the entire 64-bit word is transmitted at once, in little-endian format
>
> Here is an example:
>
> - 64-bit data to transmit: 0x0102030405060708
> - Data transmitted on IMX636: 0x0403020108070605
> - Data transmitted on GenX320: 0x0807060504030201

In each 64-bit EVT 2.1 word, the 4 Most Significant Bits (MSB) are used to define the word type.

The following table depicts the different types of events data that can be encountered:

| Event | Description | Value |
|-------|-------------|-------|
| EVT_NEG | OFF CD event, i.e. decrease in illumination (polarity '0') | '0000' |
| EVT_POS | ON CD event, i.e. increase in illumination (polarity '1') | '0001' |
| EVT_TIME_HIGH | Timer high bits: MSB part of the events timestamp. Least Significant Bits (LSB) are attached to EVT_POS / EVT_NEG words. | '1000' |
| EXT_TRIGGER | External trigger output | '1010' |
| OTHERS | To be used for extensions in the event types | '1110' |

> **Note**
> 
> Other event types are reserved. Contact your event-based camera distributor if you receive
> EVT 2.1 words whose type is not described in this table.

## Event Time Encoding

All events are timestamped with a micro-second precision. Timestamp are encoded with 34 bits, providing a rollout after:  2³⁴ μs = 4 hours and 46 minutes.
In order to minimize the amount of information stored with each event, the event timestamp is encoded in two parts. Lower 6 significant bits (0..5) of the micro-second timestamp are directly encoded into the CD or Trigger event, while the 28 most significant bits (6..33) of the timestamp are stored in a dedicated EVT_TIME_HIGH event. To rebuild the full event timestamp, the lower bits of the timestamp embedded in the event must be concatenated with the last EVT_TIME_HIGH event information.

![34 bits timestamp representation](./EVT%202.1%20Format%20—%20Metavision%20SDK%20Docs%205.1.1%20documentation_files/evt2_timestamp.jpg)

To compute the full resolution of the timestamp, decoding of the event stream should start after receiving the first event of type EVT_TIME_HIGH.

## EVT_NEG

| Bit Range | Bit Width | Field Name | Description | Default Value |
|-----------|-----------|------------|-------------|---------------|
| 63..60 | 4 bits | type | Event type \| EVT_NEG ('0000') | '0000' |
| 59..54 | 6 bits | timestamp | Least significant bits of the event time base | – |
| 53..43 | 11 bits | x | Pixel X coordinate aligned on 32 | – |
| 42..32 | 11 bits | y | Pixel Y coordinate | – |
| 31..0 | 32 bits | valid | Set bits represent valid events at coordinates:<br>• bit 0: valid event at coordinate (x + 0, y)<br>• bit n: valid event at coordinate (x + n, y)<br>• (…)<br>• bit 31: valid event at coordinate (x + 31, y) | – |

> **Note**
> 
> Polarity of EVT_NEG events is implicitly 0, encoding a decrease of illumination.

## EVT_POS

| Bit Range | Bit Width | Field Name | Description | Default Value |
|-----------|-----------|------------|-------------|---------------|
| 63..60 | 4 bits | type | Event type \| EVT_POS ('0001') | '0001' |
| 59..54 | 6 bits | timestamp | Least significant bits of the event time base | – |
| 53..43 | 11 bits | x | Pixel X coordinate aligned on 32 | – |
| 42..32 | 11 bits | y | Pixel Y coordinate | – |
| 31..0 | 32 bits | valid | Set bits represent valid events at coordinates:<br>• bit 0: valid event at coordinate (x + 0, y)<br>• bit n: valid event at coordinate (x + n, y)<br>• (…)<br>• bit 31: valid event at coordinate (x + 31, y) | – |

> **Note**
> 
> Polarity of EVT_POS events is implicitly 1, encoding an increase of illumination.

## EVT_TIME_HIGH

| Bit Range | Bit Width | Field Name | Description | Default Value |
|-----------|-----------|------------|-------------|---------------|
| 63..60 | 4 bits | type | Event type \| EVT_TIME_HIGH | '1000' |
| 59..32 | 28 bits | timestamp | Most significant bits of the event time base | – |
| 31..0 | 32 bits | – | Unused. Stuck at zero | '00…0' |

## EXT_TRIGGER

The External Trigger Event is transmitted to indicate that an edge (change of electrical state) was detected
on an external trigger signal. In the last generations of Prophesee sensors, those signals can be sent either to the
EXTTRIG pin (see the [Trigger In documentation](https://docs.prophesee.ai/stable/hw/manuals/timing_interfaces.html#chapter-timing-interfaces-trigger-in-configuration))
or the Reset pin (`TDRSTN` on the IMX636 and `PXRSTN` on the GenX320.
See the [FAQ entry about Reset](https://docs.prophesee.ai/stable/faq.html#chapter-px-reset)).

The source of the event is recorded in the `Trigger channel ID` field.
The event also records a value corresponding to the edge polarity
and a timestamp that is derived from previously sent Time High and Time Low events.

| Bit Range | Bit Width | Field Name | Description | Default Value |
|-----------|-----------|------------|-------------|---------------|
| 63..60 | 4 bits | type | Event type \| EXT_TRIGGER | '1010' |
| 59..54 | 6 bits | timestamp | Least significant bits of the event time base | – |
| 53..45 | 9 bits | – | Unused. Stuck at zero | '0' |
| 44..40 | 5 bits | id | Trigger channel ID<br>• '00000': EXTTRIG<br>• '00001': TDRSTN / PXRSTN | – |
| 39..33 | 7 bits | – | Unused. Stuck at zero | '0' |
| 32 | 1 bit | value | Trigger current value (edge polarity):<br>0: falling edge<br>1: rising edge | '0' |
| 31..0 | 32 bits | – | Unused. Stuck at zero | '0' |
