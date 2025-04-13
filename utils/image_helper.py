import os
import re
from collections import defaultdict
from pprint import pp
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from pathlib import Path


"""
Not fully complete yet.

Description:

This class is used to analyze image sequences in a folder. It can find all the image sequences in the folder and sort them by their prefix and number. It can also get a specific frame of the sequence by its number.

Usage:

image_path = r'D:\tex\test_something_demo0016.exr'  # replace with your image path

analyzer = ImageSequence(image_path)
print(analyzer)  # print the image sequence information
"""

@dataclass
class ImageSequence:

    image_path: str

    # override if needed
    pattern: str = r'(.+?)(\d+)\.(jpg|png|jpeg|tif|tiff|hdr|exr|tx|tga|psd|psb)'
    sequences: Dict[str, List[Tuple[int, str]]] = field(default_factory=lambda: defaultdict(list))

    def __post_init__(self) -> None:
        if not Path(self.image_path).exists():
            raise FileNotFoundError(f'Image File Not Found: {self.image_path}')
        self.extension = os.path.splitext(self.image_path)[1][1:]
        self.folder_path = os.path.dirname(self.image_path)
        self.image_name = os.path.basename(self.image_path)
        self.result: list = self.get_sequence()

    @property
    def length(self) -> int:
        return len(self.result) if isinstance(self.result, list) else 0
    
    @property
    def name(self) -> str:
        return os.path.splitext(list(analyzer.sequences.keys())[0])[0] if len(analyzer.sequences) > 0 else ''
    
    @property
    def start(self) -> int:
        if len(self.result) > 0:
            _, start, _ = re.match(self.pattern, self.result[0], re.I).groups()
            return start
        return 0
    
    @property
    def end(self) -> int:
        if len(self.result) > 0:
            _, end, _ = re.match(self.pattern, self.result[-1], re.I).groups()
            return end
        return 0

    @property
    def duration(self) -> str:
        if len(self.result) > 0:
            return f'{self.start} - {self.end}'
        return 'unknown'
    
    def __str__(self) -> str:
        if len(self.result) > 0:
            return f"ImageSequence Name: {self.name}[####].{self.extension} | Duration: {self.duration}"
        else:
            return f'No Image Sequence Found of {self.image_path}'

    def _analyze_sequences(self) -> None:

        images = [img for img in os.listdir(self.folder_path) if img.lower().endswith(self.extension)]

        for image in images:
            match = re.match(self.pattern, image, re.I)
            if match:
                prefix, number, extension = match.groups()
                sequence_key = f"{prefix}.{extension}"
                self.sequences[sequence_key].append((int(number), image))
        
        # Sort
        for key in self.sequences:
            self.sequences[key].sort()

    def get_sequence(self) -> list[str]:
        self.sequences.clear()
        
        # analyze all sequences
        self._analyze_sequences()
        
        # match the image name
        match = re.match(self.pattern, self.image_name, re.I)
        
        if match:
            prefix, number, extension = match.groups()
            sequence_key = f"{prefix}.{extension}"
            return [img for _, img in self.sequences.get(sequence_key, [])]
        else:
            return []

    def get_frame(self, frame: int) -> str:
        if frame < 0 or frame >= len(self.result):
            raise ValueError(f'Frame {frame} out of range')
        if (path := Path(os.path.join(self.folder_path), self.result[frame])):
            if path.exists():
                return path
        return ''
