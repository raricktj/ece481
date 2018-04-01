import numpy as _np
import pandas as _pd

class Song:
    
    def __init__(self, fs=44100, fref=440, bpm=120):
        self.fs = fs
        self.fref= fref
        self.bpm = bpm
        self.df = _pd.DataFrame(columns=['start', 'note',
                                        'duration', 'intensity'])  
        return
        
    def __BarToSamples(self):
        return int(self.__BarToSeconds()*self.fs)
    
    def __BarToSeconds(self):
        return 4*(1/self.bpm)*60
    
    def __NoteToFreq(note, fref):
        return fref*_np.power(2, note/12)
    
    # Duration and start in bars
    def AddNote(self, start, note, duration=0.25, intensity=0.1):
        newNote = _pd.DataFrame([[start, note, duration, intensity]],
                                columns=['start', 'note',
                                         'duration', 'intensity'])
        
        self.df = self.df.append(newNote)
        return
                
        # TODO: Implement
#     def MajorToNote(self):
#         return
    
    def Compile(self, instrument):    
        df = self.df.copy()
        barSamples = self.__BarToSamples()
        arraySize = (df['start'] + df['duration']).max()*barSamples
        arraySize = _np.ceil(arraySize).astype(_np.int) + 1
        
        x = _np.zeros(arraySize)
        
        df['note'] = df['note'].apply(Song.__NoteToFreq, args=(self.fref,))
        df['start'] = df['start']*barSamples
        df['duration'] = df['duration']*self.__BarToSeconds()
        
        for i, note in df.iterrows():
            subArray = instrument.play(note['note'], 
                                       self.fs,
                                       note['duration'],
                                       note['intensity'])
            start = _np.floor(note['start']).astype(_np.int)
            end = start + subArray.size
                        
            x[start:end] += subArray
            
        return 0.5*x/max(x)

class Instrument(object):
    
    def __init__(self, envelope=None):
        # Envelope defined in tuples of ADSR, (dB, Time)
        # Units are dB and seconds
        self.__envelope = envelope
        if self.__class__ == Instrument:
            raise NotImplementedError
        
    # Duration in seconds
    def play(self, f, fs, duration, intensity):
        # If no envelope, just return playFunc
        if self.__envelope is None:
            return self.playFunc(f, fs, duration, intensity)
        
        # If there is an envelope, apply it.
        else:
            env = Instrument.__CompileEnvelope(self.__envelope, fs)
            x = self.playFunc(f, fs, duration, intensity)
            return Instrument.__ApplyEnvelope(x, env)
        
#     def __playFunc(self, f, fs, duration, intensity):
#         if self.__class__ == Instrument:
#             raise NotImplementedError        
            
            
    def __CompileEnvelope(envelope, fs):
        if(len(envelope) != 4):
            raise ValueError('Envelope size must be 4: ADSR')
            
        times, amps = zip(*envelope)
        
        xvals = _np.linspace(0, times[-1], fs*times[-1])
        env = _np.interp(xvals, times, amps)
        
        return _np.power(10, env/20)
        
        
    def __ApplyEnvelope(x, envelope):
        env = _np.zeros(x.shape)
        
        maxBound = min(len(envelope), env.shape[0])
        
        env[0:maxBound] = envelope[0:maxBound]
        
        return env*x
        
                
    def OscillatorView(self):
        return self.playFunc(1, 100, 1, 1)


class SineWave(Instrument):

    # Duration in seconds
    def playFunc(self, f, fs, duration, intensity):
        samples = fs*duration
        t = _np.linspace(0,duration, samples)

        w = 2*_np.pi*f
        
        return intensity*_np.sin(w*t)


class SawTooth(Instrument):
    
    # Duration in seconds
    def playFunc(self, f, fs, duration, intensity):
        samples = fs*duration
        t = _np.linspace(0,duration, samples)
        
        T = 1/f
        
        # t mod T represents progress to T
        # Amplitude scaled by /T*intensity
        return intensity*(t % T)/T



class SquareWave(Instrument):
    
    # Duration in seconds
    def playFunc(self, f, fs, duration, intensity):
        samples = fs*duration
        t = _np.linspace(0,duration, samples)
        
        T = 1/f
        
        # Same as Sawtooth but rounded to integer 0/1
        return intensity*_np.round((t % T)/T)



class TriangleWave(Instrument):
    
    # Duration in seconds
    def playFunc(self, f, fs, duration, intensity):
        samples = fs*duration
        t = _np.linspace(0,duration, samples)
        
        T = 1/f
        
        # 2*abs(square wave - sawtooth)
        return 2*intensity*abs(_np.round((t % T)/T) - (t % T)/T)