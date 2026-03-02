from librosa import load

class Sound():
     def __init__(
        self,
        path: str
    ):
        """
        load and analyse a soundfile
        """
        self.path = path
        self.soundfile, self.samplerate = load(path)
