from pydantic import BaseModel


class DisplayResolution(BaseModel):
    width: int
    height: int

    def to_string(self):
        return f"{self.width}x{self.height}"
