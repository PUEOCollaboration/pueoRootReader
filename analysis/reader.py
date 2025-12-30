'''
A Reader class for reading PUEO ROOTified flight data.

Made by Zachary Martin, 2025 12 25
'''

import uproot
import numpy as np
import warnings
import datetime

class PUEORootReader():
    '''
    This class unpacks PUEO flight ROOT data, converting each branch to an easily accessible attribute for a given
    run and event. Calling any particular attribute will return the data values for the active run + active event.
    The active run and active event can be changed with PUEORootReader.setRun() and PUEORootReader.setEvent().
    Immediate derivations from the ROOT data can also be accessed as attributes.

    Disclaimer: We are organizing data by runs, so normally this is going to be used with single run ROOT files.
    But the ROOT files are designed to be easily concatenated. So the option to set the run is there if you need.
    That said, it's possible there are bugs in changing runs. If so, just let me know.

    Attributes
    ----------
    run : int
        The active run number.
    event : int
        The active event number.
    event_second : int
        The time in UTC seconds which the active event's triggering pulse occurs.
    event_time : int
        The time in clock cycles of the active run at which the active event's triggering pulse occurs.
    last_pps : int
        Time of last PPS (clock cycles since start of run) of the active event.
    llast_pps : int
        Time of second-to-last PPS (clock cycles since start of run) of the active event.
    deadtime_counter : int
        Current total deadtime (measured in clock cycles), i.e. time up to the active event which did not have any triggers.
    deadtime_counter_last_pps : int
        The deadtime in clock cycles at the last PPS.
    deadtime_counter_llast_pps : int
        The deadtime in clock cycles at the last PPS.
    l2_mask : int
        A 24 bit number, each bit corresponding to the SURF Channels (which target 2 phi sectors of one polarity).
        Each bit value indicates the channel's L2 sector enable mask (1: enabled, 0: masked off).
    soft_trigger : int
        Flags if the active event is a software ("forced") trigger.
    pps_trigger : int
        Flags if the active event is a PPS trigger.
    ext_trigger : int
        Inactive bit. Flags if the active event is an "external" trigger.
    readout_time_utc_sec : int
        The UTC seconds at which the active event was read out.
    readout_time_utc_nsec : int
        The UTC nanoseconds at which the active event was read out.
    channel_ids : 1darray
        The DAQ channel IDs corresponding to each waveform in the active event.
    surf_word : 1darray
        SURF header word (not exactly sure what that means...)
    wf_length : 1darray
        The sampling lengths corresponding to each waveform in the active event.
    wfs : 2darray
        The waveforms in ADU Voltage of the active event.
    time : 1darray
        The sampling time axis for the waveforms.
    trigger_type : int
        A trigger ID integer: 0=RF, 1=SW, 2=PPS, 3=EXT
    readout_date : datetime.datetime
        The UTC date timestamp at which the active event was read out.
    subsecond : float
        The GPS subsecond of the active event. Note that this may not be well defined for early events in 
        a given run (need enough time for two PPS to pass for valid last_pps and llast_pps values).
    N : int
        The number of events found in the active run.

    Methods
    -------
    setRun(run, index=True)
        Sets the active run. Input the run number, or input the index of runs with index=True.
        This will reset the active event to the first listed for the active run.
    setEvent(event, index=True)
        Sets the active event. Input the event number, or input the index of events with index=True.
    getTriggerTypes()
        Returns the list of trigger types for every event in the active run. Types: 0=RF, 1=SW, 2=PPS, 3=EXT
    getWF(channel)
        Return the given channel's waveform for the current active event.
    '''

    def __init__(self, rootfile, run=None, event=None):

        # unpack all raw data
        with uproot.open(rootfile) as data:
            self._RUNS = data['eventTree']['run'].array()
            self._EVENTS = data['eventTree']['event'].array()
            self._EVENT_SECOND = data['eventTree']['event_second'].array()
            self._EVENT_TIME = data['eventTree']['event_time'].array()
            self._LAST_PPS = data['eventTree']['last_pps'].array()
            self._LLAST_PPS = data['eventTree']['llast_pps'].array()
            self._DEADTIME_COUNTER = data['eventTree']['deadtime_counter'].array()
            self._DEADTIME_COUNTER_LAST_PPS = data['eventTree']['deadtime_counter_last_pps'].array()
            self._DEADTIME_COUNTER_LLAST_PPS = data['eventTree']['deadtime_counter_llast_pps'].array()
            self._L2_MASK = data['eventTree']['L2_mask'].array()
            self._SOFT_TRIGGER = data['eventTree']['soft_trigger'].array()
            self._PPS_TRIGGER = data['eventTree']['pps_trigger'].array()
            self._EXT_TRIGGER = data['eventTree']['ext_trigger'].array()
            # self._RESERVED = data['eventTree']['reserved'].array()
            self._READOUT_TIME_UTC_SECS = data['eventTree']['readout_time_utc_secs'].array()
            self._READOUT_TIME_UTC_NSECS = data['eventTree']['readout_time_utc_nsecs'].array()
            self._CHANNEL_ID = data['eventTree']['channel_id'].array()
            self._SURF_WORD = data['eventTree']['surf_word'].array()
            self._WF_LENGTH = data['eventTree']['wf_length'].array()
            self._WFS = data['eventTree']['wfs'].array()

        # set active run and active event
        if run is None:
            if len(self.runs) > 1:
                warnings.warn(f'No run specified. Active run set to first found ({self.runs[0]}) by default. You can change the active run with PUEORootReader.setRun(run).')
            self.run = self.runs[0]
        else:
            self.setRun(run)
        if event is None:
            warnings.warn(f'No event specified. Active event set to first found ({self.events[0]}) by default. You can change the active event with PUEORootReader.setEvent(event).')
            self.event = self.events[0]
        else:
            self.setEvent(event)

        # read corresponding values for active event
        self._INITIALIZE_EVENT()

        # things we know to be true
        self._SAMPLE_RATE = 3 # GS/s
        self._SAMPLE_DT = 1 / self._SAMPLE_RATE

    
    @property
    def runs(self):
        '''Run numbers found in the data.'''
        return np.unique(self._RUNS)
    
    @property
    def events(self):
        '''Event numbers found for the active run.'''
        return self._EVENTS[np.asarray(self.run == self._RUNS).nonzero()[0]]

    @property
    def time(self):
        '''The sampling time for the waveforms in the active event. All waveforms are assumed to have the same length and samplerate.'''
        return 1e-9*np.arange(0, self.wf_length[0]*self._SAMPLE_DT, self._SAMPLE_DT) # assume all wfs have same length

    @property
    def trigger_type(self):
        '''The type of trigger for the active event. 0=RF, 1=SW, 2=PPS, 3=EXT'''
        return 1*self.soft_trigger + 2*self.pps_trigger + 3*self.ext_trigger

    @property
    def readout_date(self):
        '''The UTC datetime timestamp at which the active event was read out.'''
        return datetime.datetime.fromtimestamp(self.readout_time_utc_sec + 1e-9*self.readout_time_utc_nsec, datetime.timezone.utc)

    @property
    def subsecond(self):
        '''Returns the GPS subsecond of the active event. Note that this may not be well defined for early events in a given run (need
        enough time for two PPS to pass for valid last_pps and llast_pps values).'''
        # cast away from uint32's to avoid "overflow" errors (occur when last_pps > event_time, aka early event)
        return ( np.float64(self.event_time) - np.float64(self.last_pps) ) / ( np.float64(self.last_pps) - np.float64(self.llast_pps) )

    @property
    def N(self):
        '''The number of events found in the active run.'''
        return len(self.events)

    def setRun(self, run, index=False):
        '''
        Sets the active run. Give the run number, or the index of the runs with index=True.
        This will reset the active event to the first listed for the active run.
        '''
        if index:
            self.run = self.runs[run]
        else:
            if not (int(run) in self.runs):
                raise ValueError(f'Given run, {int(run)}, not found. Available runs are {self.runs}')
            self.run = int(run)

        # fix event inconsistency
        self.setEvent(0, index=True)

    def setEvent(self, event, index=False):
        '''Sets the active event. Give the event number, or the index of the events with index=True.'''
        if index:
            self.event = self.events[event]
        else:
            if not (int(event) in self.events):
                raise ValueError(f'Given event, {int(event)}, not found. Available events are {self.events}')
            self.event = int(event)

        # reread event
        self._INITIALIZE_EVENT()

    def getTriggerTypes(self):
        '''Returns the list of trigger types for every event in the active run. Types: 0=RF, 1=SW, 2=PPS, 3=EXT'''
        return (1*self._SOFT_TRIGGER + 2*self._PPS_TRIGGER + 3*self._EXT_TRIGGER)[np.asarray(self.run == self._RUNS).nonzero()[0]]

    def getWF(self, channel):
        '''Return the given channel's waveform for the current active event.'''
        index_of_channel = np.asarray(self.channel_ids == int(channel)).nonzero()[0][0]
        return self.wfs[index_of_channel]

        
    def _INITIALIZE_EVENT(self):
        '''Parse data values for the current active event.'''

        # get raw data index of the active event
        self._active_index = np.asarray(np.logical_and(self.run == self._RUNS, self.event == self._EVENTS)).nonzero()[0][0]
        
        self.event_second = self._EVENT_SECOND[self._active_index]
        self.event_time = self._EVENT_TIME[self._active_index]
        self.last_pps = self._LAST_PPS[self._active_index]
        self.llast_pps = self._LLAST_PPS[self._active_index]
        self.deadtime_counter = self._DEADTIME_COUNTER[self._active_index]
        self.deadtime_counter_last_pps = self._DEADTIME_COUNTER_LAST_PPS[self._active_index]
        self.deadtime_counter_llast_pps = self._DEADTIME_COUNTER_LLAST_PPS[self._active_index]
        self.l2_mask = bin(self._L2_MASK[self._active_index])
        self.soft_trigger = self._SOFT_TRIGGER[self._active_index]
        self.pps_trigger = self._PPS_TRIGGER[self._active_index]
        self.ext_trigger = self._EXT_TRIGGER[self._active_index]
        # self.reserved = self._RESERVED[self._active_index]
        self.readout_time_utc_sec = self._READOUT_TIME_UTC_SECS[self._active_index]
        self.readout_time_utc_nsec = self._READOUT_TIME_UTC_NSECS[self._active_index]
        self.channel_ids = self._CHANNEL_ID[self._active_index]
        self.surf_word = self._SURF_WORD[self._active_index]
        self.wf_length = self._WF_LENGTH[self._active_index]
        self.wfs = self._WFS[self._active_index]
      