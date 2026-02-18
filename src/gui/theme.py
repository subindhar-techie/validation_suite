class Theme:
    """
    Central theme configuration for the application.
    Provides professional color palettes and font settings.
    """
    
    # Colors
    PRIMARY = "#2c3e50"       # Dark Blue-Grey (Header/Sidebar)
    SECONDARY = "#34495e"     # Slightly Lighter Blue-Grey
    ACCENT = "#3498db"        # Bright Blue (Highlights/Active)
    
    SUCCESS = "#27ae60"       # Green
    WARNING = "#f39c12"       # Orange
    ERROR = "#e74c3c"         # Red
    INFO = "#3498db"          # Blue
    
    BG_MAIN = "#f5f6fa"       # Light Grey (Main Background)
    BG_WHITE = "#ffffff"      # White (Cards/Panels)
    
    TEXT_MAIN = "#2c3e50"     # Dark Grey (Main Text)
    TEXT_LIGHT = "#7f8c8d"    # Medium Grey (Subtitles)
    TEXT_WHITE = "#ffffff"    # White Text
    
    BORDER = "#bdc3c7"        # Light Border
    
    # Fonts
    FONT_FAMILY = "Segoe UI"  # Modern Windows Font
    
    @staticmethod
    def title_font(size=18):
        return (Theme.FONT_FAMILY, size, "bold")
    
    @staticmethod
    def header_font(size=14):
        return (Theme.FONT_FAMILY, size, "bold")
    
    @staticmethod
    def text_font(size=10):
        return (Theme.FONT_FAMILY, size)
    
    @staticmethod
    def bold_font(size=10):
        return (Theme.FONT_FAMILY, size, "bold")
