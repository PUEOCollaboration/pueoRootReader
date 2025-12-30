from analysis.reader import PUEORootReader

datafile = "data/ROOT/run0839/007900.root"

# an object containing the data. By default, the first run and event found are "active"
data = PUEORootReader(datafile) # you can specify the active event when creating this instance: PUEORootReader(datafile, event=7763)


# you can access attributes corresponding to the active event
print(f'Found runs {data.runs}')
print(f'Found events {data.events}') # only shown for the active run

print(f'Data for: Run {data.run}, Event {data.event}')
# these are directly from the ROOT file
print(f'Event second: {data.event_second}')
print(f'Event time (clock cycles): {data.event_time}')
print(f'Last PPS (clock cycles): {data.last_pps}')
print(f'Last Last PPS (clock cycles): {data.llast_pps}')
print(f'Deadtime: {data.deadtime_counter}')
print(f'L2 Mask: {data.l2_mask}')
print(f'Readout Time UTC Second: {data.readout_time_utc_sec}')
print(f'Readout Time UTC Nano-Subsecond: {data.readout_time_utc_nsec}')
print(f'Channel IDs: {data.channel_ids}')
print(f'Channel Waveforms: {data.wfs}')

# these are derived from the ROOT file data
print(f'Readout Date UTC: {data.readout_date}')
print(f'Sampling Time Axis: {data.time}')
print(f'Number of Events: {data.N}')
print(f'Trigger Type: {data.trigger_type}')
print(f'Trigger Subsecond: {data.subsecond}')


# you can change the active event
data.setEvent(33, index=True) # index=True to select by index, otherwise just give the event number
print(f'Data for: Run {data.run}, Event {data.event}')
print(f'Event second: {data.event_second}')
print(f'Event time (clock cycles): {data.event_time}')
print(f'Last PPS (clock cycles): {data.last_pps}')
print(f'Last Last PPS (clock cycles): {data.llast_pps}')
print(f'Deadtime: {data.deadtime_counter}')
print(f'L2 Mask: {data.l2_mask}')
print(f'Readout Time UTC Second: {data.readout_time_utc_sec}')
print(f'Readout Time UTC Nano-Subsecond: {data.readout_time_utc_nsec}')
print(f'Channel IDs: {data.channel_ids}')
print(f'Channel Waveforms: {data.wfs}')
print(f'Readout Date UTC: {data.readout_date}')
print(f'Sampling Time Axis: {data.time}')
print(f'Number of Events: {data.N}')
print(f'Trigger Type: {data.trigger_type}')
print(f'Trigger Subsecond: {data.subsecond}')


# you can also access all event trigger types (will be useful for selecting subsets), and single waveforms by channel
print(f'Trigger Types: {data.getTriggerTypes()}')
print(f'Ch0 Waveform: {data.getWF(0)}')
print(f'Ch123 Waveform: {data.getWF(123)}')