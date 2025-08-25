# EVT 2.0 Format

EVT 2.0 is a 32-bit data format supporting sensors with up to 2048x2048 resolution.
It is a very robust format that does not contain any vectorization (contrary to EVT 3.0)
and is destined for low event rate applications.

The data transmission follows either little or big-endian format,
which is determined by the sensor configuration.
By default, IMX636 and GenX320
sensors transmit data in little-endian format, where the least significant byte comes first and the most significant one comes last.

In each 32-bit EVT 2.0 word, the 4 Most Significant Bits (MSB) are used to define the word type.

The following table depicts the different types of events data that can be encountered:

| Event | Description | Value |
|-------|-------------|-------|
| CD_OFF | OFF CD event, i.e. decrease in illumination (polarity '0') | '0000' |
| CD_ON | ON CD event, i.e. increase in illumination (polarity '1') | '0001' |
| EVT_TIME_HIGH | Timer high bits: MSB part of the events timestamp. Least Significant Bits (LSB) are attached to CD_OFF / CD_ON words. | '1000' |
| EXT_TRIGGER | External trigger output | '1010' |
| OTHERS | To be used for extensions in the event types | '1110' |
| CONTINUED | Extra data that are used for the events which arrive in several words. Vendor specific, contact your event-based camera distributor. | '1111' |

> **Note**
> 
> Other event types are reserved. Contact your event-based camera distributor if you receive
> EVT 2.0 words whose type is not described in this table.

## Event Time Encoding

All events are timestamped with a micro-second precision. Timestamp are encoded with 34 bits, providing a rollout after:  2³⁴ μs = 4 hours and 46 minutes.
In order to minimize the amount of information stored with each event, the event timestamp is encoded in two parts. Lower 6 significant bits (0..5) of the micro-second timestamp are directly encoded into the CD or Trigger event, while the 28 most significant bits (6..33) of the timestamp are stored in a dedicated EVT_TIME_HIGH event. To rebuild the full event timestamp, the lower bits of the timestamp embedded in the event must be concatenated with the last EVT_TIME_HIGH event information.

![34 bits timestamp representation](./EVT%202.0%20Format%20—%20Metavision%20SDK%20Docs%205.1.1%20documentation_files/evt2_timestamp.jpg)

To compute the full resolution of the timestamp, decoding of the event stream should start after receiving the first event of type EVT_TIME_HIGH.

## CD_OFF

| Bit Range | Bit Width | Field Name | Description | Default Value |
|-----------|-----------|------------|-------------|---------------|
| 31..28 | 4 bits | type | Event type \| CD_OFF ('0000') | ('0000') |
| 27..22 | 6 bits | timestamp | Least significant bits of the event time base | – |
| 21..11 | 11 bits | x | Pixel X coordinate | – |
| 10..0 | 11 bits | y | Pixel Y coordinate | – |

> **Note**
> 
> Polarity of CD_OFF events is implicitly 0, encoding a decrease of illumination.

## CD_ON

| Bit Range | Bit Width | Field Name | Description | Default Value |
|-----------|-----------|------------|-------------|---------------|
| 31..28 | 4 bits | type | Event type \| CD_ON ('0001') | ('0001') |
| 27..22 | 6 bits | timestamp | Least significant bits of the event time base | – |
| 21..11 | 11 bits | x | Pixel X coordinate | – |
| 10..0 | 11 bits | y | Pixel Y coordinate | – |

> **Note**
> 
> Polarity of CD_ON events is implicitly 1, encoding an increase of illumination.

## EVT_TIME_HIGH

| Bit Range | Bit Width | Field Name | Description | Default Value |
|-----------|-----------|------------|-------------|---------------|
| 31..28 | 4 bits | type | Event type \| EVT_TIME_HIGH | ('1000') |
| 27..0 | 28 bits | timestamp | Most significant bits of the event time base (33..6) | – |

## EXT_TRIGGER

The External Trigger Event is transmitted to indicate that an edge (change of electrical state) was detected
on an external trigger signal. In the last generations of Prophesee sensors, those signals can be sent either to the
EXTTRIG pin (see the Trigger In documentation)
or the Reset pin (`TDRSTN` on the IMX636 and `PXRSTN` on the GenX320.
See the FAQ entry about Reset).

The source of the event is recorded in the `Trigger channel ID` field.
The event also records a value corresponding to the edge polarity
and a timestamp that is derived from previously sent Time High and Time Low events.

| Bit Range | Bit Width | Field Name | Description | Default Value |
|-----------|-----------|------------|-------------|---------------|
| 31..28 | 4 bits | type | Event type \| EXT_TRIGGER | ('1010') |
| 27..22 | 6 bits | timestamp | Least significant bits of the event time base | – |
| 21..13 | 9 bits | – | Unused | – |
| 12..8 | 5 bits | id | Trigger channel ID<br>• '00000': EXTTRIG<br>• '00001': TDRSTN / PXRSTN | – |
| 7..1 | 7 bits | – | Unused | – |
| 0 | 1 bit | value | Trigger current value (edge polarity):<br>0: falling edge<br>1: rising edge | '0' |

## OTHERS

| Bit Range | Bit Width | Field Name | Description | Default Value |
|-----------|-----------|------------|-------------|---------------|
| 31..28 | 4 bits | type | Event type \| OTHERS | ('1110') |
| 27..22 | 6 bits | timestamp | Least significant bits of the event time base | – |
| 21..17 | 5 bits | – | Unused | – |
| 16 | bit | class | Event class:<br>0: Monitoring<br>1: TBD | – |
| 15..0 | 16 bits | subtype | Event sub-type | – |

> **Note**
> 
> OTHERS EVT 2.0 words are vendor specific. Contact your event-based camera vendor to get more
> details.

## CONTINUED

| Bit Range | Bit Width | Field Name | Description | Default Value |
|-----------|-----------|------------|-------------|---------------|
| 31..28 | 4 bits | type | Event type \| CONTINUED | ('1111') |
| 27..0 | 28 bits | – | Depends on the previous event | – |

> **Note**
> 
> CONTINUED EVT 2.0 words are vendor specific. Contact your event-based camera vendor to get
> more details.
