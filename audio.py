import pygame
import os

class AudioManager:
    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.sounds = {}
        self.music_volume = 0.7
        self.sfx_volume = 0.8
        self.load_all_sounds()
        
    def load_sound(self, name, filename):
        """Load a sound file"""
        try:
            sound = pygame.mixer.Sound(filename)
            sound.set_volume(self.sfx_volume)
            self.sounds[name] = sound
            print(f"Loaded sound: {name} from {filename}")
        except Exception as e:
            print(f"Failed to load sound {name} from {filename}: {e}")
            # Create placeholder sound if file doesn't exist
            self.sounds[name] = None
            
    def play_sound(self, name):
        """Play a sound effect"""
        print(f"Trying to play sound: {name}")
        # Check if we have a direct sound file
        if name in self.sounds and self.sounds[name]:
            print(f"Playing direct sound: {name}")
            self.sounds[name].play()
        # Check if we have a mapped sound
        elif hasattr(self, 'sound_mapping') and name in self.sound_mapping:
            mapped_sound = self.sound_mapping[name]
            print(f"Using mapped sound: {name} -> {mapped_sound}")
            if mapped_sound in self.sounds and self.sounds[mapped_sound]:
                self.sounds[mapped_sound].play()
        else:
            print(f"No sound found for: {name}, generating beep")
            # Generate simple beep sound programmatically
            self.generate_beep(name)
            
    def generate_beep(self, sound_type):
        """Generate simple 8-bit style sounds programmatically"""
        duration = 0.1
        sample_rate = 22050
        
        if sound_type == "jump":
            # Rising tone
            frequency = 220
            self.create_tone(frequency, duration * 0.5, rising=True)
        elif sound_type == "attack":
            # Sharp hit sound
            frequency = 150
            self.create_tone(frequency, duration * 0.3, sharp=True)
        elif sound_type == "crystal":
            # Pleasant chime
            frequency = 440
            self.create_tone(frequency, duration * 0.8, chime=True)
        elif sound_type == "teleport":
            # Whoosh sound
            frequency = 300
            self.create_tone(frequency, duration * 0.6, whoosh=True)
        elif sound_type == "phase":
            # Ethereal sound
            frequency = 200
            self.create_tone(frequency, duration * 1.0, ethereal=True)
        elif sound_type == "damage":
            # Low hurt sound
            frequency = 100
            self.create_tone(frequency, duration * 0.4, hurt=True)
            
    def create_tone(self, frequency, duration, rising=False, sharp=False, chime=False, whoosh=False, ethereal=False, hurt=False):
        """Create simple tones programmatically"""
        try:
            import numpy as np
            sample_rate = 22050
            frames = int(duration * sample_rate)
            arr = np.zeros(frames)
            
            for i in range(frames):
                time = float(i) / sample_rate
                
                if rising:
                    freq = frequency + (frequency * 0.5 * time / duration)
                elif sharp:
                    freq = frequency * (1 - time / duration)
                elif chime:
                    freq = frequency
                    arr[i] = 0.3 * np.sin(2 * np.pi * freq * time) * (1 - time / duration)
                    continue
                elif whoosh:
                    freq = frequency * (0.5 + 0.5 * np.sin(10 * time))
                elif ethereal:
                    freq = frequency + 50 * np.sin(20 * time)
                elif hurt:
                    freq = frequency * (1 + 0.3 * np.sin(50 * time))
                else:
                    freq = frequency
                    
                arr[i] = 0.3 * np.sin(2 * np.pi * freq * time)
                
            # Apply envelope
            envelope = np.exp(-3 * np.linspace(0, 1, frames))
            arr *= envelope
            
            # Convert to pygame sound
            sound_array = (arr * 32767).astype(np.int16)
            sound = pygame.sndarray.make_sound(sound_array)
            sound.play()
            
        except ImportError:
            # Fallback if numpy not available
            pass
            
    def load_background_music(self, filename):
        """Load and start background music"""
        try:
            pygame.mixer.music.load(filename)
            pygame.mixer.music.set_volume(0.3)  # Low volume
            pygame.mixer.music.play(-1)  # Loop indefinitely
            print(f"Background music loaded and started: {filename}")
        except Exception as e:
            print(f"Failed to load background music {filename}: {e}")
            
    def set_music_volume(self, volume):
        """Set background music volume (0.0 to 1.0)"""
        self.music_volume = volume
        pygame.mixer.music.set_volume(volume)
        
    def stop_music(self):
        """Stop background music"""
        pygame.mixer.music.stop()
        
    def pause_music(self):
        """Pause background music"""
        pygame.mixer.music.pause()
        
    def resume_music(self):
        """Resume background music"""
        pygame.mixer.music.unpause()
            
    def load_all_sounds(self):
        """Load all game sounds from files or generate them"""
        sound_files = {
            "jump": "jump.wav",
            "crystal": "crystal.wav", 
            "glitch": "glitch.wav",
            "beat": "beat.wav"
        }
        
        for name, filename in sound_files.items():
            self.load_sound(name, filename)
            
        # Load and start background music
        self.load_background_music("bg_sound.wav")
            
        # Map sounds to game actions
        self.sound_mapping = {
            "attack": "beat",
            "teleport": "glitch", 
            "phase": "glitch",
            "damage": "beat"
        }

# Global audio manager instance
audio_manager = AudioManager()